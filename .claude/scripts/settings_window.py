"""
The settings window for SiteCrew AaSS Kit: the owner pastes each key into a window, never into the
chat and never into a file by hand.

One row per key: what it is for, where to get it (the clicks), an "Open the page" button, a box that
takes an ordinary paste, and Save. Save writes the key into .claude/scripts/.env on this computer, the
file cf_api.py and github_api.py read, and changes nothing else in that file. A saved key shows as a
row of dots, never itself. Nothing in this script prints a key's value.

Standard library only (Tk). Python from python.org includes Tk on Windows and on a Mac. On Linux
install python3-tk; with Homebrew's Python on a Mac, brew install python-tk.

Usage:
  python settings_window.py open                    open the window on the owner's screen
  python settings_window.py open --registrar namecheap
                                                    also ask for a registrar's keys (namecheap, spaceship)
  python settings_window.py list                    every key: saved, needed or optional; exit 0 when
                                                    every needed key is saved. Shows the values of the
                                                    settings that are not secret, never a key
  python settings_window.py build                   build the window and close it again (a check)
"""
from __future__ import annotations

import argparse
import contextlib
import os
import re
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS = Path(__file__).resolve().parent
KEY_FILE = SCRIPTS / ".env"
TITLE = "SiteCrew AaSS Kit: settings"
NAME_SHAPE = re.compile(r"^[A-Z][A-Z0-9_]*$")
# What a saved key's box holds: a row of dots that says "something is saved here" (an empty box next to
# "saved" reads as a failure). Never the key itself, and nothing anyone could type or paste.
SAVED_MARK = "\ue000" * 12  # a private-use character: shown as dots in a masked box
GITHUB_CLASSIC = ("ghp_", "gho_", "ghu_", "ghs_", "ghr_")
REPO_RX = re.compile(r"^(?:(?:https?://)?(?:www\.)?github\.com/|git@github\.com:)?"
                     r"([A-Za-z0-9-]+)/([A-Za-z0-9._-]+?)(?:\.git)?/?$")
INTRO = ("For each key: click Open the page, follow the steps under the key, copy it, paste it into its box "
         "(Ctrl+V, Cmd+V on a Mac, or right-click and Paste), then click Save. Your keys are saved in one file "
         "on this computer (.claude/scripts/.env) that is never published. They never go into the chat, and "
         "a saved key shows as dots, never itself.")
NO_TK = ("This Python has no Tk, so no window. On Linux install your system's python3-tk package (Ubuntu and "
         "Debian: sudo apt install python3-tk); with Homebrew's Python on a Mac: brew install python-tk. Then "
         "run this again. Without a window: copy .claude/scripts/.env.example to .claude/scripts/.env and "
         "paste each key after its name in a text editor.")


# --- what the window asks for ---------------------------------------------------

CLOUDFLARE = "Cloudflare: your hosting and your domain"
GITHUB = "GitHub: where your site's files live"

CORE = [
    {"name": "CF_API_TOKEN", "group": CLOUDFLARE, "label": "Cloudflare API token",
     "for": "Lets your agent set up your site's hosting (Cloudflare Pages) and your domain's DNS records, "
            "for your one domain only.",
     "where": ("Cloudflare, signed in: Create Token, then Create Custom Token (at the bottom). Name it "
               "SiteCrew. Add the three permissions below. Zone Resources: Include, Specific zone, your "
               "domain. Then Continue to summary, Create Token, and copy the token (Cloudflare shows it "
               "only once)."),
     "permissions": "Zone / Zone / Read, Zone / DNS / Edit, Account / Cloudflare Pages / Edit.",
     "link": "https://dash.cloudflare.com/profile/api-tokens"},
    {"name": "CF_ACCOUNT_ID", "group": CLOUDFLARE, "label": "Cloudflare Account ID", "plain": True,
     "for": "Which Cloudflare account your site lives in. Not a secret.",
     "where": ("Cloudflare: open your domain, then Overview, and find the API section on the right. Copy the "
               "Account ID (not the Zone ID)."),
     "link": "https://dash.cloudflare.com/"},
    {"name": "GITHUB_REPO", "group": GITHUB, "label": "Your site's GitHub repository", "plain": True,
     "for": "The one empty repository you made for your site. Paste its address; the window keeps the "
            "owner/name part.",
     "where": ("GitHub, signed in: name the repository (for example mybusiness-site), add no README, "
               ".gitignore or license, click Create repository, then copy the address from your browser."),
     "link": "https://github.com/new"},
    {"name": "GITHUB_TOKEN", "group": GITHUB, "label": "GitHub token (for that one repository)",
     "for": "Lets your agent publish your site's files to that one repository, only after you say "
            "\"yes, publish\". It cannot change anything else.",
     "where": ("GitHub, signed in: Token name SiteCrew, Expiration 90 days. Resource owner: the account that "
               "owns the repository. Repository access: Only select repositories, then your one repository. "
               "Add the permission below, then Generate token, and copy it."),
     "permissions": ("Add permissions, Contents, Access: Read and write (Metadata, read-only, is added and "
                     "marked Required). Nothing else."),
     "link": "https://github.com/settings/personal-access-tokens/new"},
]

