---
name: create-landing-page
description: Create complete single-file HTML/Tailwind landing pages with generated images, responsive implementation, Bloque shared-file staging, visual review, and revision loops. Use when the user asks Codex to make, design, build, iterate, or review a landing page for a product, service, app, company, event, campaign, or offer.
---

# Create Landing Page

## Overview

Create a production-ready landing page from user-provided product context. Gather enough information once, then independently design, generate images, implement, stage to Bloque, review visually, fix issues, and ask the user for feedback.

## Workflow

1. Gather necessary information from the user.
2. Design.
3. Create images.
4. Implement.
5. Copy files to Bloque.
6. Review. If issues are found, fix them and repeat from step 5 without incrementing `<n>`.
7. Ask the user for feedback. If they request changes, increment `<n>` and repeat from step 4. If no changes are requested, finish.

After step 1, avoid asking the user for decisions unless a missing detail blocks progress or a choice carries meaningful product, legal, or brand risk.

## Step 1: Gather Information

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

## Step 2: Design

Search for 3 to 5 landing pages for each of two relevant keyword groups using Lazyweb MCP tools when available. Choose keyword groups from the user's product category and target-user/problem space. If the user supplied explicit keywords, use those.

Extract useful patterns, then combine the good parts without copying a specific page:

- Page structure and conversion flow.
- Messaging hierarchy.
- Visual language, section rhythm, and trust elements.
- CTA placement and pricing/FAQ treatment.

Make concrete design decisions before implementation: audience-specific tone, color palette, typography feel, imagery direction, section order, and responsive behavior.

## Step 3: Create Images

Create raster images using GPT-Image-2 through the available image generation workflow/tooling. Keep generated source images at or below 1600 x 1200. Output generated image files to `./generated-images`.

Generate only images that materially improve the page, such as hero product visuals, contextual product scenes, customer/user illustrations, or feature visuals. Do not use generated images for simple icons when an icon library or CSS is sufficient.

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

Resize generated images into `./out/<n>/images/` and reference those resized files from `index.html`. Keep the page fully responsive and verify text does not overlap or overflow at mobile and desktop sizes.

## Step 5: Copy Files to Bloque

Use the `bloque-shared-file-staging` skill to upload the complete `./out/<n>/` directory to `/shared/create-lp/<n>/`.

Respect the Bloque boundary: Bloque is an MCP gateway, so stdio-based MCP servers run in Bloque infrastructure rather than on the local machine. Those tools cannot access local files directly. Only files under Bloque's `/shared` directory are visible to Bloque-hosted MCP tools.

When crossing this boundary:

- Use `bloque_get_upload_url` plus HTTP PUT to upload local files into `/shared`.
- Use `bloque_get_download_url` plus HTTP GET to retrieve files from `/shared`.
- Use Bloque filesystem tools only for files and directories already under `/shared`.
- Stage every HTML asset needed for review, including images, CSS, JS, and generated media, before invoking Bloque-hosted filesystem or review tools.

## Step 6: Review

Use the `web-page-visual-review` skill against the staged or local `./out/<n>/index.html`. Check at minimum:

- Desktop and mobile layout.
- Broken images or missing assets.
- Console errors.
- Text overlap, clipping, or low contrast.
- CTA visibility and section completeness.

If the review finds issues, fix them in the same `./out/<n>/` directory, then repeat from step 5 without incrementing `<n>`.

## Step 7: Feedback Loop

Ask the user for feedback after the page passes review. If the user requests changes, increment `<n>` and repeat from step 4, carrying forward the latest approved direction and assets. If the user has no changes, finish with the local path and Bloque shared destination.
