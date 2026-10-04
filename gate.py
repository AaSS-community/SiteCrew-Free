"""
SiteCrew AaSS Kit gate: one command, no network, standard library only.

  python gate.py        exits 0 on GATE PASS, 1 on GATE FAIL (n)
"""
import contextlib
import io
import os
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

sys.dont_write_bytecode = True  # the gate must not leave .pyc files behind

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / ".claude" / "scripts"
SKIP_DIRS = {".git", "site", "my-old-site", "My-Vault", "__pycache__", ".venv", ".agent"}

# Words that must not ship. gate.py is excluded from this scan (it names them).
BANNED = ["admin:repo_hook", "No expiration", "paramiko", "ssh_binary",
          "heartbeat", "github.com/svsinc", "[DOMAIN_SLUG]"]

# sitecrew.ai is banned in every shipped .md/.py except the root README.md,
# where it is the deliberate credit (the credit, Al S012).
CREDIT_NAME = "sitecrew.ai"
# The old kit name and repo URL must not come back. sitecrew.ai is LIVE since Oct 4,
# 2026 (Al): the root README.md may link it in exactly one form, SITE_LINK_OK. Every
# other link form, and any link outside the README, stays RED.
SITE_LINK_OK = "](https://sitecrew.ai)"
_SITE = r"sitecrew\.ai(?![\w-])(?!\.[a-z])"  # not sitecrew.ai.example.com
BANNED_EVERYWHERE_RE = [
    ("old kit name", re.compile(r"\bsitecrew[ -]free\b", re.I)),
    ("link to sitecrew.ai", re.compile("|".join([
        r"//(?:[\w-]+\.)*" + _SITE,                      # https://, http://, // and any subdomain
        r"\b[\w-]+\." + _SITE,                           # www.sitecrew.ai, docs.sitecrew.ai
        r"\]\(\s*(?:[\w-]+\.)*" + _SITE,                 # markdown target ](sitecrew.ai...)
        r"\bsitecrew\.ai/"]), re.I)),                    # sitecrew.ai/path
]
AASS_EXPANSION = "Agent as Software Solution"
README_TITLE = "# SiteCrew AaSS Kit"
README_CREDIT = "This kit is possible because of SiteCrew.ai"
README_CREDIT_HEADING = "## Where it comes from"

BANNED_MD_ONLY = ["\u2014"]  # the em-dash character
# The upkeep word is "maintain" (Al, 2026-10-04): the agent builds and maintains;
# "keep" means holding on (keep renting, yours to keep). These old forms must not come back.
OLD_KEEP_RE = re.compile("|".join([
    r"\b(?:builds?|built|publish(?:es|ed)?|puts?)\b[^.\n]{0,60}?\b(?:then |and )(?:keeps|kept)\b"
    r"(?= (?:it|(?:a|the|your) (?:site|website)|software)\b)",
    r"\bkept by (?:your |an? |the )?(?:AI (?:coding )?|coding )?agent\b",
    r"\b(?:keep|keeps|kept|keeping)\s+(?:it|(?:a|the|your) (?:site|website)|software)\s+(?:working|right)\b",
    r"\b(?:the agent|it|then you) keeps?\b (?:it\b|the site)",
    r"\bcosts? to keep\b",
    r"\bkeeping (?:a site|it|software)(?: still)? (?:takes work|working|right)",
    r"\bcheap(?:er)?\. keeping (?:it )?(?:didn|did not)",
    r"\bmove the site, keep it\b",
    r"\bowning (?:software )?means keeping\b",
]), re.I)
# Claims the kit must not make (house copy laws); matched in .md files, case-insensitive.
BANNED_MD_PHRASES = ["no monthly fees", "20-30 minutes", "~$10/year", ".ca ", "CA$", "Canadian"]
# GUIDE.md and README.md are public pages: no private research file, no local path.
PUBLIC_DOCS = ("GUIDE.md", "README.md")
PUBLIC_BANNED = ["kit-research", "c:\\users", "c:/users", "/users/", "\\projects\\"]

failures = 0


def report(ok: bool, text: str) -> None:
    global failures
    if not ok:
        failures += 1
    print(f"{'PASS' if ok else 'FAIL'}  {text}")


def shipped(*suffixes: str):
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(suffixes):
                yield Path(dirpath) / name


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# 1. Every .py compiles (py_compile's check, without writing .pyc files)
def check_compile() -> None:
    bad = []
    for p in shipped(".py"):
        try:
            compile(p.read_bytes(), str(p), "exec")  # same check as py_compile, writes nothing
        except (SyntaxError, ValueError) as e:
            bad.append(f"{rel(p)}: {e}")
    report(not bad, "every .py compiles" + "".join(f"\n      {b}" for b in bad))