# Only when the agent moves the nameservers through the registrar's API (open --registrar ...), or when
# one of these is already saved.
REGISTRARS = {
    "namecheap": [
        {"name": "NAMECHEAP_API_USER", "label": "Namecheap API user", "plain": True,
         "for": "Your Namecheap API user name (usually the same as your login)."},
        {"name": "NAMECHEAP_USERNAME", "label": "Namecheap user name", "plain": True,
         "for": "Your Namecheap login user name (often the same as the API user)."},
        {"name": "NAMECHEAP_API_KEY", "label": "Namecheap API key",
         "for": "Lets your agent change your domain's nameservers at Namecheap, only after your yes.",
         "where": "Namecheap, signed in: Account, Profile, API Access. Copy the API key."},
        {"name": "NAMECHEAP_CLIENT_IP", "label": "Your computer's IP address", "plain": True,
         "for": "Namecheap answers only an IP address you added to the list on the same API Access page."},
    ],
    "spaceship": [
        {"name": "SPACESHIP_API_KEY", "label": "Spaceship API key",
         "for": "Lets your agent change your domain's nameservers at Spaceship, only after your yes.",
         "where": "Spaceship, signed in: your dashboard, API. Copy the API key."},
        {"name": "SPACESHIP_API_SECRET", "label": "Spaceship API secret",
         "for": "The secret that goes with the API key, from the same page."},
    ],
}
for _name, _fields in REGISTRARS.items():
    for _f in _fields:
        _f["group"] = f"{_name.capitalize()}: only if your agent moves your nameservers there for you"
        _f["optional"] = True

OTHER = "Other keys in this file"
OTHER_FOR = {"CF_ZONE_ID": "Optional: your domain's Zone ID. It only saves a look-up: cf_api.py finds the zone "
                           "by your domain's name."}
OTHER_PLAIN = {"CF_ZONE_ID"}


def _known() -> dict[str, dict]:
    return {f["name"]: f for f in CORE + [f for fs in REGISTRARS.values() for f in fs]}


# --- each key's own check -------------------------------------------------------

def repo_name(value: str) -> str:
    """owner/name from what GitHub shows: the address in the browser, the clone address, or owner/name."""
    m = REPO_RX.match(value.strip())
    if not m or m.group(2) in (".", ".."):
        raise ValueError("paste your repository's address from GitHub, like https://github.com/jane/janes-bakery-site")
    return f"{m.group(1)}/{m.group(2)}"


def clean(key: str, value: str) -> str:
    """The value to save, or ValueError with a sentence the owner can act on."""
    value = value.strip()
    if not value:
        raise ValueError("the box is empty: paste the key first")
    if SAVED_MARK[0] in value:
        raise ValueError("click into the box so it is empty, then paste")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("what arrived is not a key (it holds control characters: the paste did not arrive). "
                         "Copy it again")
    if key == "GITHUB_REPO":
        return repo_name(value)
    if re.search(r"\s", value):
        raise ValueError("a key has no spaces in it: copy it again")
    if key == "CF_ACCOUNT_ID":
        if not re.fullmatch(r"[0-9a-fA-F]{32}", value):
            raise ValueError("an Account ID is 32 letters and digits (0-9 and a-f). Copy the Account ID, "
                             "not the Zone ID or the token")
        return value.lower()
    if value.startswith(("http://", "https://", "github.com/")):
        raise ValueError("this is a web address, not the key: copy the key the page showed you")
    if key == "CF_API_TOKEN" and value.startswith(GITHUB_CLASSIC + ("github_pat_",)):
        raise ValueError("this is a GitHub token: paste it into the GitHub token's box")
    if key == "GITHUB_TOKEN" and value.startswith(GITHUB_CLASSIC):
        raise ValueError("this is a classic token, which can reach every repository you have. Make a "
                         "fine-grained token for your one repository instead (Open the page)")
    return value


