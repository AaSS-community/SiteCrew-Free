# SiteCrew AaSS Kit

A free kit that puts your website on Cloudflare Pages, with an AI coding agent that builds it and keeps it for you. Bring a site you rent today, or start a new site (or one more).

**This kit is possible because of SiteCrew.ai.** It is SiteCrew.ai's free starter kit, given to everyone as a working example of AaSS (Agent as Software Solution). See [where it comes from](#where-it-comes-from).

**Read [GUIDE.md](GUIDE.md) first.** It explains everything, with a receipt link for every number.

## What it costs, honestly

All prices are in USD. Use any currency converter for your own currency. Checked 2026-10-03; prices change, so re-check.

- Hosting: **$0**, on Cloudflare's free tier.
- Your domain: currently **$10.46 a year** to register and to renew a .com at Cloudflare ([price table](https://pricing.registrar.cloudflare.com/)). Prices can change. This is never "free".
- The agent: free tiers exist (Gemini CLI $0 with 1,000 requests a day, GitHub Copilot Free $0), and Claude Pro is $20 a month.

## What you need

A computer, an AI coding agent, a free GitHub account, a free Cloudflare account, and a domain.

## Quick start

1. Clone this repository or download it as a ZIP, and open the folder.
2. Open your agent in the folder.
3. Claude Code: type `/init-client-free`. Any other agent: say "follow .claude/commands/init-client-free.md".

One site per folder (`site/`). For a second site, make a second copy of the kit.

## The four safety rules

- Your tokens go into `.claude/scripts/.env` by you, never into the chat. The GitHub token is for one repository only.
- Nothing is published until you say "yes, publish".
- Your email records are checked in Cloudflare before your nameservers move.
- DNS records are deleted only after you say yes.

## For anyone changing the kit

Run `python gate.py` (needs `pip install -r .claude/scripts/requirements.txt`). It checks the scripts, the safety text and the safety logic, offline.

## The method

This kit is an example: take it and build any solution you want with it. The tested solutions are in the Practical AI Community.

## Why it exists

On Nov 29, 2025, Alex G.'s web host billed him $710.82 for three more years of shared hosting. He decided to own instead of rent.

## Where it comes from

**SiteCrew.ai** is a website product in development at Strategic Viral Services Inc., Alex G.'s company: an AI crew for a business website, where an agent builds the site, publishes it and keeps it, and the owner says yes before anything goes live. The full product (your own server, a back office where you talk to your site) is not running yet. This kit is its free starter, and the kit works today: it put [aass.co](https://aass.co) on Cloudflare Pages on Oct 2, 2026 (we filmed the run; the video is coming).

**AaSS** is the same idea as a method, so anyone can learn it and do it. AaSS (Agent as Software Solution) is a software ownership model where an AI agent builds, runs and maintains software you own, instead of software you rent. More: [aass.co/what-is-aass](https://aass.co/what-is-aass)

So the name says both: **SiteCrew**, where the kit comes from, and **AaSS**, the model it shows. This is the first free kit from AaSS.

MIT license, Strategic Viral Services Inc.
