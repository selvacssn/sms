#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError
} from '@modelcontextprotocol/sdk/types.js';
import { Octokit } from '@octokit/rest';
import JiraClient from 'jira-client';
import * as fs from 'fs';
import moment from 'moment';

interface JiraDetails {
  summary: string;
  status: string;
  assignee: string;
  description: string;
}

interface CommitSummary {
  ticket: string;
  description: string;
  authors: Set<string>;
  commits: number;
  additions: number;
  deletions: number;
  pullRequests: Set<string>;
  jiraDetails?: JiraDetails;
  commitDetails: Array<{
    sha: string;
    message: string;
    additions: number;
    deletions: number;
    files: Array<{
      filename: string;
      additions: number;
      deletions: number;
      changes: string[];
    }>;
  }>;
}

class MCPServer {
  private server: any;
  private octokit: Octokit | undefined;
  private jira?: JiraClient;

  constructor() {
    // Initialize server
    this.server = new Server({
      name: "jira-github-mcp",
      version: "1.0.0"
    }, {
      capabilities: {}
    });

    // Initialize JIRA client if credentials are provided
    const jiraUrl = process.env.JIRA_URL;
    const jiraUsername = process.env.JIRA_USERNAME;
    const jiraToken = process.env.JIRA_API_TOKEN;

    if (jiraUrl && jiraUsername && jiraToken) {
      this.jira = new JiraClient({
        protocol: 'https',
        host: jiraUrl.replace('https://', ''),
        username: jiraUsername,
        password: jiraToken,
        apiVersion: '2',
        strictSSL: true
      });
    }

    // Set up request handlers
    this.setupHandlers();

    // Handle errors
    process.on('uncaughtException', (error: Error) => {
      console.error('Uncaught exception:', error);
    });

    process.on('unhandledRejection', (error: unknown) => {
      console.error('Unhandled rejection:', error);
    });

  }

  private setupHandlers() {
    // List available tools
    this.server.on('tools/list', async () => ({
      tools: [{
        name: 'get_production_changes',
        description: 'Get a summary of changes pushed to production for a specific date',
        inputSchema: {
          type: 'object',
          properties: {
            repository: {
              type: 'string',
              description: 'Repository name in owner/repo format'
            },
            production_branch: {
              type: 'string',
              description: 'Name of the production branch (e.g., main, master, production)',
              default: 'main'
            },
            date: {
              type: 'string',
              description: 'Date to check commits for (YYYY-MM-DD format). Defaults to today.',
              pattern: '^\d{4}-\d{2}-\d{2}$'
            }
          },
          required: ['repository']
        }
      }]
    }));

    // Handle tool calls
    this.server.on('tools/call', async (request: { params: { name: string; arguments: any } }) => {
      if (request.params.name !== 'get_production_changes') {
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
      }
      return this.handleGetProductionChanges(request.params.arguments);
    });
  }

  private extractTicketNumber(message: string): string {
    const patterns = [
      /\b([A-Z]+-\d+)\b/, // e.g., PROJ-1234
      /#(\d+)/ // e.g., #1234 for pull requests
    ];

    for (const pattern of patterns) {
      const match = message.match(pattern);
      if (match) return match[1];
    }

    return 'Other';
  }

  private async getJiraDetails(ticketId: string): Promise<JiraDetails | undefined> {
    if (!this.jira || !ticketId || ticketId === 'Other') {
      return undefined;
    }

    try {
      const issue = await this.jira.findIssue(ticketId);
      return {
        summary: issue.fields.summary,
        status: issue.fields.status.name,
        assignee: issue.fields.assignee ? issue.fields.assignee.displayName : 'Unassigned',
        description: issue.fields.description || 'No description available'
      };
    } catch (error) {
      console.error(`Error fetching JIRA details for ${ticketId}:`, error);
      return undefined;
    }
  }

  private summarizeChanges(files: Array<{ filename: string; additions: number; deletions: number; patch?: string }>): string[] {
    const changes: string[] = [];
    const fileTypes = new Map<string, { count: number; examples: string[] }>();
    
    for (const file of files) {
      const ext = file.filename.split('.').pop()?.toLowerCase() || 'unknown';
      const type = fileTypes.get(ext) || { count: 0, examples: [] };
      type.count++;
      if (type.examples.length < 3) {
        type.examples.push(file.filename);
      }
      fileTypes.set(ext, type);

      if (file.patch) {
        if (file.patch.includes('class ')) changes.push(`Modified class definitions in ${file.filename}`);
        if (file.patch.includes('function ') || file.patch.includes('def ')) changes.push(`Updated functions in ${file.filename}`);
        if (file.patch.includes('import ')) changes.push(`Changed imports in ${file.filename}`);
        if (file.patch.includes('test')) changes.push(`Modified tests in ${file.filename}`);
        if (file.patch.includes('config')) changes.push(`Updated configuration in ${file.filename}`);
      }
    }

    for (const [ext, { count, examples }] of fileTypes) {
      if (count === 1) {
        changes.push(`Modified ${examples[0]}`);
      } else {
        changes.push(`Modified ${count} ${ext} files (e.g., ${examples.join(', ')})`);
      }
    }

    return Array.from(new Set(changes));
  }

