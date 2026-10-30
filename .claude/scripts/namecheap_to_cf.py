"""
Namecheap -> Cloudflare domain migration for SiteCrew Architect.

Migrates domains from Namecheap DNS to Cloudflare by:
  1. Adding the domain as a zone in Cloudflare (jump_start imports existing DNS records)
  2. Fetching the assigned Cloudflare nameservers
  3. Updating the domain's nameservers at Namecheap

Required .env vars:
  NAMECHEAP_API_USER      Your Namecheap API username (usually same as login)
  NAMECHEAP_API_KEY       Your Namecheap API key (Account -> Profile -> API Access)
  NAMECHEAP_USERNAME      Your Namecheap login username (often same as API user)
  NAMECHEAP_CLIENT_IP     Your whitelisted IP (must be added in Account -> Profile -> API Access)
  CF_API_TOKEN            Cloudflare API token (Zone Read, DNS Edit, Zone Edit to add a zone)
  CF_ACCOUNT_ID           Cloudflare account ID

Usage:
  python namecheap_to_cf.py list-domains
  python namecheap_to_cf.py get-ns <domain>
  python namecheap_to_cf.py migrate <domain> --owner-approved
  python namecheap_to_cf.py migrate <domain> --dry-run
  python namecheap_to_cf.py status <domain>

Notes:
  - Changing nameservers needs --owner-approved (the owner said yes) AND a passing
    mail-check, run automatically right before the change. One domain at a time.
  - Namecheap API requires your IP to be whitelisted: Account -> Profile -> API Access.
  - jump_start=true tells Cloudflare to auto-import existing DNS records (MX, A, CNAME, etc.)
  - DNS propagation after migration takes 30 minutes to 48 hours.
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))
from cf_api import (CloudflareAPI, CloudflareAPIError, _load_env, describe_request_error,
                    mail_check, root_domain)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class NamecheapAPIError(Exception):
    pass


# ---------------------------------------------------------------------------
# Namecheap API client
# ---------------------------------------------------------------------------

class NamecheapAPI:
    """Thin wrapper around the Namecheap XML API."""

    BASE = "https://api.namecheap.com/xml.response"

    def __init__(self, api_user: str, api_key: str, username: str, client_ip: str) -> None:
        self.api_user = api_user
        self.api_key = api_key
        self.username = username
        self.client_ip = client_ip

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _params(self, command: str, **extra) -> dict:
        return {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.username,
            "ClientIp": self.client_ip,
            "Command": command,
            **extra,
        }

    def _request(self, command: str, **extra) -> ET.Element:
        """GET the Namecheap API, return parsed XML root. Raises NamecheapAPIError on failure."""
        params = self._params(command, **extra)
        try:
            r = requests.get(self.BASE, params=params, timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            raise NamecheapAPIError(f"HTTP error: {describe_request_error(e)}") from None

        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            raise NamecheapAPIError(f"XML parse error: {e}") from e

        if root.attrib.get("Status") != "OK":
            errors = [el.text for el in root.iter() if el.tag.endswith("Error") and el.text]
            msg = "; ".join(errors) or "Unknown Namecheap error"
            raise NamecheapAPIError(msg)

        return root

    @staticmethod
    def _sld_tld(domain: str) -> tuple[str, str]:
        """Split 'example.co.uk' -> ('example', 'co.uk')."""
        parts = domain.split(".")
        return parts[0], ".".join(parts[1:])

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        try:
            self._request("namecheap.domains.getList", PageSize="1", Page="1")
            return True
        except NamecheapAPIError:
            return False

    def list_domains(self, page_size: int = 100) -> list[dict]:
        """Return all domains in the account. Paginates automatically."""
        domains: list[dict] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            root = self._request(
                "namecheap.domains.getList",
                PageSize=str(page_size),
                Page=str(page),
            )

            list_result = next(
                (el for el in root.iter() if el.tag.endswith("DomainGetListResult")),
                None,
            )
            if list_result is None:
                raise NamecheapAPIError("DomainGetListResult not found in response")

            for el in list_result:
                if el.tag.endswith("Domain"):
                    domains.append({
                        "domain": el.attrib.get("Name", ""),
                        "expires": el.attrib.get("Expires", ""),
                        "auto_renew": el.attrib.get("AutoRenew", "").lower() == "true",
                        "namecheap_dns": el.attrib.get("IsOurDNS", "").lower() == "true",
                    })

            # Calculate total pages from Paging element (first page only)
            if page == 1:
                paging = next(
                    (el for el in root.iter() if el.tag.endswith("Paging")),
                    None,
                )
                if paging is not None:
                    total_items = next(
                        (int(el.text) for el in paging if el.tag.endswith("TotalItems") and el.text),
                        0,
                    )
                    if total_items:
                        total_pages = (total_items + page_size - 1) // page_size

            page += 1

        return domains

    def get_nameservers(self, domain: str) -> list[str]:
        """Return the current nameservers for a domain."""
        sld, tld = self._sld_tld(domain)
        root = self._request("namecheap.domains.dns.getList", SLD=sld, TLD=tld)

        # IsUsingOurDNS=true means domain is on Namecheap's own DNS service
        for el in root.iter():
            if el.tag.endswith("IsUsingOurDNS") and el.text:
                if el.text.lower() == "true":
                    return ["dns1.registrar-servers.com", "dns2.registrar-servers.com"]
                break

        return [el.text for el in root.iter() if el.tag.endswith("Nameserver") and el.text]

    def set_nameservers(self, domain: str, nameservers: list[str]) -> None:
        """Update the nameservers for a domain. Raises NamecheapAPIError on failure."""
        if not 2 <= len(nameservers) <= 5:
            raise NamecheapAPIError("Namecheap requires between 2 and 5 nameservers")
        sld, tld = self._sld_tld(domain)
        self._request(
            "namecheap.domains.dns.setCustom",
            SLD=sld,
            TLD=tld,
            NameServers=",".join(nameservers),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def from_env() -> NamecheapAPI:
    """Build a NamecheapAPI instance from environment variables."""
    _load_env()
    api_user   = os.getenv("NAMECHEAP_API_USER", "").strip()
    api_key    = os.getenv("NAMECHEAP_API_KEY", "").strip()
    username   = os.getenv("NAMECHEAP_USERNAME", "").strip()
    client_ip  = os.getenv("NAMECHEAP_CLIENT_IP", "").strip()

    missing = [k for k, v in {
        "NAMECHEAP_API_USER":   api_user,
        "NAMECHEAP_API_KEY":    api_key,
        "NAMECHEAP_USERNAME":   username,
        "NAMECHEAP_CLIENT_IP":  client_ip,
    }.items() if not v]

    if missing:
        raise EnvironmentError(
            f"Missing required env vars: {', '.join(missing)}\n"
            "The owner pastes them into the settings window: "
            "python .claude/scripts/settings_window.py open --registrar namecheap\n"
            "Whitelist your IP at: Namecheap -> Account -> Profile -> API Access"
        )

    return NamecheapAPI(api_user, api_key, username, client_ip)


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

def _is_cloudflare_ns(nameservers: list[str]) -> bool:
    return any("cloudflare" in ns.lower() for ns in nameservers)


def _migrate_domain(
    nc: NamecheapAPI,
    cf: CloudflareAPI,
    domain: str,
    dry_run: bool = False,
) -> dict:
    """
    Migrate one domain from Namecheap DNS to Cloudflare.
    Returns: {domain, status, cf_nameservers, message}
    status values: already_on_cf | dry_run | migrated
    """
    result: dict = {"domain": domain, "status": "unknown", "cf_nameservers": [], "message": ""}

    # Step 1 — check if NS already point to Cloudflare
    current_ns = nc.get_nameservers(domain)
    if _is_cloudflare_ns(current_ns):
        result["status"] = "already_on_cf"
        result["message"] = f"Already using Cloudflare NS: {', '.join(current_ns)}"
        return result

    # Step 2 — ensure Cloudflare zone exists
    if cf.zone_exists(domain):
        cf_ns = cf.get_nameservers(domain)
        print(f"  Cloudflare zone already exists.")
    else:
        if dry_run:
            print(f"  [DRY RUN] Would create Cloudflare zone for {domain}")
            result["status"] = "dry_run"
            result["message"] = "Would create CF zone and update nameservers at Namecheap"
            return result
        zone = cf.add_zone(domain, jump_start=True)
        cf_ns = zone.get("name_servers", [])
        print(f"  Cloudflare zone created (DNS records auto-imported).")

    result["cf_nameservers"] = cf_ns
    print(f"  CF nameservers: {', '.join(cf_ns)}")

    # Step 3 — update NS at Namecheap
    if dry_run:
        print(f"  [DRY RUN] Would update Namecheap NS to: {', '.join(cf_ns)}")
        result["status"] = "dry_run"
        result["message"] = "Would update nameservers at Namecheap"
        return result

    print("  Mail-record check (must pass before nameservers move)...")
    if mail_check(cf, domain) != 0:
        result["status"] = "blocked"
        result["message"] = "mail-check failed: nameservers NOT changed. Fix the records in Cloudflare and run migrate again."
        return result

    nc.set_nameservers(domain, cf_ns)
    result["status"] = "migrated"
    result["message"] = "Nameservers updated at Namecheap. Propagation: 30 min – 48 hours."
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if cmd == "migrate" and not dry_run and "--owner-approved" not in sys.argv:
        print("Refusing to change nameservers: the owner must say yes first, then pass --owner-approved.",
              file=sys.stderr)
        sys.exit(1)

    try:
        nc = from_env()
    except EnvironmentError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        from cf_api import from_env as cf_from_env
        cf = cf_from_env()
    except EnvironmentError as e:
        print(f"Cloudflare config error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if cmd == "list-domains":
            print("Fetching domains from Namecheap...\n")
            domains = nc.list_domains()
            if not domains:
                print("No domains found.")
                return
            print(f"  {'Domain':<38} {'Expires':<14} NS Status")
            print(f"  {'-'*38} {'-'*14} {'-'*20}")
            for d in domains:
                ns_label = "Namecheap default" if d["namecheap_dns"] else "Custom NS"
                ar = " [AR]" if d["auto_renew"] else ""
                print(f"  {d['domain']:<38} {d['expires']:<14} {ns_label}{ar}")
            print(f"\n  Total: {len(domains)} domains  ([AR] = auto-renew on)")

        elif cmd == "get-ns":
            if len(sys.argv) < 3:
                print("Usage: namecheap_to_cf.py get-ns <domain>", file=sys.stderr)
                sys.exit(1)
            domain = sys.argv[2]
            ns = nc.get_nameservers(domain)
            print(f"Nameservers for {domain}:")
            for n in ns:
                cf_flag = "  [Cloudflare]" if "cloudflare" in n.lower() else ""
                print(f"  {n}{cf_flag}")

        elif cmd == "migrate":
            if len(sys.argv) < 3:
                print("Usage: namecheap_to_cf.py migrate <domain> --owner-approved", file=sys.stderr)
                sys.exit(1)
            domain = root_domain(sys.argv[2])
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"{prefix}Migrating {domain} to Cloudflare...\n")
            result = _migrate_domain(nc, cf, domain, dry_run=dry_run)
            print(f"\n  Status:  {result['status']}")
            print(f"  Message: {result['message']}")
            if result["status"] == "blocked":
                sys.exit(1)

        elif cmd == "status":
            if len(sys.argv) < 3:
                print("Usage: namecheap_to_cf.py status <domain>", file=sys.stderr)
                sys.exit(1)
            domain = sys.argv[2]
            print(f"Migration status for {domain}\n")

            nc_ns = nc.get_nameservers(domain)
            print(f"  Current NS (Namecheap): {', '.join(nc_ns) or '(none)'}")

            if cf.zone_exists(domain):
                cf_ns = cf.get_nameservers(domain)
                zone = cf.get_zone(domain)
                cf_status = zone.get("status", "unknown")
                print(f"  Cloudflare zone:        {zone.get('id', '?')} ({cf_status})")
                print(f"  Expected CF NS:         {', '.join(cf_ns)}")
                if _is_cloudflare_ns(nc_ns):
                    print(f"\n  Migration complete — NS point to Cloudflare.")
                    if cf_status == "active":
                        print(f"  Zone is ACTIVE. Proxy and SSL are live.")
                    else:
                        print(f"  Zone status '{cf_status}' — may still be propagating.")
                else:
                    print(f"\n  NS not yet updated or still propagating.")
                    print(f"  Run: python namecheap_to_cf.py migrate {domain}")
            else:
                print(f"\n  No Cloudflare zone found for {domain}.")
                print(f"  Run: python namecheap_to_cf.py migrate {domain}")

        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__)
            sys.exit(1)

    except NamecheapAPIError as e:
        print(f"Namecheap error: {e}", file=sys.stderr)
        sys.exit(1)
    except CloudflareAPIError as e:
        print(f"Cloudflare error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {describe_request_error(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
