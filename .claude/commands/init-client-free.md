---
description: Free SiteCrew setup: static website on Cloudflare Pages with GitHub. Guides new users A-Z from zero to live site.
---

# /init-client-free: SiteCrew Free Setup

Guides the user from a fresh install all the way to a live static website on Cloudflare Pages.
No server, no database, no monthly hosting fees.

---

## Before Starting

Check if this workspace is already initialized:

```
Glob: .agent/free-setup-progress.md
```

**If the file exists and shows COMPLETE:**
> "This workspace is already set up for [client name]. Your site is live at [domain].
> What would you like to do? I can help you push changes, update content, or add pages."
> Stop here.

**If the file exists and shows IN PROGRESS:**
Read `.agent/free-setup-progress.md` and resume from the last incomplete step.
Tell the user: "We started setup before, resuming from Step [N]: [step name]."

**If neither exists:** Fresh install. Proceed below.

---

## STEP 0: Welcome

Say:

> "Welcome to SiteCrew Free, your website crew in a box.
>
> I'm going to walk you through getting your website live on Cloudflare Pages.
> It's free hosting, auto-deploys from GitHub, and takes about 20-30 minutes end to end.
>
> I'll ask you some questions along the way. Some steps require you to click a few things
> in your browser, I'll tell you exactly what to do each time.
>
> Let's start. What's your name?"

Wait for their name. Use it throughout the session.

---

## STEP 1: Quick Interview

Ask these questions **one at a time**. Wait for each answer.

1. "What's the name of your business or project?"

2. "What do you do, and who is it for? (2-3 sentences is perfect)"

3. "What's the main goal of the website?
   - Get people to call or email you
   - Book appointments
   - Showcase your work / portfolio
   - Sell something
   - Something else, describe it"

4. "What's the tone of your brand?
   For example: professional and trustworthy, friendly and approachable,
   bold and energetic, clean and minimal..."

5. "Do you already have a domain name? (like mybusiness.com)"

Save all answers. You'll use them when building or reviewing the site content.

---

## STEP 2: Domain Setup

### If they said NO to having a domain:

> "No problem, let's get you one. I recommend Cloudflare Registrar.
> It's the cheapest option (no markup over cost), and it puts your domain
> right inside Cloudflare which makes the rest of setup automatic.
>
> 1. Go to: https://www.cloudflare.com/products/registrar/
> 2. Sign up for a free Cloudflare account if you don't have one
> 3. Search for your domain name
> 4. Buy it (most .com domains are ~$10/year)
>
> Come back and tell me the domain name you bought."

Wait. Once they return with their domain name, they're automatically on Cloudflare, skip the NS propagation wait below and jump straight to the API token step.

---

### If they said YES to having a domain:

Ask: "Is it already on Cloudflare? (If you're not sure, check your registrar, it's on Cloudflare if the nameservers say something like `aria.ns.cloudflare.com`)"

**If YES, already on Cloudflare:** Skip to the API token step below.

**If NO, not on Cloudflare yet:**

