# Create a Landing Page in 30 Minutes
## Prerequisites

* Bloque account
* Netlify personal access token (PAT)
* OpenAI API key
* Lazyweb's token

## Setup (one time)
### Get your credentials of Netlify, OpenAI, and Lazyweb

Get a Netlify personal access token by following the "Authentication" section of the page below:
[Get started with the Netlify API | Netlify Docs](https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/#authentication)

Next, get an OpenAI API key. See the following page for details:
[Where do I find my OpenAI API Key? | OpenAI Help Center](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)

Finally, Go to the page below and copy the token shown:
[Install Lazyweb MCP](https://www.lazyweb.com/mcp-install)

### Set up MCP servers on Bloque

1. Sign up for Bloque if you haven't already
2. Go to "Search" from the left menu
3. Install the following 4 MCP servers:
    * Lazyweb: Replace `<YOUR_TOKEN>` with your Lazyweb's token on the Install dialog
    * Netlify: Under "Environment Variables" section of the Install dialog, enter your Netlify personal access token in `NETLIFY_PERSONAL_ACCESS_TOKEN`
    * filesystem
    * Playwright
4. Go to "API Keys" from the bottom-left menu, create an API key, and save it.

### Project directory

1. Copy `.env.example` to `.env`
2. Replace the placeholder values in `.env` with your Bloque API key and OpenAI API key

## Create!

1. Copy `input-template.md` to a filename of your choice
2. Edit the file
3. Run `codex.sh`, which sets the environment variables and launches Codex CLI
4. Type `$` to invoke a skill, and choose "Create Landing Page", and pass the file you created in step 1

That's it!