# 2. Every script runs its usage on a cp1252 pipe without a traceback
def check_usage() -> None:
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    for p in sorted(SCRIPTS.glob("*.py")):
        r = subprocess.run([sys.executable, str(p)], cwd=ROOT, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           stdin=subprocess.DEVNULL, timeout=60)
        out = (r.stdout + r.stderr).decode("cp1252", errors="replace")
        if "No module named" in out:
            report(False, f"{rel(p)} usage on cp1252 pipe\n"
                          "      install first: pip install -r .claude/scripts/requirements.txt")
        elif any(w in out for w in ("Traceback", "UnicodeEncodeError", "SyntaxError")):
            report(False, f"{rel(p)} usage on cp1252 pipe\n      {out.strip().splitlines()[-1]}")
        else:
            report(r.returncode in (0, 1, 2), f"{rel(p)} usage on cp1252 pipe (exit {r.returncode})")


# 3. Safety text checks over shipped .md and .py
def check_text() -> None:
    hits = []
    for p in shipped(".md", ".py"):
        if p.name == "gate.py" and p.parent == ROOT:
            continue
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        hits += [f"{rel(p)}: {w}" for w in BANNED if w.lower() in text]
        is_readme = p.parent == ROOT and p.name == "README.md"
        scan = text.replace(SITE_LINK_OK, "](allowed)") if is_readme else text
        hits += [f"{rel(p)}: {label}: {m.group(0)}" for label, rx in BANNED_EVERYWHERE_RE
                 for m in rx.finditer(scan)]
        if CREDIT_NAME in text and not (p.parent == ROOT and p.name == "README.md"):
            hits.append(f"{rel(p)}: {CREDIT_NAME} (allowed only in the root README.md credit)")
        if p.suffix == ".md":
            hits += [f"{rel(p)}: em-dash character" for w in BANNED_MD_ONLY if w in text]
            hits += [f"{rel(p)}: {w}" for w in BANNED_MD_PHRASES if w.lower() in text]
            if p.parent == ROOT and p.name in PUBLIC_DOCS:
                hits += [f"{rel(p)}: {w}" for w in PUBLIC_BANNED if w in text]
    report(not hits, "no banned text in .md/.py" + "".join(f"\n      {h}" for h in hits))


# 3b. The root README keeps its title and the credit to SiteCrew.ai
def check_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    first = text.splitlines()[0].strip() if text.strip() else ""
    why = "" if first == README_TITLE else f"\n      found: {first!r}"
    report(first == README_TITLE, f"README.md first line is exactly '{README_TITLE}'" + why)
    missing = [m for m in (README_CREDIT, README_CREDIT_HEADING) if m not in text]
    why = "" if not missing else ("\n      the credit to SiteCrew.ai must stay (Al, S012), and the sitecrew.ai website quotes it: change the site too; missing: "
                                  + ", ".join(repr(m) for m in missing))
    report(not missing, "README.md credits SiteCrew.ai" + why)


# 3b2. The upkeep word is "maintain", in every shipped .md (Al, 2026-10-04)
def check_upkeep_word() -> None:
    hits = []
    for p in shipped(".md"):
        # Whole document, whitespace squashed: a phrase wrapped across two lines still counts.
        text = re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="replace")).strip()
        hits += [f"{rel(p)}: {m.group(0)!r}" for m in OLD_KEEP_RE.finditer(text)]
    why = "" if not hits else ("\n      the agent MAINTAINS the site; 'keep' is only for holding on (keep renting, yours to keep). "
                               "The sitecrew.ai website quotes the README: change it too. Found:"
                               + "".join(f"\n      {h}" for h in hits))
    report(not hits, "the upkeep word is 'maintain', not 'keep' (Al, 2026-10-04)" + why)


# 3c. AaSS is expanded at first use in every shipped .md: "Agent as Software Solution"
# in the same or the next unit (a unit is a heading line, or a sentence ending . ? ! or a line).
# A heading is a name, not a use, so the first AaSS in running text is the one that counts.
def aass_units(text: str):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            yield line, True
        else:
            for sentence in re.split(r"(?<=[.?!])\s+", line):
                yield sentence, False


