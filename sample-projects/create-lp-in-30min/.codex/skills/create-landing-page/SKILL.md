---
name: create-landing-page
description: Create complete single-file HTML/Tailwind landing pages from briefs, URLs, or product context, with visual assets, responsive implementation, Bloque shared-file staging, Playwright visual review, screenshot inspection, Netlify publishing from staged files after approval, and revision loops. Use when the user asks Codex to make, design, build, iterate, stage, publish, deploy, or review a landing page for a product, service, app, company, event, campaign, or offer.
---

# Create Landing Page

## Overview

Create a production-ready landing page from user-provided product context. Gather enough information once, then independently design, create visual assets, implement, stage to Bloque, review visually, fix issues, ask the user for feedback, and publish to Netlify from staged files only after approval.

## Workflow

1. Gather necessary information from the user or supplied files.
2. Design.
3. Create visual assets.
4. Implement.
5. Copy files to Bloque.
6. Review. If issues are found, fix them and repeat from step 5 without incrementing `<n>`.
7. Ask the user for feedback. If they request changes, increment `<n>` and repeat from step 4.
8. Publish to Netlify from `/shared/create-lp/<n>/` only after the user approves the reviewed page.

After step 1, avoid asking the user for decisions unless a missing detail blocks progress or a choice carries meaningful product, legal, or brand risk.

## Step 1: Gather Information

If the user passes a file path, read it first and treat it as the brief. Ask for missing essentials only after reading all supplied files.

Ask for unclear or missing essentials only. Required inputs:

- Product, service, company, event, campaign, or offer name.
- Product description and core value proposition.
- Target users or buyers.
- What to include, add, delete, or modify from the baseline landing page structure.

Use this baseline when the user has no preferred structure:

1. Header with logo and navigation.
2. Hero with headline, subheadline, and CTA.
3. Three benefits.
4. How to use in three steps.
5. Three customer voices.
6. Plans.
7. Five FAQs.
8. Footer with CTA.

Optional inputs to ask about only when useful: brand colors, logo or existing assets, preferred tone, proof points, pricing, primary CTA URL, competitors, and keywords for design research.

If the brief references a live URL for pricing, plans, product claims, or proof points, verify the current public content before writing those details. Prefer official product pages. If the URL cannot be reached, use only details from the brief and say what could not be verified.

## Step 2: Design

Search for 3 to 5 landing pages for each of two relevant keyword groups using Lazyweb MCP tools when available. Choose keyword groups from the user's product category and target-user/problem space. If the user supplied explicit keywords, use those.

Extract useful patterns, then combine the good parts without copying a specific page:

- Page structure and conversion flow.
- Messaging hierarchy.
- Visual language, section rhythm, and trust elements.
- CTA placement and pricing/FAQ treatment.

Make concrete design decisions before implementation: audience-specific tone, color palette, typography feel, imagery direction, section order, and responsive behavior.

Use the frontend design rules from the active developer instructions. In particular: build the actual landing page, not a generic marketing placeholder; use visual assets; avoid nested cards, decorative blobs/orbs, one-note palettes, cramped text, and text that can overflow at mobile widths.

## Step 3: Create Visual Assets

Create visual assets that materially improve the page, such as hero product visuals, contextual product scenes, customer/user illustrations, product UI mockups, or feature visuals. Do not use generated images for simple icons when an icon library or CSS is sufficient.

Prefer generated raster images for illustrative or photographic assets. Keep generated source images at or below 1600 x 1200 and output them to `./generated-images`.

For precise product-dashboard or UI visuals, it is acceptable to build a source SVG/HTML mockup and rasterize it into `./out/<n>/images/` when that will be clearer, more legible, or more controllable than an AI-generated bitmap.

## Step 4: Implement

Create the page as HTML + Tailwind CSS with minimal JavaScript. Use CDN links for external libraries. Put the HTML, CSS, and JS in one `index.html` file.

