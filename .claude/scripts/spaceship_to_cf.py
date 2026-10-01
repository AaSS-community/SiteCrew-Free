"""
Spaceship -> Cloudflare domain migration for SiteCrew Architect.

Migrates domains from Spaceship DNS to Cloudflare by:
  1. Adding the domain as a zone in Cloudflare (jump_start imports existing DNS records)
  2. Fetching the assigned Cloudflare nameservers
  3. Updating the domain's nameservers at Spaceship (async - polls for completion)

Required .env vars:
  SPACESHIP_API_KEY       Your Spaceship API key   (dashboard -> API)
  SPACESHIP_API_SECRET    Your Spaceship API secret (dashboard -> API)
  CF_API_TOKEN            Cloudflare API token (Zone Read, DNS Edit, Zone Edit to add a zone)
  CF_ACCOUNT_ID           Cloudflare account ID

Usage:
  python spaceship_to_cf.py list-domains
  python spaceship_to_cf.py get-ns <domain>
  python spaceship_to_cf.py migrate <domain> --owner-approved
  python spaceship_to_cf.py migrate <domain> --dry-run
  python spaceship_to_cf.py status <domain>

Notes:
  - Changing nameservers needs --owner-approved (the owner said yes) AND a passing
    mail-check, run automatically right before the change. One domain at a time.
  - Spaceship nameserver updates return HTTP 202 (async). The script polls until
    the operation completes (up to 60 seconds per domain).
  - jump_start=true tells Cloudflare to auto-import existing DNS records.
  - DNS propagation after migration takes 30 minutes to 48 hours.
"""
from __future__ import annotations

import os
import sys
import time
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

class SpaceshipAPIError(Exception):
    pass


# ---------------------------------------------------------------------------
# Spaceship API client
# ---------------------------------------------------------------------------