# --- the key file ---------------------------------------------------------------

def _lines(path: Path) -> tuple[list[str], str]:
    if not path.is_file():
        return [], "\n"
    raw = path.read_bytes().decode("utf-8", errors="replace")
    return raw.splitlines(), ("\r\n" if "\r\n" in raw else "\n")


def _parse(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip().removeprefix("export ").strip()
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return key, value


def held(path: Path | None = None) -> dict[str, str]:
    """Every key in the file with its value: for this process only, never printed."""
    return dict(p for p in (_parse(line) for line in _lines(path or KEY_FILE)[0]) if p)


def save(key: str, value: str, path: Path | None = None) -> str:
    """Put one key into the file, in its own line's place; every other line stays as it was. Returns what was
    saved (a repository address becomes owner/name)."""
    path = path or KEY_FILE
    if not NAME_SHAPE.match(key):
        raise ValueError("a key name is capital letters, digits and _")
    value = clean(key, value)
    lines, newline = _lines(path)
    out, done = [], False
    for line in lines:
        parsed = _parse(line)
        if parsed and parsed[0] == key:
            if not done:
                out.append(f"{key}={value}")
            done = True
        else:
            out.append(line)
    if not done:
        if out and out[-1].strip():
            out.append("")
        out.append(f"{key}={value}")
    tmp = path.with_name(path.name + ".saving")
    tmp.write_bytes((newline.join(out) + newline).encode("utf-8"))
    if os.name != "nt":
        os.chmod(tmp, 0o600)  # readable by the owner's account only
    os.replace(tmp, path)
    return value


def fields(registrars: tuple[str, ...] = (), path: Path | None = None) -> list[dict]:
    values = held(path)
    wanted = list(CORE)
    for name, group in REGISTRARS.items():
        if name in registrars or any(values.get(f["name"]) for f in group):
            wanted += group
    out = []
    for spec in wanted:
        value = values.get(spec["name"], "")
        f = dict(spec, held=bool(value))
        if value:
            try:
                clean(spec["name"], value)
            except ValueError:
                f["held"], f["bad"] = False, True
        if f.get("plain") and value:
            f["current"] = value
        out.append(f)
    for name in sorted(values):
        if name in _known() or not values[name]:
            continue
        plain = name in OTHER_PLAIN
        out.append({"name": name, "group": OTHER, "held": True, "plain": plain, "optional": True,
                    "current": values[name] if plain else "",
                    "for": OTHER_FOR.get(name, "Not described here: ask your agent what it is for.")})
    return out


# --- the window -----------------------------------------------------------------

def no_window_reason() -> str:
    try:
        import tkinter  # noqa: F401
    except ImportError:
        return NO_TK
    if sys.platform not in ("win32", "darwin") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return "This computer has no screen here, so no window: open the kit on the computer the owner sits at."
    return ""


def show(rows: list[dict], build_only: bool = False, path: Path | None = None):
    """The window itself (blocking). build_only=True returns the Tk root without running it (the gate)."""
    import tkinter as tk
    from tkinter import messagebox, ttk
    if os.name == "nt":
        with contextlib.suppress(Exception):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # crisp text on high-DPI screens

    win = tk.Tk()
    win.title(TITLE)
    win.geometry("860x720")
    win.minsize(640, 420)
    style = ttk.Style(win)
    with contextlib.suppress(tk.TclError):
        style.theme_use({"nt": "vista"}.get(os.name, "aqua" if sys.platform == "darwin" else "clam"))
    style.configure("Title.TLabel", font=("Segoe UI", 15, "bold"))
    style.configure("Group.TLabel", font=("Segoe UI", 12, "bold"), foreground="#2b4c7e")
    style.configure("Key.TLabel", font=("Segoe UI", 11, "bold"))
    style.configure("Held.TLabel", foreground="#1a7f37")
    style.configure("Missing.TLabel", foreground="#b35900")
    style.configure("Name.TLabel", foreground="#777777", font=("Consolas", 9))

    head = ttk.Frame(win, padding=(16, 12))
    head.pack(fill="x")
    ttk.Label(head, text="Your website's keys", style="Title.TLabel").pack(anchor="w")
    ttk.Label(head, wraplength=800, justify="left", text=INTRO).pack(anchor="w", pady=(4, 0))

    body = ttk.Frame(win)
    body.pack(fill="both", expand=True)
    canvas = tk.Canvas(body, highlightthickness=0)
    bar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas, padding=(16, 4))
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=bar.set)
    canvas.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    if sys.platform == "darwin":
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-e.delta, "units"))
    else:
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def clear_mark(entry):
        if entry.get() == SAVED_MARK:
            entry.delete(0, "end")

    def paste_menu(entry):
        menu = tk.Menu(entry, tearoff=0)
        menu.add_command(label="Paste", command=lambda: (clear_mark(entry), entry.focus_set(),
                                                         entry.event_generate("<<Paste>>")))
        for button in ("<Button-3>",) + (("<Button-2>", "<Control-Button-1>") if sys.platform == "darwin" else ()):
            entry.bind(button, lambda e: menu.tk_popup(e.x_root, e.y_root))

    group = None
    for f in rows:
        if f.get("group") and f["group"] != group:
            group = f["group"]
            ttk.Label(inner, text=group, style="Group.TLabel").pack(anchor="w", pady=(14, 0))
        box = ttk.Frame(inner, padding=(0, 10))
        box.pack(fill="x")
        top = ttk.Frame(box)
        top.pack(fill="x")
        ttk.Label(top, text=f.get("label") or f["name"], style="Key.TLabel").pack(side="left")
        state = ttk.Label(top, text="saved" if f["held"] else ("needed: what was saved is not a key" if f.get("bad")
                                                              else "optional" if f.get("optional") else "needed"),
                          style="Held.TLabel" if f["held"] else "Missing.TLabel")
        state.pack(side="left", padx=10)
        if f.get("label"):
            ttk.Label(top, text=f["name"], style="Name.TLabel").pack(side="right")
        if f.get("for"):
            ttk.Label(box, text=f["for"], wraplength=780, justify="left").pack(anchor="w")
        if f.get("where"):
            ttk.Label(box, text="Where: " + f["where"], wraplength=780, justify="left").pack(anchor="w", pady=(2, 0))
        if f.get("permissions"):
            ttk.Label(box, text="Permissions: " + f["permissions"], wraplength=780,
                      justify="left").pack(anchor="w", pady=(2, 0))
        row = ttk.Frame(box)
        row.pack(fill="x", pady=(6, 0))
        if f.get("link"):
            ttk.Button(row, text="Open the page", command=lambda u=f["link"]: webbrowser.open(u)).pack(side="left")
        plain = bool(f.get("plain"))
        # A setting that is not secret shows what it holds; a saved key shows as dots, cleared by a click so
        # the paste lands in an empty box.
        entry = ttk.Entry(row, show="" if plain else "•", width=56)
        saved = {"now": bool(f["held"])}
        if plain and f.get("current"):
            entry.insert(0, f["current"])
        elif not plain and f["held"]:
            entry.insert(0, SAVED_MARK)
        if not plain:
            entry.bind("<FocusIn>", lambda e, ent=entry: clear_mark(ent))
            entry.bind("<FocusOut>", lambda e, ent=entry, s=saved: ent.insert(0, SAVED_MARK)
                       if s["now"] and not ent.get() else None)
        paste_menu(entry)
        entry.pack(side="left", fill="x", expand=True, padx=8)
        button = ttk.Button(row, text="Replace" if f["held"] else "Save")

        def do_save(key=f["name"], label=f.get("label") or f["name"], ent=entry, lab=state, s=saved,
                    masked=not plain, btn=button):
            value = ent.get().strip()
            if value == SAVED_MARK:
                messagebox.showinfo(TITLE, f"{label} is saved. To replace it, paste the new one into its box "
                                    "first, then click Replace.", parent=win)
                return
            try:
                kept = save(key, value, path)
            except (ValueError, OSError) as e:
                messagebox.showerror(TITLE, f"{label}: {e}", parent=win)
                return
            s["now"] = True
            ent.delete(0, "end")
            ent.insert(0, SAVED_MARK if masked else kept)
            lab.configure(text="saved", style="Held.TLabel")
            btn.configure(text="Replace")
        button.configure(command=do_save)
        button.pack(side="left")
        ttk.Separator(inner).pack(fill="x")

    foot = ttk.Frame(win, padding=(16, 10))
    foot.pack(fill="x")
    ttk.Label(foot, text="When every key says saved, close this window and tell your agent. It checks each key."
              ).pack(side="left")
    ttk.Button(foot, text="Close", command=win.destroy).pack(side="right")

    win.lift()
    win.attributes("-topmost", True)
    win.after(600, lambda: win.attributes("-topmost", False))
    win.focus_force()
    if build_only:
        return win
    win.mainloop()
    return None


