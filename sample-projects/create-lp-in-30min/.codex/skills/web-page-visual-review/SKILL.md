---
name: web-page-visual-review
description: Inspect rendered web pages for visual quality, layout, asset loading, console errors, and accessibility-oriented contrast problems. Use when Codex needs to open an HTML file, local/staged page, or URL with Playwright; capture screenshots; download or inspect screenshot artifacts; review AI-generated landing pages and web apps for low-contrast text, broken images, overflow, overlap, awkward spacing, or other visual regressions.
---

# Web Page Visual Review

## Overview

Review a web page as rendered, not just as source code. Prefer screenshots and browser observations over assumptions, and report concrete visual issues with enough location context that a developer can fix them.

## Workflow

1. Identify the page target.
   - For a server-side Bloque Playwright review, use a URL that the Bloque browser can access, such as `file:///shared/<path>/index.html` or an HTTPS URL.
   - If the source is local but Playwright runs on Bloque, stage the local files into `/shared` first, using the `bloque-shared-file-staging` skill when available.

2. Open the page with Playwright.
   - Navigate to the target.
   - Confirm the page title and final URL.
   - Collect console messages, especially errors and warnings.

3. Capture screenshots.
   - Save a full-page screenshot to a clear `/shared/...` path when using Bloque-hosted Playwright.
   - Use PNG unless the user requests another format.
   - For responsive pages or when the user asks for quality review, also check at least one mobile viewport and one desktop viewport when feasible.

4. Download or open the screenshot for inspection.
   - For `/shared` screenshots, call `bloque_get_download_url`, download with HTTP `GET`, and save the image locally.
   - Use local image viewing for pixel inspection. Do not rely only on DOM snapshots.

5. Inspect visual quality.
   - Check for low-contrast text, especially AI-generated pages with light text on light backgrounds or dark text on dark backgrounds.
   - Check hero, section headings, body copy, buttons, cards, nav, pricing tables, FAQ rows, forms, and footer.
   - Check image rendering, missing assets, broken icons, unexpected cropping, text overlap, horizontal overflow, awkward wrapping, clipped controls, and excessive blank space.

6. Run targeted automated checks when useful.
   - Use Playwright evaluation to sample computed text color and nearby background color for suspicious elements.
   - Treat automated contrast output as advisory: transparent layers, gradients, images, pseudo-elements, and overlays can produce false positives or false negatives.
   - Let the screenshot decide final severity when automation and pixels disagree.

7. Report findings.
   - Lead with real problems, ordered by visual severity.
   - Include the screenshot path, page URL, viewport, and console status.
   - Mention if no issues were found, and note any residual risks such as only testing one viewport.

## Bloque Pattern

When Playwright runs on Bloque and the page is under `/shared`:

1. Navigate to `file:///shared/<dir>/index.html`.
2. Save the screenshot to `/shared/<name>-review.png`.
3. Download it locally with `bloque_get_download_url` plus `curl`.
4. If local `curl` fails because of sandboxed DNS or network access, rerun with the required approval.
5. Verify screenshot dimensions or file metadata before reviewing so the user knows whether it is full-page or viewport-only.

## Contrast Guidance

Flag text that is hard to read, even if it may technically pass in some contexts. Common failure modes:

- Dark navy text on dark teal, blue, or black sections.
- Pale gray text on white or very light cards.
- White text over bright image regions without a sufficient overlay.
- Accent-colored labels with tiny font sizes.
- Disabled-looking buttons used as active calls to action.

Prefer specific repair suggestions such as "change this heading to white" or "darken the card body text" instead of vague advice like "improve contrast."

## Reporting Template

Use a concise report:

- Page tested: `<url>`
- Screenshot: `<local path>` and `/shared/...` when applicable
- Console: `<errors/warnings summary>`
- Findings: ordered list of visual or contrast issues
- Notes: responsive coverage, asset loading, and anything not tested

Avoid overstating automated results. If a contrast script produced false positives, say that manual screenshot inspection was the deciding check.
