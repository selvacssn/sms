# JIRA-GitHub MCP Server

An MCP server that integrates JIRA and GitHub to provide insights about code changes and related JIRA tickets. This server allows you to track changes pushed to production branches and correlate them with JIRA tickets.

## Features

- Track changes pushed to production branches
- Link commits with JIRA tickets
- Analyze code impact (additions/deletions)
- View pull request information
- Get JIRA ticket details (status, assignee, description)

## Prerequisites

- Node.js 16 or higher
- A GitHub account with a personal access token
- A JIRA account with API token access
- VSCode with Cline extension installed

## Installation

1. Create the MCP directory if it doesn't exist:
   ```bash
   mkdir "%USERPROFILE%\Documents\Cline\MCP"
   ```

2. Clone or copy this repository into the MCP directory:
   ```bash
   cd "%USERPROFILE%\Documents\Cline\MCP"
   git clone [repository-url] jira-github-mcp
   ```

3. Install dependencies:
   ```bash
   cd jira-github-mcp
   npm install
   ```

4. Build the project:
   ```bash
   npm run build
   ```

## Configuration

1. Generate required API tokens:

   ### GitHub Token
   1. Go to https://github.com/settings/tokens
   2. Click "Generate new token (classic)"
   3. Select scopes:
      - `repo` (Full control of private repositories)
      - `read:org` (Read org and team information)
   4. Copy the generated token

   ### JIRA Token
   1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
   2. Click "Create API token"
   3. Give it a name (e.g., "MCP Server")
   4. Copy the generated token

2. Configure the MCP server:

   Open your Cline MCP settings file:
   ```
   %USERPROFILE%\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
   ```

   Add the configuration from `mcp-settings-template.json` to your settings file, replacing the placeholders:
   - `your-github-token-here`: The GitHub personal access token you generated
   - `your-jira-url-here`: Your JIRA instance URL (e.g., https://your-company.atlassian.net)
   - `your-jira-email-here`: Your JIRA account email
   - `your-jira-api-token-here`: The JIRA API token you generated

3. Restart VSCode completely for changes to take effect

## Usage

The server provides the following tool:

### get_production_changes

Gets a summary of changes pushed to production for a specific date.

Parameters:
- `repository`: Repository name in owner/repo format (required)
- `production_branch`: Branch name to check (default: main)
- `date`: Date to check in YYYY-MM-DD format (default: today)

Example usage in Cline:
```
What changes were pushed to production in owner/repo-name today?
```

Example response:
```
Changes pushed to main branch on 2024-02-03 in owner/repo-name:

Overall Impact: +150 -50 lines across 3 commits

Changes by Feature/Ticket:

PROJ-1234:
• JIRA Summary: Add new feature X
• JIRA Status: In Progress
• JIRA Assignee: John Doe
• JIRA Description: Implementing feature X to improve performance...
• Git Summary: feat: Add feature X implementation
• Impact: +100 -30 lines in 2 commits
• Authors: John Doe, Jane Smith
• Changes:
  - [abc1234] feat: Add feature X implementation
    Impact: +80 -20 lines
    Details:
      • Modified class definitions in src/feature-x.ts
      • Updated functions in src/utils.ts
  - [def5678] test: Add tests for feature X
    Impact: +20 -10 lines
    Details:
      • Modified tests in test/feature-x.test.ts
```

## Development

To modify or extend the server:

1. Update source code in `src/index.ts`
2. Rebuild the project:
   ```bash
   npm run build
   ```
3. Restart VSCode to load changes

## Troubleshooting

1. If you see "ERROR: GITHUB_TOKEN environment variable is not set":
   - Check your cline_mcp_settings.json
   - Verify the GitHub token is valid
   - Restart VSCode

2. If you see "ERROR: JIRA environment variables are not set":
   - Check your cline_mcp_settings.json
   - Verify the JIRA URL and credentials
   - Restart VSCode

3. If TypeScript errors occur:
   - Run `npm install` to ensure all dependencies are installed
   - Check that all required types are installed
   - Rebuild with `npm run build`

## License

MIT