# --- the commands ---------------------------------------------------------------

def open_on_screen(registrars: list[str]) -> int:
    """Start the window as its own process with no console, so it outlives the agent's command."""
    problem = no_window_reason()
    if problem:
        print(problem)
        return 1
    args = [str(Path(__file__).resolve()), "here"] + [a for r in registrars for a in ("--registrar", r)]
    quiet = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        gui = Path(sys.executable).with_name("pythonw.exe")
        proc = subprocess.Popen([str(gui if gui.is_file() else sys.executable), *args], cwd=str(SCRIPTS),
                                creationflags=0x08000000 | 0x00000200, **quiet)  # no console, own group
    else:
        proc = subprocess.Popen([sys.executable, *args], cwd=str(SCRIPTS), start_new_session=True, **quiet)
    time.sleep(3)
    if proc.poll() is not None:
        print(f"The window closed at once (exit {proc.returncode}). To see why: "
              "python .claude/scripts/settings_window.py build")
        return 1
    print("The settings window is open on the owner's screen. Ask them to paste each key and click Save, "
          "then close it. Then check: python .claude/scripts/settings_window.py list")
    return 0


def show_list(registrars: list[str]) -> int:
    rows = fields(tuple(registrars))
    group = None
    for f in rows:
        if f["group"] != group:
            group = f["group"]
            print(f"\n{group}")
        state = "saved" if f["held"] else "BAD PASTE" if f.get("bad") else "optional" if f.get("optional") else "NEEDED"
        shown = f"  {f['current']}" if f.get("plain") and f.get("current") else ""
        print(f"  {state:9} {f['name']}{shown}")
    missing = [f["name"] for f in rows if not f["held"] and not f.get("optional")]
    bad = [f["name"] for f in rows if f.get("bad")]
    print()
    if missing:
        print(f"Still needed: {', '.join(missing)}. Open the window: python .claude/scripts/settings_window.py open")
        return 1
    if bad:
        print(f"Not a key: {', '.join(bad)}. Open the window and paste it again.")
        return 1
    print("Every needed key is saved. Check them: python .claude/scripts/cf_api.py zones, "
          "then python .claude/scripts/github_api.py check")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="The settings window: the owner's keys, pasted into a window, "
                                            "saved in .claude/scripts/.env")
    sub = p.add_subparsers(dest="command")
    for name, text in (("open", "open the window on the owner's screen"),
                       ("list", "every key and its state, never a key's value"),
                       ("build", "build the window and close it again (a check)"),
                       ("here", "show the window in this process")):
        cmd = sub.add_parser(name, help=text)
        cmd.add_argument("--registrar", action="append", default=[], choices=sorted(REGISTRARS),
                         help="also ask for this registrar's keys")
    args = p.parse_args(argv)
    if args.command is None:
        print(__doc__.strip())
        return 0
    if args.command == "open":
        return open_on_screen(args.registrar)
    if args.command == "list":
        return show_list(args.registrar)
    problem = no_window_reason()
    if problem:
        print(problem)
        return 1
    if args.command == "build":
        win = show(fields(tuple(args.registrar)), build_only=True)
        win.update()
        win.destroy()
        print(f"The window builds: {len(fields(tuple(args.registrar)))} keys.")
        return 0
    show(fields(tuple(args.registrar)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