class SpaceshipAPI:
    """Thin wrapper around the Spaceship REST API (v1)."""

    BASE = "https://spaceship.dev/api/v1"

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key":    api_key,
            "X-API-Secret": api_secret,
            "Accept":       "application/json",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, **params) -> dict:
        r = self.session.get(f"{self.BASE}{path}", params=params or None, timeout=30)
        self._raise_for_status(r)
        return r.json()

    def _put(self, path: str, json: dict) -> requests.Response:
        """PUT — returns raw response so callers can inspect status and headers."""
        return self.session.put(f"{self.BASE}{path}", json=json, timeout=30)

    @staticmethod
    def _raise_for_status(r: requests.Response) -> None:
        if r.status_code == 401:
            raise SpaceshipAPIError(
                "Authentication failed — check SPACESHIP_API_KEY and SPACESHIP_API_SECRET"
            )
        if r.status_code == 403:
            raise SpaceshipAPIError("Forbidden — API credentials lack required permissions")
        if r.status_code == 404:
            raise SpaceshipAPIError(f"Not found: {r.url}")
        if not r.ok:
            try:
                body = r.json()
                msg = body.get("message") or body.get("error") or r.text[:200]
            except Exception:
                msg = r.text[:200]
            raise SpaceshipAPIError(f"HTTP {r.status_code}: {msg}")

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        try:
            self._get("/domains", take=1, skip=0)
            return True
        except SpaceshipAPIError:
            return False

    def list_domains(self, page_size: int = 100) -> list[dict]:
        """Return all domains from Spaceship. Paginates automatically (100/page)."""
        domains: list[dict] = []
        skip = 0

        while True:
            body = self._get("/domains", take=page_size, skip=skip)
            items = body.get("items", [])
            total = body.get("total", 0)

            for item in items:
                # unicodeName is the human-readable form; name may be ACE-encoded (xn--)
                fqdn = item.get("unicodeName") or item.get("name", "")
                ns_hosts = item.get("nameservers", {}).get("hosts", [])
                ns_provider = item.get("nameservers", {}).get("provider", "")

                expires_raw = item.get("expirationDate", "")
                expires = expires_raw[:10] if expires_raw else ""  # ISO 8601 -> YYYY-MM-DD

                domains.append({
                    "domain":           fqdn.lower(),
                    "expires":          expires,
                    "auto_renew":       bool(item.get("autoRenew", False)),
                    "nameservers":      ns_hosts,
                    "spaceship_dns":    ns_provider != "custom",
                    "lifecycle_status": item.get("lifecycleStatus", ""),
                })

            skip += page_size
            if len(items) < page_size or skip >= total:
                break

        return domains

    def get_nameservers(self, domain: str) -> list[str]:
        """Return the current nameservers for a domain."""
        body = self._get(f"/domains/{domain}")
        return body.get("nameservers", {}).get("hosts", [])

    def set_nameservers(self, domain: str, nameservers: list[str], poll_timeout: int = 60) -> None:
        """
        Update nameservers for a domain.

        Spaceship write operations return HTTP 202 (async) with a
        'spaceship-async-operationid' header. This method blocks until
        the operation completes, fails, or poll_timeout seconds elapse.
        """
        r = self._put(
            f"/domains/{domain}/nameservers",
            json={"provider": "custom", "hosts": nameservers},
        )

        if r.status_code == 200:
            return  # synchronous success

        if r.status_code == 202:
            op_id = r.headers.get("spaceship-async-operationid", "")
            if op_id:
                self._poll_operation(op_id, timeout=poll_timeout)
            return

        self._raise_for_status(r)

    def _poll_operation(self, operation_id: str, timeout: int = 60, interval: int = 3) -> None:
        """Poll GET /async-operations/{id} until status is success, failed, or timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            body = self._get(f"/async-operations/{operation_id}")
            status = body.get("status", "pending")
            if status == "success":
                return
            if status == "failed":
                details = body.get("details") or body
                raise SpaceshipAPIError(f"Async operation failed: {details}")
            time.sleep(interval)
        raise SpaceshipAPIError(
            f"Async operation {operation_id} timed out after {timeout}s. "
            "The change may still complete — verify in your Spaceship account."
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def from_env() -> SpaceshipAPI:
    """Build a SpaceshipAPI instance from environment variables."""
    _load_env()
    api_key    = os.getenv("SPACESHIP_API_KEY", "").strip()
    api_secret = os.getenv("SPACESHIP_API_SECRET", "").strip()

    missing = [k for k, v in {
        "SPACESHIP_API_KEY":    api_key,
        "SPACESHIP_API_SECRET": api_secret,
    }.items() if not v]

    if missing:
        raise EnvironmentError(
            f"Missing required env vars: {', '.join(missing)}\n"
            "Add them to .claude/scripts/.env or the project root .env"
        )

    return SpaceshipAPI(api_key, api_secret)


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

def _is_cloudflare_ns(nameservers: list[str]) -> bool:
    return any("cloudflare" in ns.lower() for ns in nameservers)


def _migrate_domain(
    ss: SpaceshipAPI,
    cf: CloudflareAPI,
    domain: str,
    dry_run: bool = False,
) -> dict:
    """
    Migrate one domain from Spaceship DNS to Cloudflare.
    Returns: {domain, status, cf_nameservers, message}
    status values: already_on_cf | dry_run | migrated
    """
    result: dict = {"domain": domain, "status": "unknown", "cf_nameservers": [], "message": ""}

    # Step 1 — check if NS already point to Cloudflare
    current_ns = ss.get_nameservers(domain)
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
            result["message"] = "Would create CF zone and update nameservers at Spaceship"
            return result
        zone = cf.add_zone(domain, jump_start=True)
        cf_ns = zone.get("name_servers", [])
        print(f"  Cloudflare zone created (DNS records auto-imported).")

    result["cf_nameservers"] = cf_ns
    print(f"  CF nameservers: {', '.join(cf_ns)}")

    # Step 3 — update NS at Spaceship (async, polls for completion)
    if dry_run:
        print(f"  [DRY RUN] Would update Spaceship NS to: {', '.join(cf_ns)}")
        result["status"] = "dry_run"
        result["message"] = "Would update nameservers at Spaceship"
        return result

    print("  Mail-record check (must pass before nameservers move)...")
    if mail_check(cf, domain) != 0:
        result["status"] = "blocked"
        result["message"] = "mail-check failed: nameservers NOT changed. Fix the records in Cloudflare and run migrate again."
        return result

    print(f"  Updating nameservers at Spaceship (async, polling up to 60s)...")
    ss.set_nameservers(domain, cf_ns)
    result["status"] = "migrated"
    result["message"] = "Nameservers updated at Spaceship. Propagation: 30 min – 48 hours."
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
        ss = from_env()
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
            print("Fetching domains from Spaceship...\n")
            domains = ss.list_domains()
            if not domains:
                print("No domains found.")
                return
            print(f"  {'Domain':<38} {'Expires':<14} NS Status")
            print(f"  {'-'*38} {'-'*14} {'-'*25}")
            for d in domains:
                if _is_cloudflare_ns(d["nameservers"]):
                    ns_label = "Cloudflare [active]"
                elif d["spaceship_dns"]:
                    ns_label = "Spaceship default"
                elif d["nameservers"]:
                    ns_label = f"Custom ({d['nameservers'][0]})"
                else:
                    ns_label = "Custom NS"
                ar = " [AR]" if d["auto_renew"] else ""
                print(f"  {d['domain']:<38} {d['expires']:<14} {ns_label}{ar}")
            print(f"\n  Total: {len(domains)} domains  ([AR] = auto-renew on)")

        elif cmd == "get-ns":
            if len(sys.argv) < 3:
                print("Usage: spaceship_to_cf.py get-ns <domain>", file=sys.stderr)
                sys.exit(1)
            domain = sys.argv[2]
            ns = ss.get_nameservers(domain)
            print(f"Nameservers for {domain}:")
            for n in ns:
                cf_flag = "  [Cloudflare]" if "cloudflare" in n.lower() else ""
                print(f"  {n}{cf_flag}")

        elif cmd == "migrate":
            if len(sys.argv) < 3:
                print("Usage: spaceship_to_cf.py migrate <domain> --owner-approved", file=sys.stderr)
                sys.exit(1)
            domain = root_domain(sys.argv[2])
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"{prefix}Migrating {domain} to Cloudflare...\n")
            result = _migrate_domain(ss, cf, domain, dry_run=dry_run)
            print(f"\n  Status:  {result['status']}")
            print(f"  Message: {result['message']}")
            if result["status"] == "blocked":
                sys.exit(1)

        elif cmd == "status":
            if len(sys.argv) < 3:
                print("Usage: spaceship_to_cf.py status <domain>", file=sys.stderr)
                sys.exit(1)
            domain = sys.argv[2]
            print(f"Migration status for {domain}\n")

            current_ns = ss.get_nameservers(domain)
            print(f"  Current NS (Spaceship): {', '.join(current_ns) or '(none)'}")

            if cf.zone_exists(domain):
                cf_ns = cf.get_nameservers(domain)
                zone = cf.get_zone(domain)
                cf_status = zone.get("status", "unknown")
                print(f"  Cloudflare zone:        {zone.get('id', '?')} ({cf_status})")
                print(f"  Expected CF NS:         {', '.join(cf_ns)}")
                if _is_cloudflare_ns(current_ns):
                    print(f"\n  Migration complete — NS point to Cloudflare.")
                    if cf_status == "active":
                        print(f"  Zone is ACTIVE. Proxy and SSL are live.")
                    else:
                        print(f"  Zone status '{cf_status}' — may still be propagating.")
                else:
                    print(f"\n  NS not yet updated or still propagating.")
                    print(f"  Run: python spaceship_to_cf.py migrate {domain}")
            else:
                print(f"\n  No Cloudflare zone found for {domain}.")
                print(f"  Run: python spaceship_to_cf.py migrate {domain}")

        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__)
            sys.exit(1)

    except SpaceshipAPIError as e:
        print(f"Spaceship error: {e}", file=sys.stderr)
        sys.exit(1)
    except CloudflareAPIError as e:
        print(f"Cloudflare error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {describe_request_error(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