Output to `./out/<n>/`, where `<n>` starts at `1`. Increment `<n>` only when the user requests changes after review/feedback. The typical structure is:

```text
./out/1/
├── index.html
└── images/
    ├── resized-image-1.png
    └── resized-image-2.jpg
```

Resize or rasterize visual assets into `./out/<n>/images/` and reference those files from `index.html`. Keep the page fully responsive and verify text does not overlap or overflow at mobile and desktop sizes.

## Step 5: Copy Files to Bloque

Use the `bloque-shared-file-staging` skill to upload the complete `./out/<n>/` directory to `/shared/create-lp/<n>/`.

Respect the Bloque boundary: Bloque is an MCP gateway, so stdio-based MCP servers run in Bloque infrastructure rather than on the local machine. Those tools cannot access local files directly. Only files under Bloque's `/shared` directory are visible to Bloque-hosted MCP tools.

When crossing this boundary:

- Create parent directories under `/shared` one level at a time if recursive creation fails.
- Use `bloque_get_upload_url` plus HTTP PUT to upload local files into `/shared`.
- Use `bloque_get_download_url` plus HTTP GET to retrieve files from `/shared`.
- Use Bloque filesystem tools only for files and directories already under `/shared`.
- Stage every HTML asset needed for review, including images, CSS, JS, and generated media, before invoking Bloque-hosted filesystem or review tools.
- If local `curl` fails because of sandboxed DNS or network restrictions, rerun the same transfer command with the required escalation.
- Verify the staged tree with Bloque filesystem tools before review.

## Step 6: Review

Use the `web-page-visual-review` skill after staging. For Bloque-hosted Playwright, navigate to `file:///shared/create-lp/<n>/index.html`; do not try to open a local `file:///Users/...` path because Bloque-hosted tools cannot see local files.

Check at minimum:

- Desktop and mobile layout.
- Broken images or missing assets.
- Console errors.
- Text overlap, clipping, or low contrast.
- CTA visibility and section completeness.

Capture desktop and mobile screenshots to `/shared/create-lp/<n>/`, download them locally, and inspect pixels. Also run quick DOM checks for horizontal overflow (`scrollWidth > innerWidth`) and image load status (`naturalWidth > 0`). Treat Tailwind CDN production warnings as expected when using CDN Tailwind, but do not ignore other console warnings without inspection.

If the review finds issues, fix them in the same `./out/<n>/` directory, then repeat from step 5 without incrementing `<n>`.

## Step 7: Feedback Loop

Ask the user for feedback after the page passes review. If the user requests changes, increment `<n>` and repeat from step 4, carrying forward the latest approved direction and assets.

Treat "approved", "ship it", "publish", "deploy", "make it public", or equivalent confirmation after review as approval to continue to Step 8. If the user gives no approval, finish with the local path, Bloque shared destination, and review screenshots.

## Step 8: Publish to Netlify

Use Netlify tools only after approval. Netlify tools do not have access to the local filesystem; deploy from the staged Bloque path `/shared/create-lp/<n>/`, not from `./out/<n>/`.

Before deploying:

- Verify `/shared/create-lp/<n>/` contains the latest approved `index.html` and all referenced assets.
- Find the target Netlify site ID from local context or Netlify project tools when possible.
- Never assume the user wants a new Netlify site. If no site ID is available or multiple matching sites exist, ask the user which existing site to use or whether to create a new site.
- If the user explicitly wants a new site, create or select the project using Netlify project tools, then deploy.

Deploy with `netlify_deploy_services_updater` operation `deploy-site`. Set `deployDirectory` to the absolute server-side staged directory `/shared/create-lp/<n>/` and pass `siteId` when known.

After deploying:

- Use Netlify deploy reader tools to confirm deploy status and public URL when available.
- Open the public URL with Playwright when feasible and check that the published page loads, the hero image renders, and there are no obvious console errors.
- Finish with the local path, Bloque shared path, Netlify URL, and any review notes.
