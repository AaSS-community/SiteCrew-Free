---
description: Free SiteCrew setup: a website on Cloudflare Pages through GitHub, for a site you move or a new site. Guides the owner step by step.
---

# /init-client-free: SiteCrew AaSS Kit Setup

Guides the owner from a fresh install to a live website on Cloudflare Pages. It follows AGENTS.md
(the four safety rules) and GUIDE.md (the owner's version, with receipts). Read both first.

The order the owner lives, in short: options, build in `site/`, secret scan, first publish on
"yes, publish", Pages checked on `*.pages.dev`, mail-check, DNS conflicts on yes, nameservers, both
names verified, email tested both ways, and only then a talk about cancelling the old service.

Never state a price or a duration you cannot back. Use GUIDE.md's receipts or a page you just read,
and say where it came from. For anything slow (builds, DNS, certificates), say "watch the status in
Cloudflare" and check it, instead of promising a time.

---

## Before Starting

```
Glob: .agent/free-setup-progress.md
```

**If it exists and shows COMPLETE:**
> "This workspace is already set up for [client name]. Your site is at [domain].
> What would you like to change or add?"
> Stop here (changes follow AGENTS.md: show what changes, wait for "yes, publish").

**If it exists and shows IN PROGRESS:** read it, tell the owner "We started setup before, resuming
from Step [N]: [step name]", and continue from there.

**If neither exists:** fresh install. Proceed.

---

## STEP 0: Welcome

> "Welcome to the SiteCrew AaSS Kit (AaSS means Agent as Software Solution). I'll walk you through getting your website onto Cloudflare Pages,
> one step at a time. Hosting there has a free tier. Your domain is a yearly cost, and the AI
> plan I run on may cost something too; GUIDE.md chapter 0 has the numbers and where they come from.
>
> Some steps need a few clicks in your browser. I'll tell you exactly what to do each time.
> Nothing is published until you say "yes, publish".
>
> What's your name?"

Wait for the name. Use it from now on.

---

## STEP 1: Quick Interview

Ask **one at a time**, waiting for each answer.

1. "Do you have a website now that you want to move (road 1), or do you want a new site, or one more site (road 2)?"
   Save `ROAD` as `move` or `fresh`. (One site per folder: a second site means a second copy of this kit.)
   A site the owner already built that isn't online yet: its files go in `site/`, either road works.
2. "What's the name of your business or project?"
3. "What do you do, and who is it for? (2-3 sentences)"
4. "What's the main goal of the website? (calls or emails, bookings, showing your work, selling something, other)"
5. "What's the tone of your brand? (for example professional, friendly, bold, minimal)"
6. "Do you already have a domain name? (like mybusiness.com)"
7. Road 1 only: "Where does the site live today (if it's online), and where is the domain registered?" Remind them:
   a domain that came with a builder may need an unlock and an authorization code to move
   (GUIDE.md chapter 1, Warning 1), and transfers can have a waiting period.

Save the answers.

---

## STEP 2: Cloudflare account, domain and token

### No domain yet

> "Cloudflare Registrar sells domains at cost, with no markup (Cloudflare's own statement:
> https://developers.cloudflare.com/registrar/faq/). Current prices are at https://pricing.registrar.cloudflare.com/ .
>
> 1. Sign up for a free Cloudflare account at https://dash.cloudflare.com if you don't have one
> 2. Search for the domain you want and buy it
>
> Tell me the domain you bought."

It is then already on Cloudflare. Go to "Cloudflare API Token" below.

### Domain you already have

Ask: "Is it already on Cloudflare? (Its nameservers say something like `aria.ns.cloudflare.com`.)"

**Yes:** go to "Cloudflare API Token" below.

**No:**

> "I need the domain added to Cloudflare first. **Do not change your nameservers yet.**
> 1. Create a free account at https://dash.cloudflare.com if you don't have one
> 2. Click 'Add a Site', type your domain, choose the Free plan, and let Cloudflare scan your DNS records
> 3. Stop at the screen that shows two Cloudflare nameservers. Tell me when you're there."

The nameservers move later, in Step 7, after the site works and the mail records are checked.

### Cloudflare API Token

Keys go through the settings window, never the chat and never a file opened by hand. Open it on the
owner's screen first:

```bash
python .claude/scripts/settings_window.py open
```

It shows one box per key, with the clicks for each, an **Open the page** button and **Save**, and saves
into `.claude/scripts/.env`, the file the scripts read. If it says it cannot open a window (no Tk, or
no screen), tell the owner what it printed: it names the package to install, and the editor way as
the last resort.

> "Now I need an API token so I can set up your hosting. **You paste it into the settings window I
> just opened (Your website's keys); never paste it here in the chat.**
>
> 1. Go to: https://dash.cloudflare.com/profile/api-tokens (or click **Open the page** next to the token's box)
> 2. 'Create Token', then 'Create Custom Token' (at the bottom). Name it 'SiteCrew'
> 3. Permissions, add these three:
>    - Zone → Zone → Read
>    - Zone → DNS → Edit
>    - Account → Cloudflare Pages → Edit
> 4. Zone Resources: 'Include → Specific zone → [your domain]' (limits both Zone permissions to your domain)
> 5. 'Continue to summary' → 'Create Token' and copy the token (you only see it once)
> 6. In the settings window, paste it into the **Cloudflare API token** box and click **Save**
>
> Tell me when it says saved. (Don't tell me the token.)"

Then the Account ID (not secret):

> "Your Cloudflare Account ID: open your domain in the dashboard, then Overview, and find the **API**
> section on the right. Copy the **Account ID** (not the Zone ID), paste it into the window's
> **Cloudflare Account ID** box, and click **Save**."

If the owner closed the window, open it again with the same command.

Never ask for, echo or print a token. Verify:

```bash
python .claude/scripts/cf_api.py zones
```

It should list their domain. If it errors, help fix the token permissions before going on.

---

## STEP 3: GitHub (one repository, least access)

Ask: "Do you have a GitHub account?" If not: "GitHub is where your site's files live. It's free. Sign up at https://github.com and come back."

> "Please create ONE empty repository for your website:
> 1. Go to https://github.com/new
> 2. Name it (for example `mybusiness-site`), leave it empty (no README, .gitignore or license)
> 3. Click 'Create repository', copy the address from your browser, paste it into the settings
>    window's **Your site's GitHub repository** box, and click **Save**."

Ask whether the repository is public or private.

> "Now a token limited to that repository's files. **You paste it into the settings window; never
> paste it here in the chat.**
>
> 1. Go to https://github.com/settings/personal-access-tokens/new
> 2. Token name 'SiteCrew'. Expiration: **90 days**
> 3. Resource owner: **the account that owns the repository** (your username, or the organization if the
>    repository is in one; otherwise it won't appear in the next list)
> 4. Repository access: **Only select repositories**, then choose your one repository
> 5. Permissions: click **Add permissions**, choose **Contents**, and set it to **Access: Read and write**
>    (Metadata, read-only, is added and marked Required). Add nothing else
> 6. 'Generate token' and copy it
> 7. In the settings window, paste it into the **GitHub token** box and click **Save**. When every
>    key says saved, close the window
>
> Tell me when it's closed. (Don't tell me the token.)"

Never ask for, echo or print a token. Verify:

```bash
python .claude/scripts/settings_window.py list
python .claude/scripts/github_api.py check
```

`list` shows each key's state, never a key, and ends with "Every needed key is saved" (exit 0). It
shows the repository as owner/name (not secret): save the two parts as `GITHUB_OWNER` and `GITHUB_REPO`.

It must say the token reaches the repository with push access. Then ask the owner to confirm, in
GitHub's token settings, the three things the script prints: only this repository is selected,
Contents is Read and write, and the token has an expiry date. Be plain about what this means: the
token can only WRITE to that one repository. Fine-grained tokens can still read public repositories.
Wait for the owner's confirmation. If `check` fails, make a new token for the one repository.
For a repository in an organization: the organization may have to approve the token first, and until
then it can only read public repositories. An organization owner's own token is approved automatically
(https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

---

## STEP 4: Choose how to build, then build in `site/`

The site always lives in `site/` (git-ignored, it becomes the owner's own repository).

### Choose (both roads)

Think the problem through, then offer a short list with trade-offs, say which you would pick and why,
and let the owner choose:

- **Plain HTML/CSS:** simplest, you edit files directly, fewer moving parts.
- **WordPress, as a static export** (for example with the Simply Static plugin): the owner keeps
  working in WordPress, and the exported static files go on Pages. A live WordPress site is a
  different road (SiteCrew Paid), not this kit.
- **Astro** (or another static generator): templates and blogs are easy, needs a build step.
- **Next.js** with `output: 'export'` only: powerful, heavier to maintain.
- **Others** the owner names (Vite, Gatsby...).

Save `SITE_FRAMEWORK` (`html`, `nextjs`, `astro`, `vite`, `gatsby`, `other`; a WordPress static export
is `html`, a folder of static files).

### Road 1 (move): get the content

Official export first, then a careful copy of the owner's own words and photos. Say plainly what cannot
come along: the builder's template, licensed images, platform features (forms, stores, bookings). Scraping
terms are a legal question; do not answer it, point to the builder's terms. Build a NEW design for the content.

**Option A: the files are already in a GitHub repository.** Ask for the address and clone it into `site/`:
`git clone <address> site`. Inspect it (what framework, what pages). Go to Step 5, the secret scan, on the
files you just cloned. Nothing goes live until the owner says "yes, publish" in Step 5.

**Option B: the files are on the owner's computer.** "Drop the files into a folder called `site/` here."
Build the new design from the content there.

### Road 2 (fresh): examples or a template first

**The new site is already built** (by the owner or another tool): bring it into `site/` the same way as
Road 1, Option A (a repository) or Option B (files on their computer), then go to Step 5.

> "First, show me what you like. Any of these works: links to sites you admire; screenshots, a sketch or
> a mock-up; the overall idea in plain words; or a template, bought or free.
>
> I take ideas from sites you like. I don't copy another site's code, text or images."

If they name a template, read its license with them BEFORE building (attribution? client work? one site
only?) and say plainly what it allows. GUIDE.md chapter 1b lists common free-template licenses.

Build the site in `site/`: use the business details and tone from the interview and their examples;
semantic HTML5, mobile-responsive, a `<title>`, a meta description and Open Graph tags.

The owner looks at it on their own computer (not public) and asks for changes until they like it.

---

## STEP 5: Secret scan, then the first publish

### Secret scan (before any commit)

Do this on the files in `site/` BEFORE `git add` or any commit. A secret that gets into a commit stays in
the history, and the first push would publish that history.

List every file (`find site -type f`, skipping `node_modules`) and show the owner the list. Look for
things that must never be published: `.env` or `.env.*` (an `.env.example` is fine when it holds only
names and empty or placeholder values: open it and check), `*.sql`, `*.bak`, `*.old`, `*.zip`,
`wp-config.php`, private keys (`*.pem`, `*.key`, `id_rsa*`), and any file whose text holds passwords, API
keys or tokens (search for `password`, `secret`, `api_key`, `BEGIN PRIVATE KEY`).

If you find ANY: STOP. Tell the owner what you found and why it must not go public. Move it out of `site/`
or add it to `site/.gitignore`, then scan again until clean.

If `site/` already contains a `.git` folder (an old export or a clone):
- Cloned from the owner's repository (Option A): its history is already on GitHub. If a secret appears
  in the files or `git log -p`, tell the owner to treat it as exposed and replace it (new password or
  key), because deleting it now does not un-publish it.
- Anything else: ask the owner before deleting that `.git` folder, and start a clean one below.

If anything was already committed locally and not pushed, rebuild it: delete `site/.git`, run the
scan again, and make a new first commit.

### Commit (only when the scan is clean)

Road 1 Option B and road 2:

```bash
cd site
git init -b main
git add .
git commit -m "Initial site"
```

Option A: the clone already has its history; commit only your own edits, if any.

### First publish (needs "yes, publish")

Show the owner what will go live: the files changed or added (`git -C site status`, `git -C site ls-files`)
and a plain-words summary (pages, what they say, anything that links elsewhere). Then ask:

> "This is what will go on GitHub and then live on the internet. Say **yes, publish** and I'll go ahead.
> If you'd like anything changed first, tell me."

Wait. Only "yes, publish" (or a clear equivalent) counts. A wish like "looks good, go ahead and fix the
footer" is not a yes to publish. No yes, no push, and no Pages project.

On yes, for new commits:

```bash
python .claude/scripts/github_api.py push main --owner-approved
```

Option A with nothing new to push: the yes is the approval to connect this repository to Cloudflare Pages in Step 6.

---

## STEP 6: Pages, checked on `*.pages.dev`

### Connect GitHub to Cloudflare (one-time, in the browser)

> "One thing I can't automate, a one-time GitHub authorization:
> 1. https://dash.cloudflare.com, then **Workers & Pages** (in the left menu)
> 2. **Create application**, then **Continue with GitHub**
> 3. On GitHub, choose your account (or your organization if the repo is in one), choose
>    **Only select repositories**, pick just your site's repository, then **Install & Authorize**
> 4. Back in Cloudflare you see **Select a repository** with your repository and a **Next** button.
>    **Stop there: don't press Next or Deploy.** That wizard makes a different kind of project; I create
>    the Pages project for you. Tell me when you're there."
>
> (The dashboard changes from time to time. If your screen looks different, send me a screenshot.)

### Build settings

| Framework | Build command | Output directory |
|-----------|--------------|-----------------|
| `html`    | *(empty)*    | `/`             |
| `nextjs`  | `npm run build` | `out`        |
| `astro`   | `npm run build` | `dist`       |
| `vite`    | `npm run build` | `dist`       |
| `gatsby`  | `npm run build` | `public`     |
| `other`   | ask the owner what builds the site and where the output goes | |

A WordPress static export is `html`: the output directory is the folder that holds `index.html`.

**Next.js:** before creating the project, confirm `output: 'export'` in `next.config.js`, `.mjs` or `.ts`,
then run `npm install` and `npm run build` inside `site/` and check that `out/` exists and holds
`index.html`. If not, STOP and fix it with the owner (adding `output: 'export'` is a code change: show
it, get a yes). No Pages project until `out/` is produced.

### A Wrangler file in `site/`

If `site/` holds `wrangler.toml`, `wrangler.json` or `wrangler.jsonc` with `pages_build_output_dir`, Pages
takes the project's settings from that file, not from the dashboard
(https://developers.cloudflare.com/pages/functions/wrangler-configuration/). Read it with the owner before
creating the project: its `name` should be `CF_PAGES_PROJECT`, and every binding in it (a database,
storage) must exist, or the deploy fails. `pages-create` prints what it finds and stops on a placeholder id.

### Create the project and deploy

Project names use lowercase letters, numbers and hyphens (`mybusiness.com` becomes `mybusiness-com`).
Save as `CF_PAGES_PROJECT`.

```bash
python .claude/scripts/cf_api.py pages-create [CF_PAGES_PROJECT] [GITHUB_OWNER] [GITHUB_REPO] main --build-command "[BUILD_COMMAND]" --output-dir "[OUTPUT_DIR]"
python .claude/scripts/cf_api.py pages-deploy [CF_PAGES_PROJECT] main
```

> "Cloudflare is building your site. Watch it at https://dash.cloudflare.com → Workers & Pages →
> [CF_PAGES_PROJECT] → Deployments, and tell me when it shows 'Success'."

If the build fails, see Error Handling.

### Check the site on `*.pages.dev`

Open `https://[CF_PAGES_PROJECT].pages.dev` with the owner. Check every page, every link and every form.
Do not touch the domain until the owner says the site is right.

---

## STEP 7: The domain (no domain: skip to Step 8)

Do these in order. Nothing here is live on the owner's domain until the nameservers point to Cloudflare.

1. **Mail-check.** Needed whenever the nameservers have not moved yet (a domain already active on
   Cloudflare skips this and goes to item 2).

   ```bash
   python .claude/scripts/cf_api.py mail-check [DOMAIN]
   ```

   Exit 0: go on. Exit 1: STOP. Show the owner the table and the missing records, add them in
   Cloudflare (DNS only, not proxied), run it again until it passes. Tell the owner the limit it prints:
   DKIM selectors can't be listed from outside, so they should also compare with their mail provider's
   setup page. Moving mailboxes is not this kit's job: see GUIDE.md chapter 6b.

2. **DNS conflicts, on the owner's yes.**

   ```bash
   python .claude/scripts/cf_api.py dns-conflicts [DOMAIN]
   ```

   If records come back (A, AAAA or CNAME at the root or `www`), show them:
   > "These records are at your root or www now: [list]. To point the domain at your new site I will DELETE
   > exactly these and create new ones. Nothing else is touched (email records and other names stay).
   > If they belong to a live site you want to keep running, tell me now. Otherwise say 'yes'."

   No yes, no deletion. If nothing comes back, continue.

3. **Register both names and wire up DNS.**

   ```bash
   python .claude/scripts/cf_api.py pages-domain [CF_PAGES_PROJECT] [DOMAIN]
   python .claude/scripts/cf_api.py pages-dns [DOMAIN] [CF_PAGES_PROJECT] --owner-approved
   ```

   `pages-domain` registers `[DOMAIN]` and `www.[DOMAIN]` and prints each one's status. Re-run it
   (it is safe to repeat) and watch the status in Cloudflare; it exits 1 if a name is missing. `pages-dns`
   removes only the records the owner approved and creates proxied CNAMEs for both names.

4. **Move the nameservers** (only if the domain was not already on Cloudflare), after the mail-check passed:

   > "Mail records are safe. Now set BOTH nameservers at your registrar to the two Cloudflare shows you.
   > Which registrar is it? I'll give you step-by-step instructions."

   If you use `namecheap_to_cf.py` or `spaceship_to_cf.py`, they need `--owner-approved`, run
   `mail-check` themselves right before the change, and stop (exit 1) if it fails. One domain at a time.
   Cloudflare emails the owner when the domain is active; watch the status in the dashboard and wait for it.

5. **Verify both names.** Run `pages-domain` again until both names are active, then open
   `https://[DOMAIN]` and `https://www.[DOMAIN]` and confirm both load the site. Certificates and DNS take
   as long as they take: look at the status, don't guess.

---

## STEP 8: Email, then the old service

Email test (if the domain has email): the owner sends a message to their address and has a friend send
one too. Both must arrive, and replies must work. If the mailbox lived with the old host or builder and
needs a new home, GUIDE.md chapter 6b has the side note (Zoho Mail's free plan is one suggestion; read
Zoho's own setup pages and help step by step; set up the new mailbox and copy the old mail BEFORE the
old service is cancelled).

Road 1 only: **only now** talk about cancelling the old builder or host, and ask for its renewal date.
Cancel before it renews, but only after the site, both names and email are confirmed. Road 2 has nothing to cancel.

---

## STEP 9: Write the setup record

Create `.agent/free-setup-progress.md`:

```markdown
# SiteCrew AaSS Kit Setup: [BUSINESS_NAME]

## Status: COMPLETE
## Date: [today's date]

## Site
- Business: [BUSINESS_NAME]
- Road: [move / fresh]
- Domain: [DOMAIN]
- Framework: [SITE_FRAMEWORK]

## GitHub
- Owner: [GITHUB_OWNER]
- Repo: [GITHUB_REPO]
- Visibility: [public/private]
- Token expires: [date, 90 days from creation]

## Cloudflare
- Pages project: [CF_PAGES_PROJECT]
- Live URL: https://[DOMAIN]
- Pages URL: https://[CF_PAGES_PROJECT].pages.dev

## Steps Completed
- [x] Step 1, Interview
- [x] Step 2, Cloudflare and token
- [x] Step 3, GitHub repo and token
- [x] Step 4, Built in site/
- [x] Step 5, Secret scan and first publish
- [x] Step 6, Pages checked on pages.dev
- [x] Step 7, Domain
- [x] Step 8, Email checked
```

Also fill the memory templates (`.claude/memory-templates/SOUL-free.md`, `USER.md`) into `My-Vault/Memory/`
(no tokens in them). Remind the owner that the GitHub token expires on the date above and needs renewing:
a new token for the same repository, pasted into the settings window's GitHub token box with **Replace**.

---

## STEP 10: Done

> "Your site is set up: https://[DOMAIN] (or https://[CF_PAGES_PROJECT].pages.dev).
> - Hosted on Cloudflare Pages; the GitHub repo is https://github.com/[GITHUB_OWNER]/[GITHUB_REPO]
> - Every push to `main` updates the site, and I only push after your "yes, publish"
>
> To change something, tell me in plain words. I'll show you what changes and wait for your yes.
>
> Need your own server or a back office? That is SiteCrew Paid; the tested solutions are in the Practical AI Community.
>
> What would you like to do next?"

---

## Error Handling Notes

**Pages create fails with "could not connect to GitHub":** the authorization in Step 6 wasn't completed for
the right account or organization. Walk them through it again.

**Pages create fails with "project name already exists":** append `-site` or `-web` to the project name.

**Build fails in Cloudflare:** have the owner open Workers & Pages → the project → Deployments → the failed
deploy → 'View build log', and paste the last lines of the log here (a build log holds no tokens). Diagnose and fix.

**The domain doesn't load after setup:** look at the status of the domain and its certificate in the
Cloudflare dashboard and run `pages-domain` again. If a name is not active, check the DNS records
with `cf_api.py records [DOMAIN]` instead of waiting blindly.
