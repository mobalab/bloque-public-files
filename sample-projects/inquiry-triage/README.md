# Auto-triage contact form inquiries to Slack/email
## Prerequisites

* A Bloque account
* A WordPress site with Contact Form 7 and Flamingo (for storing submissions) active
* A Slack app's client ID and client secret
* A Zoho Mail account
* Claude Code

## Setup (one time)

### WordPress side

This sample uses a dedicated WordPress Ability (`wordpress-ability/flamingo-abilities.php`)
to list inquiries and mark them processed. First, follow the doc below to
set up the MCP Adapter plugin and the Abilities API foundation on WordPress.
[WordPress MCP | Bloque Documentation](https://docs.bloque.run/docs/integrations/wordpress-mcp)

Once that's in place, upload `wordpress-ability/flamingo-abilities.php` to
your WordPress site's `wp-content/mu-plugins/`. This makes the two Abilities
`myplugin/list-flamingo-messages` and `myplugin/mark-flamingo-message-processed`
available over MCP.

### Get your Slack credentials

Follow the doc below to create the Slack app Bloque will use, and get its
client ID and client secret.
[Create a Slack app | Bloque Documentation](https://docs.bloque.run/docs/integrations/create-slack-app)

### Set up the MCP servers on Bloque

1. Sign up for [Bloque](https://bloque.run) if you haven't already
2. Go to the [sample Hub](https://bloque.run/to/demo/hub/98bac5bd-a5e5-416e-95af-38d6f1480fdc) and click "Install Hub"
3. On the [MCP servers screen](https://bloque.run/mcp-servers), open each server's "Edit" and fill in what's needed under "Configuration":
    * WordPress: the Application Password (and anything else) from the doc above
    * Slack: your Slack app's "Client ID" and "Client Secret"
    * Zoho Mail: the credentials from the connection flow
4. Go to [API Keys](https://bloque.run/api-keys) and create/save one

### Project directory

1. Copy `.env.example` to `.env`
2. Fill in your Bloque API key in `.env`

### Replace the placeholder values in the skill

`SKILL.md` contains placeholder values — replace them with your own before
using this for real.

You can edit them by hand, or ask the `skill-creator` skill to do it for
you, e.g.:

```
/skill-creator process-inquiries is a sample skill someone gave me. I want
to replace the placeholder values inside it with values for my own
project — tell me what you need from me.
```

If editing by hand, here's what to change (Configuration table in
`.claude/skills/process-inquiries/SKILL.md`, around line 20):

* `MARKETING_SLACK_CHANNEL`: Slack channel ID for general inquiries
* `ADMIN_DM_CHANNEL`: Slack DM channel ID for inquiries that need a human's judgment
* `JOBS_ZOHO_ACCOUNT_ID` / `JOBS_FROM_ADDRESS`: the Zoho Mail account ID and from-address used for job-application draft replies

`LIST_ABILITY` / `MARK_PROCESSED_ABILITY` (`myplugin/list-flamingo-messages` /
`myplugin/mark-flamingo-message-processed`) must match the Ability names
registered in `wordpress-ability/flamingo-abilities.php`. If you rename the
`myplugin/` namespace, update both the PHP file and `SKILL.md` to match.

## Using it

### Run it manually

Start Claude Code and invoke the `process-inquiries` skill:
```
./claude-env.sh
/process-inquiries
```

### Run it on a schedule

The simplest way to run this on a schedule is cron on your own machine.

For something more managed, Claude Code has built-in support for running on
a schedule via GitHub Actions — no extra server needed if you already have a
GitHub account:
[Run on a schedule | Claude Code Docs](https://code.claude.com/docs/en/github-actions#run-on-a-schedule)
