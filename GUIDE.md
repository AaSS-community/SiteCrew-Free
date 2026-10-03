# Your website, on hosting you own

SiteCrew Free: a free kit that puts your website on Cloudflare Pages, with an AI agent that builds it and keeps it for you. Bring a site you rent today, or start a new one.

## 0. What this is, in one screen

This kit is for two kinds of readers, and they share almost every chapter.

- **You have a site you rent,** usually by the month, on a website builder or an old host. The kit moves it onto hosting you own.
- **You want a new site, or one more site.** The kit builds it from examples you like, from your own idea, or from a template, and puts it on the same hosting.

Either way, an AI coding agent (Claude Code or a similar one) does the work while you direct it. You stay in charge. The agent asks before anything leaves your computer. Nothing is published to GitHub, to Cloudflare or to your domain until you say yes.

**What it costs, honestly:**

All prices in this guide are in USD. Use any currency converter for your own currency.

- **Hosting: $0.** The hosting is Cloudflare Pages, on Cloudflare's free tier [R1].
- **Your domain: currently $10.46 a year to register and to renew a .com** at Cloudflare. Prices can change. This is never part of "free". It is your yearly cost [R2].
- **The agent: free tiers exist, with limits.** Gemini CLI is $0 with a Google account (1,000 requests a day), and GitHub Copilot Free is $0 and includes agent mode [R3]. A paid plan, such as Claude Pro, is $20 a month [R3]. You can pay for one month, just for the build, and cancel.

**What you give up:** the drag-and-drop editor, and the builder's support desk. The agent becomes your editor. If you like dragging boxes around and calling a help line, a builder may be the right choice for you (see chapter 10).

**Why is the hosting free?** Our reading: Cloudflare offers a free tier hoping you will stay and grow with them. When your site gets big, or needs more, you may pay them. Cloudflare has not told us this; it is our inference, and we say so, so that you can decide with your eyes open.

### Why this kit exists

On Nov 29, 2025, Alex G.'s web host sent a bill: $710.82 for three more years of shared hosting for svsinc.com, his agency's site [R7]. He decided to stop renting and start owning. He built AI agents to do that work for himself first: move the site, keep it, change it when asked. This kit is the free part of what he built. It is a gift, and it can be one because Cloudflare hosts sites like yours for free.

**This kit is an example of what's possible.** Take it, change it, and build any solution you want with it: that is the method, an AI agent as your software solution. We share what we learned, the pain and how we solved it, so you can do it yourself. If you'd rather have our already tested agents and solutions, they are in the Practical AI Community.

His own business needed more than a website, so his site runs on his own server today. That road (your own server, a back office, the other things a business may want) is SiteCrew Paid.

## 1. Before you start

### The leaving test (for sites you rent today)

Website builders serve many owners well, and many owners are happy to pay them. This guide is not against them. It asks you one question, and you answer it yourself:

**Can you walk away with your data, your code and your process?**

Here is what five common builders' own help pages say you can export [R5]. We quote them. We give no verdicts.

| Builder | What its help pages say you can export |
|---|---|
| Wix | No site export: "your site must run on Wix's servers". CMS collections as CSV. |
| Squarespace | Some content as XML (for WordPress), products and contacts as CSV. No design, styles or custom CSS. "Squarespace owns the Templates." |
| Shopify | Data as CSV (products, customers, orders). The theme as a ZIP, but a bought theme is "licensed only to the store" it was bought for. |
| WordPress.com | Content as XML (not media files, theme or plugins). For the whole site, its export page names a migration plugin, or a full backup on Business and Commerce plans. |
| Webflow | Full front-end code (HTML, CSS, JS, images), only on a paid Workspace plan. CMS as CSV. Forms, store and CMS stop working outside. |