> "I need to add your domain to Cloudflare first. Here's exactly what to do:
>
> **Step 1, Create a free Cloudflare account (if you don't have one)**
> Go to: https://cloudflare.com → Sign Up → Free plan
>
> **Step 2, Add your domain**
> In the Cloudflare dashboard:
> - Click 'Add a Site'
> - Type your domain name and click 'Add Site'
> - Choose the Free plan → Continue
> - Cloudflare will scan your existing DNS records, click 'Continue'
>
> **Step 3, Stop here, do NOT change nameservers yet**
> Cloudflare will show you two nameservers. Don't use them yet. First I check that your
> email records made it into Cloudflare, so your email keeps working. Tell me when you're here."

**Before any nameserver change, get the Cloudflare token and run the mail check.**
Do the "Cloudflare API Token" section below first (the zone now exists, so the token can be limited to it), then:

```bash
python .claude/scripts/cf_api.py mail-check [DOMAIN]
```

- **Exit 0 (PASS):** continue to the nameserver change below.
- **Exit 1 (MISMATCH):** STOP. Show the owner the table and the missing records. Add the missing
  records in Cloudflare first (DNS only, not proxied), then run `mail-check` again. Repeat until it
  passes. Only then move nameservers.
- Always tell the owner the limit the script prints: DKIM selectors can't be listed from outside,
  so they should also compare with their mail provider's setup page.
- If you use `namecheap_to_cf.py` or `spaceship_to_cf.py` to switch nameservers, they need `--owner-approved`
  (the owner's yes) and run `mail-check` themselves right before the change; they stop if it fails.
  One domain at a time.

Moving mailboxes is not this kit's job. Email side note: see GUIDE.md chapter 6b.

**Only after `mail-check` passes**, tell them:

> "Mail records are safe. Now update your nameservers.
> Cloudflare shows two (like `aria.ns.cloudflare.com` and `beck.ns.cloudflare.com`).
> Log into your domain registrar and set BOTH nameservers to what Cloudflare shows you.
>
> Which registrar do you use? (GoDaddy, Namecheap, Dynadot, Google, other?)
> I can give you step-by-step instructions for your specific registrar."

Give registrar-specific nameserver change instructions based on their answer.

> "Once you've changed the nameservers, Cloudflare will send you an email with the subject:
> '[your domain] is now active on Cloudflare'
>
> That can take anywhere from 5 minutes to a few hours depending on your registrar.
> No rush, come back here once you get that email."

**WAIT** for them to confirm they received the Cloudflare activation email before continuing.

---

### Cloudflare API Token

Needs the domain added to Cloudflare (so the token can be limited to that one zone).

> "Now I need an API token so I can set up your hosting. **You paste it into a file yourself;
> never paste it here in the chat.**
>
> 1. Go to: https://dash.cloudflare.com/profile/api-tokens
> 2. Click 'Create Token', then 'Create Custom Token' (at the bottom)
> 3. Give it a name like 'SiteCrew'
> 4. Under Permissions, add these three:
>    - Zone → Zone → Read
>    - Zone → DNS → Edit
>    - Account → Cloudflare Pages → Edit
> 5. Under Zone Resources: 'Include → Specific zone → [your domain]' (this limits both Zone permissions to your domain)
> 6. Click 'Continue to summary' → 'Create Token' and copy the token (you only see it once)
> 7. Copy `.claude/scripts/.env.example` to `.claude/scripts/.env` (if you haven't yet),
>    open `.env` in your editor and paste the token after `CF_API_TOKEN=`. Save the file.
>
> Tell me when it's saved. (Don't tell me the token.)"

Never ask for, echo, or print the token. Then the Account ID (not secret):

> "One more thing, your Cloudflare Account ID:
> 1. Go to: https://dash.cloudflare.com
> 2. In the left sidebar, expand **Domains** and click your domain name
> 3. Click **Overview** (top of the left menu)
> 4. On the right side of the page, scroll down to the **API** section
> 5. Copy the **Account ID** (not the Zone ID) and put it after `CF_ACCOUNT_ID=` in `.env`"

Verify the token works:
```bash
python .claude/scripts/cf_api.py zones
```

If it lists zones including their domain: "Great, Cloudflare is connected."
If it errors: help them troubleshoot the token permissions before continuing.

---

## STEP 3: GitHub Setup

Ask: "Do you have a GitHub account?"

**If NO:**
> "GitHub is where your website's code lives. It's free.
> 1. Go to: https://github.com → Sign Up
> 2. Come back once your account is created."
> Wait.

**Then (the kit only ever gets access to ONE repository):**

> "Please create ONE empty repository for your website:
> 1. Go to: https://github.com/new
> 2. Name it (for example `mybusiness-site`), leave it empty (no README, no .gitignore, no license)
> 3. Click 'Create repository' and tell me its address (like https://github.com/your-username/mybusiness-site)"

Parse the owner and repo name from the URL. Save as `GITHUB_OWNER` and `GITHUB_REPO`.
Ask: "Is the repository public or private?" Save as `GITHUB_REPO_VISIBILITY`.

Then the token, limited to that one repository:

> "Now a token that can touch only that repository. **You paste it into a file yourself;
> never paste it here in the chat.**
>
> 1. Go to: https://github.com/settings/personal-access-tokens/new
> 2. Token name: 'SiteCrew'. Expiration: **90 days**
> 3. Repository access: **Only select repositories** → choose your one repository
> 4. Repository permissions: **Contents → Read and write** (Metadata: Read is added automatically).
>    Leave everything else at 'No access'.
> 5. Click 'Generate token' and copy it
> 6. Open `.claude/scripts/.env` in your editor, paste it after `GITHUB_TOKEN=`, and write
>    `GITHUB_REPO=your-username/mybusiness-site` on the next line. Save the file.
>
> Tell me when it's saved. (Don't tell me the token.)"

Never ask for, echo, or print the token. Verify:

```bash
python .claude/scripts/github_api.py check
```

It must report push access and "Other repositories this token reaches: 0". If it fails, walk the owner
through making a new fine-grained token for the single repository.

---

## STEP 4: Site Files

Ask: "What's the situation with your website files?"

**Option A: Files are already in the GitHub repo:**
> "Perfect, Cloudflare will build directly from your repo. Nothing to do here."
> Ask: "What technology is the site built with? (Plain HTML/CSS, Next.js, Astro, Vite, Gatsby, other?)"
> Save `SITE_FRAMEWORK`, we'll use this to set the right build command in Step 6.

**Option B: Files are on your computer, not yet on GitHub:**
> "Drop the website files into a folder called `site/` here in this directory.
> Tell me when you've done that and I'll show you what will be published."
>
> Once they confirm, prepare the commit (no push yet):
> ```bash
> cd site/
> git init -b main
> git add .
> git commit -m "Initial site"
> ```
> Then do the **first publish** (see "First publish" below). Set `SITE_FRAMEWORK` to "html" unless they tell you otherwise.

**Option C: No website yet, build from scratch:**
> "No problem, I'll build a clean static website based on what you told me about your business.
>
> Here's what I'll create:
> - Home page (headline, what you do, call to action)
> - Services/About section
> - Contact section (phone, email, address if applicable)
> - Clean, modern design with your brand colours
>
> This will be a plain HTML/CSS site, fast, no dependencies.
>
> Give me a moment to build it..."

Build the site:
- Create `site/` folder with `index.html`, `css/style.css`, and any subpages
- Use business name, description, services, brand tone, and colours from the interview
- Keep it clean: semantic HTML5, one CSS file, mobile-responsive, no JavaScript frameworks
- Include a `<title>`, meta description, and Open Graph tags

Then prepare the commit and do the **first publish** as in Option B. Set `SITE_FRAMEWORK` to "html".

---

### First publish (needs "yes, publish")

Before the first push, list EVERY file that is staged (`git -C site ls-files`, after `git add .`) and
look for things that must never be published: `.env` or `.env.*`, `*.sql`, `*.bak`, `*.old`, `*.zip`,
`wp-config.php`, private keys (`*.pem`, `*.key`, `id_rsa*`), `.git` folders from the old site, and any file
whose text holds passwords, API keys or tokens (search the staged files for `password`, `secret`,
`api_key`, `BEGIN PRIVATE KEY`). If you find ANY: STOP. Unstage it (`git -C site rm --cached <file>`),
tell the owner what you found and why it must not go public, and move it out of `site/` (or add it to
`site/.gitignore`) before going on. Only when the list is clean, show the owner what will go live: the list
of files in `site/` and a plain-words summary (pages, what they say, anything that links elsewhere). Then ask:

> "This is what will go on GitHub and then live on the internet. Say **yes, publish** and I'll push it.
> If you'd like anything changed first, tell me."

Wait. Only the words "yes, publish" (or a clear equivalent) count. A wish like "looks good, go ahead
and fix the footer" is not a yes to publish. If there is no yes, do not push. On yes:

```bash
python .claude/scripts/github_api.py push main --owner-approved
```

---

## STEP 5: Connect GitHub to Cloudflare (One-Time OAuth)

This is the one step that requires a browser click, it's a one-time GitHub authorization.

> "Almost there. I need to do one thing that I can't automate, it's a one-click
> GitHub authorization in your browser. Takes about 30 seconds.
>
> Here's exactly what to do:
>
> 1. Go to: https://dash.cloudflare.com
> 2. In the left sidebar, under **Build**, click **Compute**, then **Workers & Pages**
> 3. Click the blue **Create application** button (top right)
> 4. A dialog appears, click **Connect GitHub** (under 'Ship something new')
> 5. GitHub will ask where to install Cloudflare Workers and Pages:
>    - Select your personal GitHub account
>    - If your repo is inside a GitHub organization, also click that org name
> 6. On the next screen, choose **Only select repositories** and pick just your site's repo
> 7. Click **Install & Authorize**
> 8. You'll be redirected back to Cloudflare showing a 'Select a repository' screen
>
> **IMPORTANT: Stop here, do not select a repo or finish the wizard.**
> Come back here and I'll create the project via API with the correct build settings.
>
> Come back and tell me when you've completed the GitHub authorization."

Wait for confirmation before continuing.

---

## STEP 6: Deploy to Cloudflare Pages

### Detect build settings

Based on `SITE_FRAMEWORK`:

| Framework | Build Command | Output Directory |
|-----------|--------------|-----------------|
| `html`    | *(empty)*    | `/`             |
| `nextjs`  | `npm run build` | `out`        |
| `astro`   | `npm run build` | `dist`       |
| `vite`    | `npm run build` | `dist`       |
| `gatsby`  | `npm run build` | `public`     |
| `other`   | Ask the user what command builds their site and what folder the output goes to |

### Next.js: check the static export first

Only if `SITE_FRAMEWORK` is `nextjs`. Cloudflare Pages here serves static files, so before the Pages
project is created, confirm in `next.config.js` / `next.config.mjs` / `next.config.ts` that it has
`output: 'export'`, then run a local build (`npm install` then `npm run build` inside `site/`) and check
that the `out/` folder now exists and holds `index.html`. If the setting is missing or the build does not
produce `out/`, STOP and fix that with the owner (adding `output: 'export'` is a code change: show it and
get a yes first). Do not create the Pages project until `out/` is produced.

### Sanitize the project name

Cloudflare Pages project names: lowercase letters, numbers, hyphens only. No dots.
Convert the domain to a valid project name: `apiconcierge.app` → `apiconcierge-app`

Save as `CF_PAGES_PROJECT`.

### Create the Pages project

```bash
python .claude/scripts/cf_api.py pages-create \
  [CF_PAGES_PROJECT] \
  [GITHUB_OWNER] \
  [GITHUB_REPO] \
  main \
  --build-command "[BUILD_COMMAND]" \
  --output-dir "[OUTPUT_DIR]"
```

Then immediately trigger the first deployment, no dashboard clicks needed:

```bash
python .claude/scripts/cf_api.py pages-deploy [CF_PAGES_PROJECT] main
```

> "Cloudflare is building your site now. The first build takes 1-3 minutes.
>
> You can watch it here:
> https://dash.cloudflare.com → Workers & Pages → [CF_PAGES_PROJECT] → Deployments
>
> Tell me when the deployment shows 'Success' (green checkmark)."

Wait for them to confirm the build succeeded before adding the custom domain.

### DNS pre-check

Before creating DNS records, check what is already at the root and `www`:

```bash
python .claude/scripts/cf_api.py dns-conflicts [DOMAIN]
```

**If records are returned (A, AAAA or CNAME at the root or www):** show them to the user and say:
> "Your domain has these existing records at the root or www:
> [list them]
>
> This can happen if your domain was previously used for another site,
> or if your registrar added default records.
>
> To point your domain at Cloudflare Pages I will DELETE exactly these records and create new ones
> pointing to your site. Nothing else is touched (email records and everything on other names stay).
>
> If these belong to a live site you want to keep running, tell me now. Otherwise say 'yes'."
>
> Wait for the owner's yes. No yes, no deletion.

**If nothing is returned:** continue.

### Add the custom domains and wire up DNS

```bash
python .claude/scripts/cf_api.py pages-domain [CF_PAGES_PROJECT] [DOMAIN]
python .claude/scripts/cf_api.py pages-dns [DOMAIN] [CF_PAGES_PROJECT] --owner-approved
```

`pages-domain` registers BOTH `[DOMAIN]` and `www.[DOMAIN]` with Cloudflare Pages and then checks that
both are registered (it prints each one's status, usually `pending` for a minute or two, then `active`).
It exits 1 if either is missing: fix that before going on.
`pages-dns` (only with the owner's yes, via `--owner-approved`) deletes exactly the A, AAAA and CNAME
records at the root and `www` that you showed the owner, then creates proxied CNAMEs for both to the
Pages project. MX, TXT and every other name are never touched. The SSL certificate is provisioned automatically.

Verify: wait a minute or two, run `pages-domain` again (it is safe to repeat) until both show `active`,
then open `https://[DOMAIN]` and `https://www.[DOMAIN]` (or ask the owner to) and confirm both load the site.

> "Custom domain configured! [DOMAIN] and www.[DOMAIN] both point to your site.
> SSL certificate will be active within 1-2 minutes."

---

## STEP 7: Write Setup Record

Create `.agent/free-setup-progress.md`:

```markdown
# SiteCrew Free Setup: [BUSINESS_NAME]

## Status: COMPLETE
## Date: [today's date]

## Site
- Business: [BUSINESS_NAME]
- Domain: [DOMAIN]
- Framework: [SITE_FRAMEWORK]

## GitHub
- Owner: [GITHUB_OWNER]
- Repo: [GITHUB_REPO]
- Visibility: [public/private]

## Cloudflare
- Pages project: [CF_PAGES_PROJECT]
- Live URL: https://[DOMAIN]
- Pages URL: https://[CF_PAGES_PROJECT].pages.dev

## Steps Completed
- [x] Step 1, Interview
- [x] Step 2, Domain on Cloudflare
- [x] Step 3, GitHub repo
- [x] Step 4, Site files
- [x] Step 5, GitHub -> Cloudflare OAuth
- [x] Step 6, Deployed to Pages
- [x] Step 7, Setup record written
```

---

## STEP 8: Done

> "Your site is live!
>
> **[BUSINESS_NAME] is now live at https://[DOMAIN]**
>
> Here's what's set up:
> - Static website deployed on Cloudflare Pages (free)
> - GitHub repo: https://github.com/[GITHUB_OWNER]/[GITHUB_REPO]
> - Auto-deploys: every time I push to the main branch (only after your "yes, publish"), your site updates
>
> ---
>
> **How to update your site:**
> Tell me what to change. I'll show you what changes, and when you say "yes, publish" I push it
> and your site rebuilds and redeploys automatically.
>
> ---
>
> **Want more?**
> Need your own server or a back office? That is SiteCrew Paid; the tested solutions are in the Practical AI Community.
>
> ---
>
> That's it, you're live. What would you like to do next?"

---

## Error Handling Notes

**CF Pages create fails with "could not connect to GitHub":**
The OAuth step in Step 5 wasn't completed for the right account/org. Walk them back through Step 5, making sure they authorized the correct GitHub account and any orgs where the repo lives.

**CF Pages create fails with "project name already exists":**
Try appending `-site` or `-web` to the project name (e.g., `apiconcierge-app-site`).

**Build fails in Cloudflare:**
> "The build failed. Let's check what went wrong:
> 1. Go to Cloudflare → Workers & Pages → [project] → Deployments → click the failed deploy
> 2. Click 'View build log'
> 3. Paste the last 20 lines of the log here"
>
> Diagnose and fix based on the error.

**DNS not resolving after custom domain added:**
> "DNS changes can take a few minutes to propagate. Wait 5 minutes and try again.
> If it still doesn't work after 10 minutes, let's check the DNS records in Cloudflare."