def check_aass() -> None:
    bad = []
    for p in shipped(".md"):
        pairs = list(aass_units(p.read_text(encoding="utf-8", errors="replace")))
        units = [u for u, _ in pairs]
        for i, (unit, heading) in enumerate(pairs):
            if heading or not re.search(r"\bAaSS\b", unit):
                continue
            if not any(AASS_EXPANSION in u for u in units[i:i + 2]):
                bad.append(f"{rel(p)}: first AaSS has no '{AASS_EXPANSION}' next to it: "
                           f"{unit[:80]!r}")
            break
    report(not bad, f"AaSS is expanded ('{AASS_EXPANSION}') at first use in every .md"
           + "".join(f"\n      {b}" for b in bad))


# 4. Scripts named in .md exist, and so do the commands named for them
def check_references() -> None:
    pattern = re.compile(r"python\s+(?:[\w./\\-]*[/\\])?([\w]+\.py)(?:\s+([a-z][a-z-]*))?")
    problems = []
    for md in shipped(".md"):
        for name, cmd in pattern.findall(md.read_text(encoding="utf-8", errors="replace")):
            target = ROOT / name if name == "gate.py" else SCRIPTS / name
            if not target.exists():
                problems.append(f"{rel(md)}: {name} does not exist")
            elif cmd and f'"{cmd}"' not in target.read_text(encoding="utf-8"):
                problems.append(f"{rel(md)}: {name} has no command '{cmd}'")
    report(not problems, "scripts and commands named in .md exist"
           + "".join(f"\n      {p}" for p in sorted(set(problems))))


# 6. Offline self-test of the safety logic (DNS and Cloudflare are stubbed, no network)
class _FakeResp:
    def __init__(self, body):
        self._body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self._body


class _FakeCF:
    def __init__(self, records):
        self.records = records

    def list_records(self, domain):
        return self.records


def _run_mail_check(cf_api, dns, records):
    """dns(name, type) -> DoH JSON body. Returns mail_check's exit code."""
    real_get = cf_api.requests.get

    def fake_get(url, params=None, **kw):
        return _FakeResp(dns(params["name"], params["type"]))

    cf_api.requests.get = fake_get
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return cf_api.mail_check(_FakeCF(records), "www.ex.com")
    finally:
        cf_api.requests.get = real_get


def check_selftest() -> None:
    sys.path.insert(0, str(SCRIPTS))
    try:
        import cf_api
    except ImportError:
        report(False, "offline self-test\n      install first: pip install -r .claude/scripts/requirements.txt")
        return

    def ans(name, rtype, data):
        return {"Status": 0, "Answer": [{"name": name + ".", "type": rtype, "data": data}]}

    def empty(name, rtype):
        return {"Status": 3}

    mx_rec = {"type": "MX", "name": "ex.com", "content": "mx.mail.com", "priority": 10}
    spf_rec = {"type": "TXT", "name": "ex.com", "content": "v=spf1 -all"}

    def dns_ok(name, rtype):
        if (name, rtype) == ("ex.com", "MX"):
            return ans(name, 15, "10 mx.mail.com.")
        if (name, rtype) == ("ex.com", "TXT"):
            return ans(name, 16, '"v=spf1 " "-all"')  # quoted chunks on one side only
        return empty(name, rtype)

    def dns_dkim_cname(name, rtype):
        if (name, rtype) == ("google._domainkey.ex.com", "CNAME"):
            return ans(name, 5, "google.dkim.example.net.")
        return empty(name, rtype)

    cases = [
        ("SERVFAIL fails closed", lambda n, t: {"Status": 2}, [mx_rec], 1),
        ("truncated answer fails closed", lambda n, t: {"Status": 0, "TC": True}, [mx_rec], 1),
        ("matching zone passes (quoted TXT chunks decoded)", dns_ok, [mx_rec, spf_rec], 0),
        ("missing record fails", dns_ok, [mx_rec], 1),
        ("proxied DKIM CNAME fails", dns_dkim_cname,
         [{"type": "CNAME", "name": "google._domainkey.ex.com", "content": "google.dkim.example.net",
           "proxied": True}], 1),
        ("DNS-only DKIM CNAME passes", dns_dkim_cname,
         [{"type": "CNAME", "name": "google._domainkey.ex.com", "content": "google.dkim.example.net",
           "proxied": False}], 0),
    ]
    for label, dns, records, want in cases:
        got = _run_mail_check(cf_api, dns, records)
        report(got == want, f"mail_check: {label} (exit {got}, want {want})")

    got = (cf_api.root_domain("willow.com"), cf_api.root_domain("www.willow.com"))
    report(got == ("willow.com", "willow.com"), f"www. handling: {got[0]}, {got[1]}")

    hosts = (cf_api.pages_host({"name": "shop", "subdomain": "shop.pages.dev"}),
             cf_api.pages_host({"name": "shop"}))
    report(hosts == ("shop.pages.dev", "shop.pages.dev"),
           f"pages_host: never doubles .pages.dev ({hosts[0]}, {hosts[1]})")

    import tempfile
    head = 'name = "shop-com"\npages_build_output_dir = "./dist"\n'
    d1 = '[[d1_databases]]\nbinding = "DB"\ndatabase_id = "local-placeholder-replace-before-deploy"\n'
    wcases = [
        ("no Wrangler file: silent", None, 0, False),
        ("file without pages_build_output_dir: silent", 'name = "x"\n', 0, False),
        ("output dir set: notes, goes on", head, 1, False),
        ("placeholder D1 id: stops", head + d1, 2, True),
        ("commented-out placeholder: goes on", head + "".join("# " + l + "\n" for l in d1.splitlines()), 1, False),
    ]
    for label, body, want_lines, want_stop in wcases:
        with tempfile.TemporaryDirectory() as tmp:
            if body is not None:
                Path(tmp, "wrangler.toml").write_text(body, encoding="utf-8")
            lines, stop = cf_api.wrangler_notes(Path(tmp), "shop-com")
        report(len(lines) == want_lines and stop == want_stop,
               f"wrangler_notes: {label} ({len(lines)} lines, stop={stop})")