Other builders publish their own export pages, and some of them disagree with themselves (Framer's help has two articles that give different answers). Check your builder's current page yourself.

### What you need

- A computer.
- An AI coding agent (chapter 0 has the options and prices).
- A GitHub account (free).
- A Cloudflare account (free).
- A domain. If you have one, access to wherever it is registered. If you don't, Cloudflare sells domains at cost [R2].

### ⚠️ Warning 1: where is your domain registered?

(For people moving a site.) If your domain came "free" with the builder, it may be registered through the builder. Find out first. Log in to your builder and look for a "domains" page. If the builder is the registrar, you will need to unlock the domain and ask for an authorization code before it can move (chapter 6). The agent will help. Do this early, because transfers can have a waiting period.

### ⚠️ Warning 2: your email can stop

(For people moving a site.) If you use email on your domain (you@yourbusiness.com), moving the domain's DNS must carry your email records (called MX records) over. If they are lost, your email stops. The agent checks this before anything moves, and shows you the records first. If your mailbox itself lives with your old host or builder, it needs a new home before you cancel them: see the side note in chapter 6b.

## 1b. Starting fresh: a new site, or one more site

No old site to move? Good. You skip chapter 3 and the leaving test, and you share everything else.

**Show the agent what you like.** Any of these works:

- Links to sites you admire.
- Screenshots, a sketch on paper, or a mock-up.
- The overall idea in plain words: what the site is for, who visits, how it should feel.

The agent builds your site from that. **It takes ideas from the sites you like. It does not copy another site's code, text or images.**

**Or start from a template.** You can buy one, or use one of the many free ones. The agent can find them, set one up and fit it to your content.

- **Free templates have licenses, and they differ.** HTML5 UP says its templates are licensed under the Creative Commons Attribution 3.0 License, so you must give credit [R9]. Start Bootstrap's templates carry the MIT license [R10]. BootstrapMade's free templates say "You must keep the footer credit line as is: Designed by BootstrapMade" and "You cannot use the free version to create websites for clients or charge for your work" [R11]. Free Astro themes each carry their own license, for example MIT for Astro Paper [R12]. Read the license of the one you pick.
- **Bought templates** usually come with a license for one site or one end product, not unlimited use. Webflow's paid templates, for example, are licensed for "one single End Product" [R13]. Before building, the agent reads the license with you and tells you plainly what it allows.

**One more site?** The kit holds one site per folder (`site/`). A second site is a second copy of the kit in its own folder, with its own GitHub repository and its own token.

## 2. Tell the agent about your site

Download this kit, open your agent in the kit's folder, and tell it:

- Moving a site: where it lives today. Starting fresh: your examples, mock-up or template (chapter 1b).
- What it does. Pages only? A contact form? A store? Bookings?
- What you want it to become.

Then the agent thinks the problem through and **offers you a list of options, not one path.** For example: plain HTML, WordPress (on Cloudflare Pages that means a static export, such as the Simply Static plugin; a live WordPress is a different road, SiteCrew Paid), Next.js, Astro, and others. Each comes with its trade-offs (how easy it is to change, what it costs to keep, what it can do). The agent says which it would pick and why. **You choose.**

## 3. Get your content out (moving a site)

The agent works in this order:

1. **The official export first.** Whatever your builder gives you (chapter 1).
2. **Then a careful copy of your own words and photos** from your live site, if the export is not enough.

**What cannot come along.** The agent tells you plainly, item by item:

- **The builder's template design.** Your content is yours. The template usually belongs to the builder: "Squarespace owns the Templates", Showit designs are "exclusive to Showit hosting", and a Shopify theme is licensed to one store [R8].
- **Licensed stock images.** These often do not transfer [R8].
- **Platform features.** Forms, stores, bookings and member areas need a replacement. The agent lists each one and offers choices.

Several builders' terms also ban automated scraping of their service [R8]. Whether that covers copying the text of your own public site is a legal question, and this guide cannot answer it. This is not legal advice. Read your builder's current terms.

That is why the kit moves your **content** and builds a **new design** for it.

## 4. The agent builds the new site

The agent takes your content (or your examples and ideas) and builds the design. For a moved site it can feel like your old one. It does not copy the old template's code.

You look at it on your own computer first. Ask for changes until you like it. Nothing is public yet.

## 5. GitHub: your site's home

GitHub is where your site's files live, with a history of every change.

- You create one empty repository for the site (one click on GitHub).
- The agent shows you how to make a **fine-grained token** for that one repository only, able to change its files and nothing else, with an expiry date. That is the least access that works: the token can write to that one repository only. (GitHub fine-grained tokens can still read public repositories, which anyone can read anyway.) If the repository belongs to an organization, you pick the organization as the token's owner, and the organization may have to approve the token before it works.
- You paste the token into a settings file on your own computer, not into the chat.
- The agent publishes to GitHub **only when you approve.** Before every publish it shows you what changed and waits for your "yes, publish".

## 6. Cloudflare: live on the internet

1. Connect your GitHub repository to Cloudflare Pages.
2. The first deploy gives you a free `something.pages.dev` address. Check every page there.
3. HTTPS (the padlock) is automatic.

**Your domain.** A bare domain (yourbusiness.com) must use Cloudflare's DNS on Pages. A www address (www.yourbusiness.com) can keep another DNS service [R1]. You can also move the domain's registration to Cloudflare, which sells domains at cost [R2].

Domain transfers have rules: an unlock, an authorization code, and a waiting period after a recent registration or transfer. The agent walks you through each.

⚠️ Before the DNS moves, the agent lists your email records and checks that they arrived in Cloudflare (Warning 2, chapter 1). If a record is missing, nothing moves until it is fixed.

The limits of the free tier, so you know what "free" covers [R1]: 500 builds a month, 20,000 files per site, and the largest file 25 MiB. Bandwidth is listed as unlimited on Cloudflare's product page.

## 6b. A side note: your business email

This kit moves your website, not your mailbox. But if your email (you@yourbusiness.com) lives with the old host or builder you are leaving, it needs a new home before you cancel them.

If you are stuck, one free suggestion: **Zoho Mail's free plan.** Up to 5 users, 5 GB each, email for one domain [R6]. You use it in the browser and the mobile app; the free plan has no IMAP, POP or ActiveSync, and it is "available only in select data centers", so check your region first [R6].

You don't need a recipe from us. Ask your agent: it can read Zoho's own setup pages and walk you through it, step by step. One rule worth knowing: set up the new mailbox and bring your old mail across **while the old service is still paid**, then cancel.

## 7. Switch over, then cancel (in that order)

(For people moving a site. A brand new site has nothing to cancel.)

1. Point the domain at the new site.
2. Check every page, every form and your email (send yourself a test message, and have a friend send one too).
3. **Only then** cancel the builder plan.

Mind the renewal date. If your plan renews next week, cancel before it renews, but only after step 2 passes. If it is tight, ask the agent to help you plan the timing.

## 8. After launch: the agent keeps it

Changes, new pages, blog posts: you ask, the agent edits, you read what it did, you approve, and it publishes. You can ask in plain words ("change the phone number on the contact page").

## 9. If the site needs a database, or outgrows free

**Cloudflare's free database (D1):** 5 GB of storage across your account (500 MB per database), 5 million rows read a day, and 100,000 rows written a day [R1]. It works with Pages Functions. If you outgrow it, Workers Paid starts at $5 a month [R1]. That is the "hope you grow with us" part of the deal.

**When you need more than Cloudflare gives** (your own server, a back office, apps that run all day): that is a different road, and it is SiteCrew Paid. This free kit stays on Cloudflare.

The proof for this kit's road is the aass.co site (AaSS means Agent as Software Solution): this same kit put it on Cloudflare Pages on Oct 2, 2026, and we filmed the whole run. See it live at [aass.co](https://aass.co); the video is coming.

## 10. The other side of the coin

Building got cheap. Keeping did not.

- **The domain costs money every year.** Currently $10.46 to register and to renew a .com at Cloudflare; prices can change [R2].
- **The agent runs on a paid AI plan,** or on a free tier with limits [R3].
- **You give up the drag-and-drop editor** and the builder's support desk.
- **Keeping a site still takes work.** Updates, a form that breaks, a security fix. The agent makes this lighter. It does not make it free.

**A builder can be the right choice.** Many builders serve their owners well. WordPress.com's Personal plan is $4 a month paid yearly, and Carrd Pro Standard is $19 a year [R4]. Mainstream site plans cost more: Webflow Basic $15, Wix Light $17 and Squarespace Basic $19 a month paid yearly, and Shopify's Basic store plan $29 [R4]. A free domain is often the first year only [R4]. If you want the editor and the help desk, and the price feels fair, stay. If you want to own your data, your code and your process, this kit is for you. You answer the test.

## 11. Receipts

Every number and quote above, with where it comes from. Prices change by promotion and by country: re-check each on the day you use it. Unless a receipt says otherwise, it was checked on 2026-10-03.

- **[R1] Cloudflare free tier limits.** Pages: 500 builds a month, 20,000 files per site, 25 MiB largest file. D1: 5 GB per account and 500 MB per database, 5 million reads and 100,000 writes a day. Workers Paid from $5 a month. A bare domain needs Cloudflare DNS; a www address can use a CNAME. Sources: [Pages limits](https://developers.cloudflare.com/pages/platform/limits/), [Pages product page (bandwidth)](https://www.cloudflare.com/products/pages/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [D1 limits](https://developers.cloudflare.com/d1/platform/limits/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [Pages custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/). Checked 2026-10-03.
- **[R2] Domain prices.** Cloudflare Registrar publishes a price table: [pricing.registrar.cloudflare.com](https://pricing.registrar.cloudflare.com/). It currently shows $10.46 a year to register and to renew a .com. Prices can change, so re-check on the day. Cloudflare's statement that domains are sold at cost: [Registrar FAQ](https://developers.cloudflare.com/registrar/faq/), [Registrar](https://www.cloudflare.com/products/registrar/). Checked 2026-10-03.
- **[R3] Agent prices.** Gemini CLI $0 (1,000 requests a day); GitHub Copilot Free $0; Claude Pro $20 a month ($17 a month on the yearly plan, $200 billed up front). Sources: [Gemini CLI quota and pricing](https://geminicli.com/docs/resources/quota-and-pricing/), [GitHub Copilot plans](https://github.com/features/copilot/plans), [Claude pricing](https://claude.com/pricing). Checked 2026-10-03.
- **[R4] Builder prices.** WordPress.com Personal $4 a month paid yearly, $9 monthly; Carrd Pro Standard $19 a year; Webflow Basic $15, Wix Light $17, Squarespace Basic $19 and Shopify Basic $29 a month paid yearly (a free domain for the first year on yearly plans at several of them). Sources: [WordPress.com pricing](https://wordpress.com/pricing/), [Carrd Pro](https://carrd.com/pro), [Webflow pricing](https://webflow.com/pricing), [Wix plans](https://www.wix.com/plans) and [Wix's US explanation](https://www.wix.com/blog/is-wix-free), [Squarespace pricing](https://www.squarespace.com/pricing), [Shopify pricing](https://www.shopify.com/pricing). Some of these pages show a local currency or load prices by script, so the USD figures come from a US view of the page: Wix's from its own article, Shopify's from its USD page, Squarespace's from the Wayback Machine's US copy of its pricing page captured 2026-09-29 (Basic $228 a year), because the live page shows the visitor's own currency. Re-check on the day. Checked 2026-10-03.
- **[R5] Export statements.** Quotes and claims from each builder's own help pages. Wix: [no site export](https://support.wix.com/en/article/exporting-or-embedding-your-wix-site-elsewhere), [CMS collection CSV](https://support.wix.com/en/article/cms-formerly-content-manager-exporting-content-from-your-collection). Squarespace: [content export (XML)](https://support.squarespace.com/hc/en-us/articles/206566687-Exporting-your-site), [products CSV](https://support.squarespace.com/hc/en-us/articles/360000694948-Export-products-to-a-csv), [customers CSV](https://support.squarespace.com/hc/en-us/articles/229497568-Managing-customers), [contacts CSV](https://support.squarespace.com/hc/en-us/articles/360046485652-The-Contacts-panel), [terms](https://www.squarespace.com/terms-of-service). Shopify: [products CSV](https://help.shopify.com/en/manual/products/import-export/export-products), [theme download](https://help.shopify.com/en/manual/online-store/themes/managing-themes/downloading-themes). WordPress.com: [export page](https://wordpress.com/support/export/) (content as XML; for the whole site it names a migration plugin, or a full backup on Business and Commerce plans). Webflow: [code export](https://help.webflow.com/hc/en-us/articles/33961386739347-How-do-I-export-my-Webflow-site-code), [CMS collection CSV](https://help.webflow.com/hc/en-us/articles/33961290794771-How-do-I-import-content-into-the-Webflow-CMS). Framer's two articles: [no HTML export](https://www.framer.com/help/articles/can-i-export-my-website-to-html-and-self-host-it/), [porting your data](https://www.framer.com/help/articles/porting-your-data-from-framer/). Checked 2026-10-03.
- **[R6] Zoho Mail free plan.** "Up to 5 users", "5 GB mail storage per user", "Custom email for one domain", "IMAP/ POP/ Active Sync not included", "Available only in select data centers". [Zoho Mail pricing](https://www.zoho.com/mail/zohomail-pricing.html). Checked 2026-10-03.
- **[R7] Alex G.'s bill.** His web host's invoice dated Nov 29, 2025: $710.82 for three more years of shared hosting for svsinc.com. Source: Alex G.'s invoice and screen recording (private).
- **[R8] Templates and scraping.** "Squarespace owns the Templates" ([terms](https://www.squarespace.com/terms-of-service)); Showit designs "exclusive to Showit hosting" ([Showit help](https://learn.showit.com/en/articles/4785318-export-wordpress)); a Shopify theme is "licensed only to the store" it was bought for ([theme download help](https://help.shopify.com/en/manual/online-store/themes/managing-themes/downloading-themes), [terms, section 9.6](https://www.shopify.com/legal/terms)); for licensed images, "As a rule, these licenses are not transferable" ([IONOS](https://www.ionos.com/help/websites-stores/organize-websites-and-stores/website-builders-overview-of-export-options/)). Scraping bans: [Squarespace acceptable use](https://www.squarespace.com/acceptable-use-policy), [Webflow acceptable use](https://webflow.com/legal/aup), [Duda terms](https://www.duda.co/legal/terms). Checked 2026-10-03.
- **[R9] HTML5 UP license.** "All of the site templates I create for HTML5 UP are licensed under the Creative Commons Attribution 3.0 License"; "just give HTML5 UP credit for the design". [HTML5 UP license](https://html5up.net/license). Checked 2026-10-03.
- **[R10] Start Bootstrap license.** The templates are MIT licensed ("The MIT License (MIT)", "Copyright (c) 2013-2023 Start Bootstrap LLC", read in the repository of its Clean Blog template; each template carries its own license file). The MIT license asks you to keep the copyright notice. [Example license file](https://github.com/StartBootstrap/startbootstrap-clean-blog/blob/master/LICENSE). Checked 2026-10-03.
- **[R11] BootstrapMade free license.** "You must keep the footer credit line as is: Designed by BootstrapMade"; "You cannot use the free version to create websites for clients or charge for your work." [BootstrapMade license](https://bootstrapmade.com/license/). Checked 2026-10-03.
- **[R12] Astro themes.** Astro's theme catalog lists free and premium themes, and each theme has its own license. Example: Astro Paper is MIT licensed ("MIT License", "Copyright (c) 2023 Sat Naing"). [Astro themes](https://astro.build/themes/), [Astro Paper license](https://github.com/satnaing/astro-paper/blob/main/LICENSE). Checked 2026-10-03.
- **[R13] A bought template's license.** Webflow's paid templates are licensed for "one single End Product" (Webflow's Single-Use License; read the license on the template you buy). [Webflow template licenses](https://templates.webflow.com/template-licenses). Checked 2026-10-03.