  private async handleGetProductionChanges(args: any) {
    const [owner, repo] = args.repository.split('/');
    const branch = args.production_branch || 'main';
    const targetDate = args.date ? moment(args.date) : moment();
    const startDate = targetDate.clone().startOf('day');
    const endDate = targetDate.clone().endOf('day');

    try {
      if (!this.octokit) {
        throw new McpError(ErrorCode.InternalError, "GitHub client not initialized");
      }

      // Verify repository access
      await this.octokit.repos.get({ owner, repo });

      // Fetch commits
      const { data: commits } = await this.octokit.repos.listCommits({
        owner,
        repo,
        sha: branch,
        since: startDate.toISOString(),
        until: endDate.toISOString()
      });

      if (commits.length === 0) {
        return {
          content: [{
            type: "text",
            text: `No changes pushed to ${branch} branch on ${targetDate.format('YYYY-MM-DD')} in ${owner}/${repo}.`
          }]
        };
      }

      // Process commits
      const summaries = new Map<string, CommitSummary>();
      let totalAdditions = 0;
      let totalDeletions = 0;

      for (const commit of commits) {
        const { data: details } = await this.octokit.repos.getCommit({
          owner,
          repo,
          ref: commit.sha
        });

        const message = commit.commit.message.split('\n')[0];
        const ticket = this.extractTicketNumber(message);
        const author = commit.commit.author?.name || 'Unknown';
        const additions = details.stats?.additions || 0;
        const deletions = details.stats?.deletions || 0;

        totalAdditions += additions;
        totalDeletions += deletions;

        const fileChanges = details.files?.map(file => ({
          filename: file.filename,
          additions: file.additions || 0,
          deletions: file.deletions || 0,
          changes: this.summarizeChanges([file])
        })) || [];

        if (!summaries.has(ticket)) {
          const jiraDetails = await this.getJiraDetails(ticket);
          summaries.set(ticket, {
            ticket,
            description: message,
            authors: new Set([author]),
            commits: 1,
            additions,
            deletions,
            pullRequests: new Set(),
            jiraDetails,
            commitDetails: [{
              sha: commit.sha.substring(0, 7),
              message,
              additions,
              deletions,
              files: fileChanges
            }]
          });
        } else {
          const summary = summaries.get(ticket)!;
          summary.authors.add(author);
          summary.commits++;
          summary.additions += additions;
          summary.deletions += deletions;
          summary.commitDetails.push({
            sha: commit.sha.substring(0, 7),
            message,
            additions,
            deletions,
            files: fileChanges
          });
          if (message.toLowerCase().includes('pull request')) {
            summary.description = message;
            summary.pullRequests.add(message.match(/#\d+/)?.[0] || '');
          }
        }
      }

      // Format summary
      let result = `Changes pushed to ${branch} branch on ${targetDate.format('YYYY-MM-DD')} in ${owner}/${repo}:\n\n`;
      result += `Overall Impact: +${totalAdditions} -${totalDeletions} lines across ${commits.length} commits\n\n`;
      result += `Changes by Feature/Ticket:\n`;

      const sortedSummaries = Array.from(summaries.values())
        .sort((a, b) => (b.additions + b.deletions) - (a.additions + a.deletions));

      for (const summary of sortedSummaries) {
        result += `\n${summary.ticket}:\n`;
        if (summary.jiraDetails) {
          result += `• JIRA Summary: ${summary.jiraDetails.summary}\n`;
          result += `• JIRA Status: ${summary.jiraDetails.status}\n`;
          result += `• JIRA Assignee: ${summary.jiraDetails.assignee}\n`;
          result += `• JIRA Description: ${summary.jiraDetails.description.split('\n')[0]}...\n`;
        }
        result += `• Git Summary: ${summary.description}\n`;
        result += `• Impact: +${summary.additions} -${summary.deletions} lines in ${summary.commits} commit${summary.commits > 1 ? 's' : ''}\n`;
        result += `• Authors: ${Array.from(summary.authors).join(', ')}\n`;
        if (summary.pullRequests.size > 0) {
          result += `• Pull Requests: ${Array.from(summary.pullRequests).join(', ')}\n`;
        }
        result += `• Changes:\n`;
        for (const commit of summary.commitDetails) {
          result += `  - [${commit.sha}] ${commit.message}\n`;
          result += `    Impact: +${commit.additions} -${commit.deletions} lines\n`;
          if (commit.files.length > 0) {
            const changes = commit.files.flatMap(f => f.changes);
            const uniqueChanges = Array.from(new Set(changes));
            result += `    Details:\n`;
            for (const change of uniqueChanges) {
              result += `      • ${change}\n`;
            }
          }
        }
      }

      return {
        content: [{
          type: "text",
          text: result
        }]
      };

    } catch (error: any) {
      throw new McpError(
        ErrorCode.InternalError,
        `Error processing changes: ${error.message}`
      );
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('JIRA-GitHub MCP server running on stdio');
  }
}

new MCPServer().run().catch(console.error);
