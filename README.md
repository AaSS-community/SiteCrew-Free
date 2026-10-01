# SiteCrew Free

A free kit that puts your website on Cloudflare Pages, with an AI coding agent that builds it and keeps it for you. Bring a site you rent today, or start a new site (or one more).

**Read [GUIDE.md](GUIDE.md) first.** It explains everything, with a receipt link for every number.

## What it costs, honestly

All prices are in USD. Use any currency converter for your own currency. Checked 2026-10-01; prices change, so re-check.

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

MIT license, Strategic Viral Services Inc.