# 7. Anything that changes the outside world refuses without --owner-approved, before any network call
def check_refusals() -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GITHUB_", "CF_", "NAMECHEAP_", "SPACESHIP_"))}
    cases = [("namecheap_to_cf.py", ["migrate", "example.com"]),
             ("spaceship_to_cf.py", ["migrate", "example.com"]),
             ("github_api.py", ["push", "main"]),
             ("cf_api.py", ["pages-dns", "example.com", "proj"])]
    for name, args in cases:
        r = subprocess.run([sys.executable, str(SCRIPTS / name), *args], cwd=ROOT, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, timeout=60)
        out = (r.stdout + r.stderr).decode("utf-8", errors="replace")
        ok = r.returncode != 0 and "Refusing" in out and "Traceback" not in out
        report(ok, f"{name} {args[0]} refuses without --owner-approved")


# 8. The knowledge files exist and CLAUDE.md stays a thin pointer to AGENTS.md
def check_knowledge() -> None:
    names = ("AGENTS.md", "GUIDE.md", "README.md", "CLAUDE.md")
    missing = [n for n in names if not (ROOT / n).exists()]
    report(not missing, "AGENTS.md, GUIDE.md, README.md, CLAUDE.md exist"
           + "".join(f"\n      missing: {m}" for m in missing))
    claude = ROOT / "CLAUDE.md"
    ok = claude.exists() and "@AGENTS.md" in claude.read_text(encoding="utf-8")
    report(ok, "CLAUDE.md contains @AGENTS.md")


# 9. In the setup command, the secret scan comes BEFORE the first git commit
def check_scan_order() -> None:
    path = ROOT / ".claude" / "commands" / "init-client-free.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    heading = re.search(r"^### Secret scan", text, re.MULTILINE)  # the step itself, not the Step 5 title
    commit = text.find("git commit")
    ok = bool(heading) and commit != -1 and heading.start() < commit
    why = "" if ok else "\n      the 'Secret scan' heading must appear before the first 'git commit'"
    report(ok, "init-client-free.md: secret scan comes before the first git commit" + why)


# 5. No .env tracked or lying around outside .env.example
def _is_env(name: str) -> bool:
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def check_env() -> None:
    present = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__"}]
        present += [rel(Path(dirpath) / f) for f in filenames if _is_env(f)]
    tracked = []
    if (ROOT / ".git").exists():
        try:
            out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                                 text=True, timeout=30).stdout
            tracked = [f for f in out.splitlines() if _is_env(Path(f).name)]
        except (OSError, subprocess.SubprocessError):
            pass
    report(not tracked, "no .env file tracked" + "".join(f"\n      tracked: {t}" for t in tracked))
    for p in present:
        print(f"WARN  {p} is present (fine locally, never commit it; not deleted)")


check_compile()
check_usage()
check_text()
check_readme()
check_upkeep_word()
check_aass()
check_references()
check_env()
check_selftest()
check_refusals()
check_knowledge()
check_scan_order()

print("GATE PASS" if not failures else f"GATE FAIL ({failures})")
sys.exit(0 if not failures else 1)
