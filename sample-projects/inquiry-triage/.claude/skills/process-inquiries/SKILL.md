---
name: process-inquiries
description: Fetch unprocessed contact-form inquiries from the mobalab WordPress site (stored in Flamingo via Contact Form 7), classify each one, take the right action (notify Slack, draft a reply email, or ignore), and mark it processed so it's never handled twice. Run this when the user asks to process/check/triage the inquiries or contact form submissions.
---

Triage the newest unprocessed inquiries from the mobalab contact form and act on each one so nothing sits unread and nothing gets handled twice.

## Why this matters

The contact form on blog.mobalab.net gets a mix of genuine business inquiries, job applications, and a lot of unsolicited sales pitches (see Step 2). The goal is to make sure real opportunities (service inquiries, job applicants) reach a human fast, while routine noise (staffing sales pitches, generic outreach) doesn't need anyone's attention. When in doubt about a classification, prefer routing to a human (category 6) over silently ignoring — ignoring is only for the categories explicitly called out for it below.

Classification is a judgment call, and judgment calls are sometimes wrong. Rather than let a misjudged "ignore" vanish for good, the borderline ignore categories (3 without a named buyer, 4, and 5-when-not-useful) get bundled into one digest message to marketing at the end of the run, so a human gets a cheap second look without every ignored inquiry needing its own interruption.

Also, this skill may run unattended on a schedule, so it shouldn't blindly work through however many unprocessed inquiries have piled up — a message that's been sitting for weeks may no longer be safe to auto-act on (see the 14-day cutoff in Step 2), and a large stale backlog is itself a signal worth surfacing to a human rather than quietly working through.

## Configuration

IDs and account details that might change over time live here, and only here — the rest of this skill refers back to them by name (e.g. `{MARKETING_SLACK_CHANNEL}`) instead of repeating the raw value, so updating a channel or account only takes one edit.

| Name | Value | What it's for |
|---|---|---|
| `LIST_ABILITY` | `myplugin/list-flamingo-messages` | WordPress ability (via `mcp__bloque__wordpress__mcp-adapter-execute-ability`) that fetches inquiries |
| `MARK_PROCESSED_ABILITY` | `myplugin/mark-flamingo-message-processed` | Same execute-ability tool; marks an inquiry as handled |
| `MARKETING_SLACK_CHANNEL` | `C0AB12CDE34` | Slack channel for genuine business inquiries and useful sales pitches |
| `ADMIN_DM_CHANNEL` | `D0AB12CDE` | Admin's Slack DM channel, for job applications and anything needing a human's judgment |
| `JOBS_ZOHO_ACCOUNT_ID` | `1234567000000001234` | Zoho Mail account ID for the jobs mailbox |
| `JOBS_FROM_ADDRESS` | `jobs@example.com` | From-address for job-application draft replies (mobalab's recruiting team) |

**Company context** (for judging "is this about our service?"): mobalab is a company doing contract development / development-project handovers, and business-process improvement using MCP/AI.

---

## Step 1 — Fetch the latest unprocessed inquiries

Call `mcp-adapter-execute-ability` with:
- `ability_name`: `{LIST_ABILITY}`
- `parameters`: `{"limit": 5, "is_unprocessed_only": true}`

This returns unprocessed inquiries newest-first already limited to 5 — no extra sorting or filtering needed. Each item looks like:

```json
{
  "id": 9085,
  "subject": "...",
  "name": "Jane Doe",
  "email": "jane@example.com",
  "fields": {"your-name": "...", "your-email": "...", "your-subject": "...", "your-message": "the actual inquiry body"},
  "meta": {"date": "2026/09/04", "time": "21:29", ...}
}
```

`id` is what you'll pass back to the mark-processed ability as `message_id`. If the list comes back empty, tell the user there's nothing to process and stop.

---

## Step 2 — Stop at the 14-day cutoff, then classify

Inquiries come back newest-first, so age only increases as you go down the list. Before classifying each inquiry, compare its `meta.date` to today's date. The moment you reach one that's **more than 14 days old, stop** — don't classify, act on, or mark that inquiry (or any inquiry after it in the list, since they're only older) as processed. Leave the rest of the backlog for a human: a job-application acknowledgment or Slack ping that's three weeks late reads very differently than a same-day one, and a backlog that old more likely means something upstream (e.g. the mark-processed step) failed silently than a queue of things to act on now. Note in your final report to the user that you stopped early and why, e.g. "Stopped at #<id> (received <date>, 19 days old) — N older inquiries are still unprocessed."

For every inquiry that passes the age check, read `subject` and `fields.your-message` and assign exactly one category. Judge from the actual content, not just keywords — the examples below are patterns observed in real traffic, not an exhaustive list.

| # | Category | Signal | Action |
|---|----------|--------|--------|
| 1 | Inquiry about our service | Asking about mobalab's own dev/handover/MCP·AI services, pricing, or wanting to work with us | → Slack to marketing |
| 2 | Job application | Applying for or asking about a position at mobalab | → Draft email + Slack DM to admin |
| 3 | Potential M&A offer | Business transfer / acquisition pitch (often vague, "business transfer", "M&A", buyer unnamed) | **Ignore**, unless they name the actual prospective buyer/acquirer — then treat it like category 6 (DM admin) and flag it as M&A in the message, since a named buyer makes it worth a human's attention |
| 4 | Sale of staffing/outsourcing service | Offering to supply engineers/staff or outsourced dev work to mobalab (mobalab as the *client*, not the provider) | **Ignore** |
| 5 | Sale/proposal of other service | Any other unsolicited sales pitch (marketing tools, HR/skill platforms, consulting, etc.) | → Slack to marketing, **only if** you judge it could plausibly help grow mobalab's sales or business; otherwise ignore |
| 6 | Other | Doesn't fit cleanly above, but plausibly a real message from a real person — you're just unsure how to route it | → Slack DM to admin |
| 7 | Junk / bot noise | Random characters, gibberish, or no discernible language/intent in subject and message — clearly an automated probe, not a real person | **Ignore** |

