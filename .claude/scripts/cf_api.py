"""
Cloudflare API wrapper for SiteCrew Architect.

Handles DNS records, zone management, Cloudflare Pages, and the mail-record
check that must pass before nameservers move.

Required .env vars:
  CF_API_TOKEN    API token: Zone > Zone > Read + Zone > DNS > Edit (both limited to your one zone)
                  + Account > Cloudflare Pages > Edit
                  Create at: https://dash.cloudflare.com/profile/api-tokens
                  The owner pastes it into .env, never into the chat.
  CF_ACCOUNT_ID   Your Cloudflare account ID (dashboard, your domain, Overview, API section)

Optional .env vars (speeds up operations — otherwise looked up by domain name):
  CF_ZONE_ID      Pre-set zone ID for the active client domain

API reference: https://developers.cloudflare.com/api/

Usage:
  python cf_api.py zones
  python cf_api.py zone-id <domain>
  python cf_api.py zone-exists <domain>
  python cf_api.py add-zone <domain> [--no-jump-start]
  python cf_api.py records <domain>
  python cf_api.py add-cname <domain> <name> <target> [--no-proxy]
  python cf_api.py pages-list
  python cf_api.py pages-create <project-name> <github-owner> <github-repo> [branch] [--build-command "cmd"] [--output-dir "dir"]
  python cf_api.py pages-deploy <project-name> [branch]
  python cf_api.py dns-conflicts <domain>
  python cf_api.py pages-domain <project-name> <domain>
  python cf_api.py pages-dns <domain> <project-name> --owner-approved
  python cf_api.py ssl <domain> [strict|full|flexible|off]
  python cf_api.py purge <domain>
  python cf_api.py nameservers <domain>
  python cf_api.py mail-check <domain>
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import requests

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

def _load_env() -> None:
    script_dir = Path(__file__).parent
    for candidate in [script_dir / ".env", script_dir.parent.parent / ".env"]:
        if candidate.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(candidate, override=False)
            except ImportError:
                _parse_env(candidate)
            return


def _parse_env(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

def root_domain(domain: str) -> str:
    """Lower-case the name and drop an exact leading 'www.' (never a bare w/dot run)."""
    d = domain.strip().lower().lstrip(".")
    return d.removeprefix("www.")


def describe_request_error(e: Exception) -> str:
    """Exception type and HTTP status only. Never str(e): it can carry a URL with a key."""
    status = getattr(getattr(e, "response", None), "status_code", None)
    return type(e).__name__ + (f" (HTTP {status})" if status else "")


class CloudflareAPIError(Exception):
    def __init__(self, message: str, status_code: int = 0, errors: list = None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class CloudflareAPI:
    """
    Thin wrapper around the Cloudflare v4 REST API.
    Full reference: https://developers.cloudflare.com/api/
    """

    BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self, api_token: str, account_id: str = ""):
        self.account_id = account_id
        self._zone_cache: dict[str, str] = {}  # domain → zone_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, **kwargs) -> dict | list:
        r = self.session.get(f"{self.BASE}{path}", **kwargs)
        return self._unwrap(r)

    def _post(self, path: str, **kwargs) -> dict:
        r = self.session.post(f"{self.BASE}{path}", **kwargs)
        return self._unwrap(r)

    def _patch(self, path: str, **kwargs) -> dict:
        r = self.session.patch(f"{self.BASE}{path}", **kwargs)
        return self._unwrap(r)

    def _put(self, path: str, **kwargs) -> dict:
        r = self.session.put(f"{self.BASE}{path}", **kwargs)
        return self._unwrap(r)

    def _delete(self, path: str, **kwargs) -> dict:
        r = self.session.delete(f"{self.BASE}{path}", **kwargs)
        return self._unwrap(r)

    @staticmethod
    def _unwrap(r: requests.Response) -> dict | list:
        """Cloudflare wraps everything in {success, errors, result}."""
        try:
            body = r.json()
        except Exception:
            raise CloudflareAPIError(f"Non-JSON response ({r.status_code}): {r.text[:200]}", r.status_code)

        if not body.get("success", False):
            errors = body.get("errors", [])
            msg = "; ".join(e.get("message", str(e)) for e in errors) or r.text
            raise CloudflareAPIError(f"Cloudflare error: {msg}", r.status_code, errors)

        return body.get("result")

    # ------------------------------------------------------------------
    # Zones
    # ------------------------------------------------------------------

    def _get_all(self, path: str, params: dict) -> list:
        """GET every page of a list endpoint (100 per page)."""
        out: list = []
        page = 1
        while True:
            batch = self._get(path, params={**params, "per_page": 100, "page": page})
            out += batch
            if len(batch) < 100:
                return out
            page += 1

    def list_zones(self) -> list:
        """List all zones in the account."""
        return self._get("/zones", params={"per_page": 100})

    def get_zone_id(self, domain: str) -> str:
        """Look up the zone ID for a domain. Results are cached per instance."""
        if domain in self._zone_cache:
            return self._zone_cache[domain]

        # Strip www. prefix if present — zones are registered on the root domain
        root = root_domain(domain)
        zones = self._get("/zones", params={"name": root, "per_page": 5})
        if not zones:
            raise CloudflareAPIError(
                f"No Cloudflare zone found for '{root}'. "
                "Make sure the domain is added to your Cloudflare account."
            )
        zone_id = zones[0]["id"]
        self._zone_cache[domain] = zone_id
        self._zone_cache[root] = zone_id
        return zone_id

    def get_zone(self, domain: str) -> dict:
        zone_id = self.get_zone_id(domain)
        return self._get(f"/zones/{zone_id}")

    def get_nameservers(self, domain: str) -> list[str]:
        """Return the Cloudflare nameservers assigned to this zone."""
        zone = self.get_zone(domain)
        return zone.get("name_servers", [])

    def add_zone(self, domain: str, jump_start: bool = True) -> dict:
        """
        Add a domain as a new zone in Cloudflare.

        jump_start=True tells Cloudflare to auto-import existing DNS records from the
        domain's current nameservers — saves manual re-entry of MX, A, CNAME records.

        CF_ACCOUNT_ID must be set. Returns the zone object, which includes
        'name_servers' (the two CF nameservers assigned to this zone).
        """
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required to add a zone")
        payload = {
            "name": domain,
            "jump_start": jump_start,
            "account": {"id": self.account_id},
            "type": "full",
        }
        zone = self._post("/zones", json=payload)
        self._zone_cache[domain] = zone["id"]
        return zone

    def zone_exists(self, domain: str) -> bool:
        """Return True if this domain already has a zone in Cloudflare, False otherwise."""
        try:
            self.get_zone_id(domain)
            return True
        except CloudflareAPIError:
            return False

    # ------------------------------------------------------------------
    # DNS Records
    # ------------------------------------------------------------------

    def list_records(
        self,
        domain: str,
        record_type: str = "",
        name: str = "",
    ) -> list:
        """List DNS records. Optionally filter by type and/or name."""
        zone_id = self.get_zone_id(domain)
        params: dict = {}
        if record_type:
            params["type"] = record_type.upper()
        if name:
            params["name"] = name
        return self._get_all(f"/zones/{zone_id}/dns_records", params)

    def create_record(
        self,
        domain: str,
        record_type: str,
        name: str,
        content: str,
        proxied: bool = True,
        ttl: int = 1,  # 1 = automatic when proxied
        priority: int = 0,
    ) -> dict:
        """Create a DNS record. Returns the created record object (includes id)."""
        zone_id = self.get_zone_id(domain)
        payload: dict = {
            "type": record_type.upper(),
            "name": name,
            "content": content,
            "proxied": proxied,
            "ttl": 1 if proxied else ttl,
        }
        if record_type.upper() == "MX":
            payload["priority"] = priority
        return self._post(f"/zones/{zone_id}/dns_records", json=payload)

    def update_record(self, domain: str, record_id: str, **fields) -> dict:
        """Patch specific fields on an existing DNS record."""
        zone_id = self.get_zone_id(domain)
        return self._patch(f"/zones/{zone_id}/dns_records/{record_id}", json=fields)

    def delete_record(self, domain: str, record_id: str) -> dict:
        zone_id = self.get_zone_id(domain)
        return self._delete(f"/zones/{zone_id}/dns_records/{record_id}")

    def upsert_record(
        self,
        domain: str,
        record_type: str,
        name: str,
        content: str,
        proxied: bool = True,
    ) -> dict:
        """
        Idempotent: create the DNS record if it doesn't exist, update it if it does.
        Matches on type + name. If multiple exist, updates the first and deletes the rest.
        """
        existing = self.list_records(domain, record_type=record_type, name=name)
        if not existing:
            return self.create_record(domain, record_type, name, content, proxied)

        # Update first match
        record = self.update_record(
            domain, existing[0]["id"],
            content=content, proxied=proxied, ttl=1 if proxied else 3600,
        )
        # Remove duplicates
        for dup in existing[1:]:
            self.delete_record(domain, dup["id"])
        return record


    # ------------------------------------------------------------------
    # SSL / TLS settings
    # ------------------------------------------------------------------

    def get_ssl_mode(self, domain: str) -> str:
        """Returns the current SSL mode: off | flexible | full | strict."""
        zone_id = self.get_zone_id(domain)
        result = self._get(f"/zones/{zone_id}/settings/ssl")
        return result.get("value", "unknown")

    def set_ssl_mode(self, domain: str, mode: str = "full") -> dict:
        """
        Set SSL mode. Recommended: 'full' (cert not verified) or 'strict' (cert verified).
        Cloudflare Pages manages its own certificate, so the default is fine.
        """
        valid = {"off", "flexible", "full", "strict"}
        if mode not in valid:
            raise ValueError(f"SSL mode must be one of: {valid}")
        zone_id = self.get_zone_id(domain)
        return self._patch(f"/zones/{zone_id}/settings/ssl", json={"value": mode})

    def set_always_https(self, domain: str, enabled: bool = True) -> dict:
        """Redirect all HTTP traffic to HTTPS."""
        zone_id = self.get_zone_id(domain)
        return self._patch(
            f"/zones/{zone_id}/settings/always_use_https",
            json={"value": "on" if enabled else "off"},
        )

    def set_min_tls(self, domain: str, version: str = "1.2") -> dict:
        zone_id = self.get_zone_id(domain)
        return self._patch(
            f"/zones/{zone_id}/settings/min_tls_version",
            json={"value": version},
        )

    def harden_ssl(self, domain: str) -> None:
        """Apply recommended SSL/TLS hardening: full SSL + always HTTPS + TLS 1.2+."""
        self.set_ssl_mode(domain, "full")
        self.set_always_https(domain, True)
        self.set_min_tls(domain, "1.2")

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def purge_cache(self, domain: str) -> dict:
        """Purge all cached assets for this zone."""
        zone_id = self.get_zone_id(domain)
        return self._post(
            f"/zones/{zone_id}/purge_cache",
            json={"purge_everything": True},
        )

    # ------------------------------------------------------------------
    # Cloudflare Pages
    # ------------------------------------------------------------------

    def list_pages_projects(self) -> list:
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required for Pages operations")
        return self._get(f"/accounts/{self.account_id}/pages/projects")

    def get_pages_project(self, project_name: str) -> Optional[dict]:
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required for Pages operations")
        try:
            return self._get(f"/accounts/{self.account_id}/pages/projects/{project_name}")
        except CloudflareAPIError as e:
            if e.status_code == 404:
                return None
            raise

    def create_pages_project(
        self,
        project_name: str,
        github_owner: str,
        github_repo: str,
        branch: str = "main",
        build_command: str = "",
        destination_dir: str = "/",
    ) -> dict:
        """
        Create a Cloudflare Pages project linked to a GitHub repo.

        Prerequisites:
        - GitHub must be connected to your Cloudflare account (done once in the dashboard:
          Workers & Pages → Create Application → Pages → Connect to Git)
        - The GitHub account/org must have authorized Cloudflare Pages

        Returns the created project object.
        """
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required for Pages operations")

        payload = {
            "name": project_name,
            "production_branch": branch,
            "source": {
                "type": "github",
                "config": {
                    "owner": github_owner,
                    "repo_name": github_repo,
                    "production_branch": branch,
                    "pr_comments_enabled": False,
                    "deployments_enabled": True,
                },
            },
            "build_config": {
                "build_command": build_command,
                "destination_dir": destination_dir,
                "root_dir": "",
            },
        }
        return self._post(
            f"/accounts/{self.account_id}/pages/projects",
            json=payload,
        )

    def dns_conflicts(self, domain: str) -> list:
        """A, AAAA and CNAME records at exactly the apex and www (what Pages DNS would replace)."""
        root = root_domain(domain)
        names = {root, f"www.{root}"}
        return [r for r in self.list_records(root)
                if r["type"] in ("A", "AAAA", "CNAME") and r["name"].lower().rstrip(".") in names]

    def point_to_pages(self, domain: str, project_name: str) -> list:
        """
        After the owner's yes: delete exactly the A/AAAA/CNAME records at the apex and www,
        then create proxied CNAMEs to the Pages project. Nothing else is touched (MX, TXT,
        other names). Returns the records that were deleted.
        """
        pages_target = f"{project_name}.pages.dev"
        root = root_domain(domain)
        removed = self.dns_conflicts(root)
        for rec in removed:
            self.delete_record(root, rec["id"])
        self.create_record(root, "CNAME", root, pages_target, proxied=True)
        self.create_record(root, "CNAME", f"www.{root}", pages_target, proxied=True)
        return removed

    def trigger_pages_deployment(self, project_name: str, branch: str = "main") -> dict:
        """Trigger a new deployment for a Pages project from a specific branch."""
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required for Pages operations")
        # Documented as multipart form data; drop the session's JSON content type for this call.
        return self._post(
            f"/accounts/{self.account_id}/pages/projects/{project_name}/deployments",
            files={"branch": (None, branch)},
            headers={"Content-Type": None},
        )

    def set_pages_custom_domain(self, project_name: str, domain: str) -> dict:
        """Add a custom domain to a Cloudflare Pages project."""
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required for Pages operations")
        return self._post(
            f"/accounts/{self.account_id}/pages/projects/{project_name}/domains",
            json={"name": domain},
        )

    def get_pages_domain(self, project_name: str, domain: str) -> Optional[dict]:
        if not self.account_id:
            raise CloudflareAPIError("CF_ACCOUNT_ID is required for Pages operations")
        try:
            return self._get(f"/accounts/{self.account_id}/pages/projects/{project_name}/domains/{domain}")
        except CloudflareAPIError as e:
            if e.status_code == 404:
                return None
            raise


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def from_env() -> CloudflareAPI:
    """Build a CloudflareAPI instance from environment variables."""
    _load_env()
    token = os.getenv("CF_API_TOKEN", "").strip()
    account_id = os.getenv("CF_ACCOUNT_ID", "").strip()
    if not token:
        raise EnvironmentError(
            "CF_API_TOKEN not set.\n"
            "Create a token at https://dash.cloudflare.com/profile/api-tokens\n"
            "Required permissions: Zone Read, DNS Edit (one zone), Cloudflare Pages Edit"
        )
    return CloudflareAPI(token, account_id)


# ---------------------------------------------------------------------------
# Mail-record check (run BEFORE nameservers move)
# ---------------------------------------------------------------------------

DKIM_SELECTORS = ["default", "google", "selector1", "selector2", "k1",
                  "zoho", "zmail", "s1", "s2", "mail", "dkim"]
DOH = "https://cloudflare-dns.com/dns-query"


class DNSReadError(Exception):
    """A DNS answer could not be read or is incomplete. Never treated as 'record absent'."""


def parse_txt(value: str) -> str:
    """Decode DNS TXT text: quoted character strings (with \\" \\\\ and \\DDD escapes) are
    decoded and concatenated; unquoted text is returned as is."""
    value = value.strip()
    if not value.startswith('"'):
        return value
    out, i, n = [], 0, len(value)
    while i < n:
        if value[i] in " \t":
            i += 1
        elif value[i] == '"':
            i += 1
            while i < n and value[i] != '"':
                if value[i] == "\\" and i + 1 < n:
                    if value[i + 1:i + 4].isdigit() and len(value[i + 1:i + 4]) == 3:
                        out.append(chr(int(value[i + 1:i + 4])))
                        i += 4
                    else:
                        out.append(value[i + 1])
                        i += 2
                else:
                    out.append(value[i])
                    i += 1
            i += 1
        else:
            out.append(value[i])
            i += 1
    return "".join(out)


def _norm(rtype: str, value: str) -> str:
    if rtype == "TXT":
        return parse_txt(value)
    value = value.strip()
    if rtype == "MX":
        pri, _, host = value.partition(" ")
        return f"{pri} {host.strip().rstrip('.').lower()}"
    return value.rstrip(".").lower()


def _doh(name: str, rtype: str) -> list[str]:
    """Answers the public DNS gives right now (the OLD DNS before the switch).
    Fails closed: any error, SERVFAIL, truncation raises DNSReadError. Only NOERROR (0)
    and NXDOMAIN (3) are real answers."""
    try:
        r = requests.get(DOH, params={"name": name, "type": rtype},
                         headers={"accept": "application/dns-json"}, timeout=15)
        r.raise_for_status()
        body = r.json()
    except (requests.RequestException, ValueError) as e:
        raise DNSReadError(f"could not read {name} {rtype}; try again ({describe_request_error(e)})")
    if body.get("Status") not in (0, 3) or body.get("TC"):
        raise DNSReadError(f"could not read {name} {rtype}; try again (DNS status {body.get('Status')})")
    wanted = {"MX": 15, "TXT": 16, "CNAME": 5}[rtype]
    out = []
    for a in body.get("Answer", []) or []:
        # A CNAME'd name also returns its target's records: keep only the queried name's own.
        if a.get("type") == wanted and a.get("name", "").rstrip(".").lower() == name.lower():
            out.append(_norm(rtype, a["data"]))
    return sorted(set(out))


def _keep(rtype: str, name: str, root: str, values: list[str]) -> list[str]:
    """Only the mail-relevant TXT kind for each name (SPF, DMARC, DKIM)."""
    if rtype != "TXT":
        return values
    if name == root:
        return [v for v in values if v.lower().startswith("v=spf1")]
    if name.startswith("_dmarc."):
        return [v for v in values if v.upper().startswith("V=DMARC1")]
    return [v for v in values if "p=" in v]


def mail_check(cf: CloudflareAPI, domain: str) -> int:
    """Compare mail records seen in public DNS with the Cloudflare zone.
    0 = every old record is in Cloudflare, 1 = mismatch or could not read."""
    root = root_domain(domain)
    checks = [("MX", root, "MX"), ("TXT", root, "TXT (SPF)"),
              ("TXT", f"_dmarc.{root}", "TXT (DMARC)"),
              ("CNAME", f"autodiscover.{root}", "CNAME")]
    checks += [("TXT", f"{sel}._domainkey.{root}", f"TXT (DKIM {sel})") for sel in DKIM_SELECTORS]
    checks += [("CNAME", f"{sel}._domainkey.{root}", f"CNAME (DKIM {sel})") for sel in DKIM_SELECTORS]

    cf_records = cf.list_records(root)  # every page
    problems = []
    print(f"Mail records for {root}: public DNS now (old) vs Cloudflare zone\n")
    for rtype, name, label in checks:
        try:
            old = _keep(rtype, name, root, _doh(name, rtype))
        except DNSReadError as e:
            print(f"FAIL: {e}")
            print("Do NOT change nameservers. Run mail-check again.")
            return 1
        new, proxied = [], []
        for rec in cf_records:
            if rec["type"] != rtype or rec["name"].lower().rstrip(".") != name:
                continue
            content = rec["content"]
            if rtype == "MX":
                content = f"{rec.get('priority', 0)} {content}"
            new.append(_norm(rtype, content))
            if rtype == "CNAME" and rec.get("proxied"):
                proxied.append(name)
        new = sorted(set(_keep(rtype, name, root, new)))
        if not old and not new:
            continue
        missing = [v for v in old if v not in new]
        status = "OK" if not missing and not proxied else ("PROXIED" if not missing else "MISSING")
        print(f"[{status}] {label}  {name}")
        print(f"    old DNS:    {'; '.join(old) or '-'}")
        print(f"    Cloudflare: {'; '.join(new) or '-'}")
        for v in missing:
            problems.append(f"{label} {name}: {v}")
        if proxied:
            problems.append(f"{label} {name}: must be DNS only (turn the orange cloud off)")

    print()
    print("Limit: DKIM selectors can't be listed from outside; compare with your "
          "mail provider's setup page too.")
    if problems:
        print(f"\nMISMATCH ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        print("Fix them in Cloudflare (mail records must be DNS only) and run mail-check again.")
        print("Do NOT change nameservers until this passes.")
        return 1
    print("PASS: every mail record found in the old DNS is in Cloudflare.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    if sys.argv[1] == "pages-dns" and "--owner-approved" not in sys.argv:
        print("Refusing: show the owner the records from dns-conflicts, get their yes, "
              "then pass --owner-approved.", file=sys.stderr)
        sys.exit(1)

    try:
        cf = from_env()
    except EnvironmentError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "zones":
            for z in cf.list_zones():
                status = z.get("status", "?")
                print(f"  [{z['id']}] {z['name']} — {status}")

        elif cmd == "zone-id":
            domain = sys.argv[2]
            print(cf.get_zone_id(domain))

        elif cmd == "zone-exists":
            domain = sys.argv[2]
            exists = cf.zone_exists(domain)
            print("yes" if exists else "no")
            sys.exit(0 if exists else 1)

        elif cmd == "add-zone":
            domain = sys.argv[2]
            jump_start = "--no-jump-start" not in sys.argv
            zone = cf.add_zone(domain, jump_start=jump_start)
            ns = ", ".join(zone.get("name_servers", []))
            print(f"OK Zone created: {zone['name']} [{zone['id']}]")
            print(f"  Cloudflare nameservers: {ns}")
            print(f"  Status: {zone.get('status', '?')}")
            if jump_start:
                print(f"  DNS records imported from existing nameservers (jump_start=true)")

        elif cmd == "nameservers":
            domain = sys.argv[2]
            for ns in cf.get_nameservers(domain):
                print(f"  {ns}")

        elif cmd == "mail-check":
            sys.exit(mail_check(cf, sys.argv[2]))

        elif cmd == "dns-conflicts":
            found = cf.dns_conflicts(sys.argv[2])
            if not found:
                print("No A, AAAA or CNAME records at the root or www.")
            for r in found:
                proxy = "proxied" if r.get("proxied") else "DNS-only"
                print(f"  {r['type']:5} {r['name']:40} -> {r['content']} ({proxy})")

        elif cmd == "records":
            domain = sys.argv[2]
            rtype = sys.argv[3] if len(sys.argv) > 3 else ""
            records = cf.list_records(domain, record_type=rtype)
            if records:
                for r in records:
                    proxy = "proxied" if r.get("proxied") else "DNS-only"
                    print(f"  [{r['id'][:8]}] {r['type']:5} {r['name']:40} -> {r['content']} ({proxy})")
            else:
                print("No records found.")


        elif cmd == "add-cname":
            domain, name, target = sys.argv[2], sys.argv[3], sys.argv[4]
            proxied = "--no-proxy" not in sys.argv
            r = cf.upsert_record(domain, "CNAME", name, target, proxied=proxied)
            print(f"OK CNAME: {r['name']} -> {r['content']}")

        elif cmd == "ssl":
            domain = sys.argv[2]
            if len(sys.argv) > 3:
                cf.set_ssl_mode(domain, sys.argv[3])
                print(f"OK SSL mode set to: {sys.argv[3]}")
            else:
                print(f"SSL mode: {cf.get_ssl_mode(domain)}")

        elif cmd == "harden":
            domain = sys.argv[2]
            cf.harden_ssl(domain)
            print(f"OK SSL hardened: full SSL + always HTTPS + TLS 1.2+ ({domain})")

        elif cmd == "purge":
            domain = sys.argv[2]
            cf.purge_cache(domain)
            print(f"OK Cache purged: {domain}")

        elif cmd == "pages-list":
            projects = cf.list_pages_projects()
            if projects:
                for p in projects:
                    print(f"  {p['name']} - {p.get('subdomain', '?')}.pages.dev")
            else:
                print("No Pages projects found.")

        elif cmd == "pages-create":
            # pages-create <project-name> <github-owner> <github-repo> [branch] [--build-command "cmd"] [--output-dir "dir"]
            project_name = sys.argv[2]
            github_owner = sys.argv[3]
            github_repo = sys.argv[4]
            # Parse remaining positional and flag args
            remaining = sys.argv[5:]
            branch = "main"
            build_command = ""
            output_dir = "/"
            i = 0
            while i < len(remaining):
                if remaining[i] == "--build-command" and i + 1 < len(remaining):
                    build_command = remaining[i + 1]
                    i += 2
                elif remaining[i] == "--output-dir" and i + 1 < len(remaining):
                    output_dir = remaining[i + 1]
                    i += 2
                elif not remaining[i].startswith("--"):
                    branch = remaining[i]
                    i += 1
                else:
                    i += 1
            result = cf.create_pages_project(
                project_name, github_owner, github_repo, branch,
                build_command=build_command, destination_dir=output_dir,
            )
            print(f"OK Pages project created: {result['name']}")
            print(f"  URL: https://{result.get('subdomain', result['name'])}.pages.dev")
            if build_command:
                print(f"  Build command: {build_command}")
            if output_dir and output_dir != "/":
                print(f"  Output directory: {output_dir}")

        elif cmd == "pages-deploy":
            # pages-deploy <project-name> [branch]
            project_name = sys.argv[2]
            branch = sys.argv[3] if len(sys.argv) > 3 else "main"
            result = cf.trigger_pages_deployment(project_name, branch)
            print(f"OK Deployment triggered: {project_name} (branch: {branch})")
            print(f"   ID: {result.get('id', '?')}")
            print(f"   Status: {result.get('latest_stage', {}).get('name', 'queued')}")

        elif cmd == "pages-dns":
            # pages-dns <domain> <project-name>
            domain = root_domain(sys.argv[2])
            project_name = sys.argv[3]
            removed = cf.point_to_pages(domain, project_name)
            pages_target = f"{project_name}.pages.dev"
            for r in removed:
                print(f"   Removed {r['type']} {r['name']} -> {r['content']}")
            print(f"OK DNS configured: {domain} -> {pages_target}")
            print(f"   Also configured: www.{domain} -> {pages_target}")

        elif cmd == "pages-domain":
            # pages-domain <project-name> <domain>
            project_name, root = sys.argv[2], root_domain(sys.argv[3])
            bad = 0
            for name in (root, f"www.{root}"):
                try:
                    cf.set_pages_custom_domain(project_name, name)
                except CloudflareAPIError as e:
                    if "already" not in str(e).lower():
                        raise
                info = cf.get_pages_domain(project_name, name)
                if info is None:
                    print(f"FAIL: {name} is not registered on {project_name}")
                    bad += 1
                else:
                    print(f"OK {name}: {info.get('status', '?')}")
            sys.exit(1 if bad else 0)

        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)

    except CloudflareAPIError as e:
        print(f"Cloudflare error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {describe_request_error(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
