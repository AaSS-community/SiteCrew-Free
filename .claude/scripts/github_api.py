"""
GitHub helper for SiteCrew Free (least access).

The owner creates ONE empty repository and ONE fine-grained token for that
repository only (Contents: Read and write, expiry 90 days). Nothing wider.

Required .env vars (in .claude/scripts/.env, pasted by the owner, never in chat):
  GITHUB_TOKEN   Fine-grained token for the one repository
                 Create at: https://github.com/settings/personal-access-tokens/new
  GITHUB_REPO    The repository as owner/name, e.g. jane/janes-bakery-site

Usage:
  python github_api.py check
  python github_api.py push [branch] --owner-approved
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path

import requests

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://api.github.com"
SITE_DIR = Path(__file__).resolve().parent.parent.parent / "site"


# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

def _load_env() -> None:
    """Load .env from .claude/scripts/ (or the project root), first one found."""
    script_dir = Path(__file__).parent
    for candidate in [script_dir / ".env", script_dir.parent.parent / ".env"]:
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
            return


def _config() -> tuple[str, str]:
    _load_env()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repo = os.getenv("GITHUB_REPO", "").strip()
    if not token or repo.count("/") != 1:
        print(
            "GITHUB_TOKEN and GITHUB_REPO (owner/name) must be set in "
            ".claude/scripts/.env.\nSee .claude/scripts/.env.example.",
            file=sys.stderr,
        )
        sys.exit(1)
    return token, repo


def _session(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return s


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check() -> int:
    """Verify GITHUB_REPO is reachable with push access, then remind the owner what to confirm."""
    token, repo = _config()
    s = _session(token)

    r = s.get(f"{BASE}/repos/{repo}", timeout=30)
    if r.status_code != 200:
        print(f"FAIL: cannot reach {repo} with this token (HTTP {r.status_code}).")
        print("Check GITHUB_REPO spelling and that the token was made for this repository.")
        return 1
    info = r.json()
    can_push = bool(info.get("permissions", {}).get("push"))
    print(f"Repository: {info['full_name']} ({'private' if info['private'] else 'public'})")
    print(f"Push access: {'yes' if can_push else 'NO'}")
    if not can_push:
        print("FAIL: the token cannot write to this repository (needs Contents: Read and write).")
        return 1
    print("OK: the token reaches this repository with push access.")
    print()
    print("Please confirm in GitHub (Settings > Developer settings > Personal access tokens > Fine-grained tokens):")
    print("  1. Repository access: only this one repository is selected.")
    print("  2. Permissions: Contents is Read and write, nothing else needed.")
    print("  3. The token has an expiry date (90 days).")
    return 0


def cmd_push(branch: str) -> int:
    """Push site/ to GITHUB_REPO. Only after the owner said 'yes, publish'."""
    token, repo = _config()
    if not (SITE_DIR / ".git").exists():
        print("site/ is not a git repository yet. Run git init -b main inside site/ first.", file=sys.stderr)
        return 1
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    url = f"https://github.com/{repo}.git"
    subprocess.run(["git", "remote", "remove", "origin"], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", url], cwd=SITE_DIR, check=True)
    # The auth header travels in this child process's environment only, never in its arguments.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_TRACE") and k not in ("GIT_CURL_VERBOSE", "GIT_CONFIG_COUNT")}
    env.update({
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": "",
        "GIT_CONFIG_KEY_1": "http.https://github.com/.extraheader",
        "GIT_CONFIG_VALUE_1": f"AUTHORIZATION: basic {basic}",
        "GIT_TERMINAL_PROMPT": "0",
    })
    result = subprocess.run(["git", "push", "-u", "origin", branch],
                            cwd=SITE_DIR, capture_output=True, text=True, env=env)
    out = (result.stdout + result.stderr).replace(token, "***").replace(basic, "***")
    print(out.strip())
    return result.returncode


def _cli() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    try:
        if cmd == "check":
            sys.exit(cmd_check())
        elif cmd == "push":
            args = [a for a in sys.argv[2:] if not a.startswith("--")]
            if "--owner-approved" not in sys.argv:
                print("Refusing to push: the owner must say 'yes, publish' first, then pass --owner-approved.",
                      file=sys.stderr)
                sys.exit(1)
            sys.exit(cmd_push(args[0] if args else "main"))
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    except requests.RequestException as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        print(f"Network error: {type(e).__name__}" + (f" (HTTP {status})" if status else ""), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