Categories 3, 4, and 7 are the only ones where "ignore" means no Slack message and no email in the moment — just mark processed in Step 3. Reserve category 6 for things that read as a real person's message even if you can't tell which of 1–5 it belongs to; don't use it as a catch-all for spam that just happens to not match a pattern above — that's what category 7 is for.

Three of these "ignore" outcomes aren't fully silent, though: whenever you land on category 3 without a named buyer, category 4, or category 5-judged-not-useful, jot down a one-line note (id, category, subject, and why you didn't act) — you'll fold these into a single end-of-run digest in Step 5. Category 7 (junk/bot noise) doesn't need a note; by definition there's no real content there to second-guess, and including it every run would just bury the borderline cases the digest exists for.

---

## Step 3 — Act on the classification

### Category 1 — Slack to marketing

Call `slack_send_message` with `channel_id: {MARKETING_SLACK_CHANNEL}` and a message like:

```
📩 *Inquiry* (#<id>) — inquiry about our service

<1-2 sentence summary of what they're asking>

---
*From*: <name> <<email>>
*Subject*: <subject>
*Received*: <meta.date> <meta.time>

<full original message, quoted>
```

### Category 2 — Draft reply + DM admin

1. Call `ZohoMail_sendEmail` with:
   - `path_variables.accountId`: `{JOBS_ZOHO_ACCOUNT_ID}`
   - `body.mode`: `"draft"`
   - `body.fromAddress`: `{JOBS_FROM_ADDRESS}`
   - `body.toAddress`: the applicant's email
   - `body.subject`: `"Re: <their subject>"` (or a sensible default if their subject is empty)
   - `body.content`: a short acknowledgment, e.g.:
     ```
     Dear <name>,

     Thank you very much for your interest in a position at mobalab. We've
     received your application and will follow up with you after reviewing
     it. Thank you for your patience in the meantime.

     mobalab Recruiting Team
     ```
   - `body.mailFormat`: `"plaintext"`
2. Call `slack_send_message` with `channel_id: {ADMIN_DM_CHANNEL}` and a message telling admin a draft is waiting:
   ```
   💼 *Job application* (#<id>) — a draft reply is waiting in the jobs@example.com drafts folder. Please review and send it.

   *From*: <name> <<email>>
   *Subject*: <subject>

   <full original message, quoted>
   ```

### Category 3 (buyer disclosed) or Category 6 — Slack DM to admin

Call `slack_send_message` with `channel_id: {ADMIN_DM_CHANNEL}`:

```
❓ *Needs a human* (#<id>) — <one-line reason this needs a human: e.g. "M&A approach (prospective buyer disclosed)" or the reason classification was held>

*From*: <name> <<email>>
*Subject*: <subject>

<full original message, quoted>
```

### Category 5 (judged useful) — Slack to marketing

Same format as category 1, but the summary line should say why you think it could help increase sales, e.g. `📩 *Inquiry* (#<id>) — a proposal that could be useful for sales`.

### Categories 3 (buyer not disclosed), 4, 5 (judged not useful), and 7 — no message

Skip straight to Step 4. (For 3, 4, and 5, make sure you've jotted the digest note from Step 2 before moving on.)

---

## Step 4 — Mark the inquiry processed

For every inquiry handled in Step 3 — including the ones you ignored — call `mcp-adapter-execute-ability` with:
- `ability_name`: `{MARK_PROCESSED_ABILITY}`
- `parameters`: `{"message_id": <id>, "status": "done", "mark_spam": <true if category 7, otherwise false>}`

`mark_spam` flags category 7 (junk / bot noise) using Flamingo's native spam status, so it can be filtered out downstream — set it `true` only for category 7, `false` for every other category (1–6). Note this changes the message's `post_status` to `flamingo-spam`, so it will no longer appear in `list-flamingo-messages` results at all (not just excluded when `is_unprocessed_only: true`).

Only use `"status": "failed"` if a required action in Step 3 (the Slack message or the email draft) actually errored out — don't mark an inquiry done if the action it needed didn't go through; report the failure to the user instead so they can retry.

Process inquiries one at a time (classify → act → mark done) rather than batching all the marking at the end, so a failure partway through doesn't leave earlier inquiries unmarked.

---

## Step 5 — Send one digest of the ignored-but-maybe-useful ones

Once you're done working through inquiries (whether the list ran out or you stopped at the 14-day cutoff), check whether you collected any notes in Step 2 — that's category 3 without a named buyer, category 4, or category 5-judged-not-useful.

If you collected at least one note, send **exactly one** `slack_send_message` to `{MARKETING_SLACK_CHANNEL}` for the whole run — never one per ignored inquiry, since the point is a quick scannable digest a human can skim in a few seconds, not extra interruptions:

```
🗂 *Set aside this run* (worth a quick double-check)

#<id> [<category label>] <subject> — <one-line reason for not acting>
#<id> [<category label>] <subject> — <one-line reason for not acting>
...
```

If you collected no notes this run — nothing landed in those three categories — skip this message entirely. An empty or near-empty digest every run just trains people to stop reading it.
