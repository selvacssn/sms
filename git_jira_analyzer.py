from ag2 import AGI, Tool, system_message
import re
from jira import JIRA
import os
from github import Github
from urllib.parse import urlparse

class GitJiraAnalyzer(AGI):
    def __init__(self):
        super().__init__()
        self.jira = None
        self.github = None
        
        # Get JIRA credentials from environment variables
        self.jira_token = os.getenv('JIRA_API_TOKEN')
        self.jira_username = os.getenv('JIRA_USERNAME')
        self.jira_url = os.getenv('JIRA_URL')
        
        # Get GitHub token from environment variable
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        if not all([self.jira_token, self.jira_username, self.jira_url]):
            raise ValueError("Missing JIRA credentials in environment variables. Please set JIRA_API_TOKEN, JIRA_USERNAME, and JIRA_URL")
        
        if not self.github_token:
            raise ValueError("Missing GitHub token. Please set GITHUB_TOKEN environment variable")
            
        # Initialize GitHub client
        self.github = Github(self.github_token)
        
    def get_repo_from_url(self, repo_url: str) -> tuple:
        """Extract owner and repo name from GitHub URL"""
        path_parts = urlparse(repo_url).path.strip('/').split('/')
        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]
        raise ValueError("Invalid GitHub repository URL")
        
    @Tool
    def get_commit_summary(self, repo_url: str) -> str:
        """Get summary of recent commits from the repository using GitHub API"""
        try:
            # Extract owner and repo name from URL
            owner, repo_name = self.get_repo_from_url(repo_url)
            
            # Get repository using PyGithub
            github_repo = self.github.get_user(owner).get_repo(repo_name)
            
            commits = []
            for commit in github_repo.get_commits()[:10]:  # Last 10 commits
                commits.append({
                    'hash': commit.sha[:7],
                    'message': commit.commit.message,
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date.isoformat(),
                    'files': [file.filename for file in commit.files]
                })
            return commits
        except Exception as e:
            return f"Error accessing repository: {str(e)}"

    @Tool
    def extract_jira_id(self, commit_message: str) -> str:
        """Extract JIRA ID from commit message using regex"""
        # Pattern matches common JIRA ID formats like PROJECT-123
        pattern = r'([A-Z]+-\d+)'
        match = re.search(pattern, commit_message)
        return match.group(1) if match else None

    @Tool
    def get_jira_story(self, jira_id: str) -> dict:
        """Get JIRA story details using the JIRA API"""
        try:
            if not self.jira:
                # Initialize JIRA client with environment variables
                self.jira = JIRA(
                    server=self.jira_url,
                    basic_auth=(self.jira_username, self.jira_token)
                )
            
            issue = self.jira.issue(jira_id)
            return {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description,
                'status': str(issue.fields.status),
                'type': str(issue.fields.issuetype)
            }
        except Exception as e:
            return f"Error fetching JIRA story: {str(e)}"

    @Tool
    def analyze_changes(self, commit_data: dict, jira_data: dict) -> dict:
        """Analyze if the changes are relevant to the JIRA story"""
        # Basic relevance analysis
        relevance_score = 0
        reasons = []
        
        # Check if commit message contains keywords from JIRA story
        keywords = set(jira_data['summary'].lower().split() + 
                      (jira_data['description'].lower().split() if jira_data['description'] else []))
        
        commit_words = commit_data['message'].lower().split()
        matching_keywords = set(commit_words) & keywords
        
        if matching_keywords:
            relevance_score += len(matching_keywords) * 0.2
            reasons.append(f"Found matching keywords: {', '.join(matching_keywords)}")
        
        # Analyze file changes
        for file_path in commit_data['files']:
            if any(keyword in file_path.lower() for keyword in keywords):
                relevance_score += 0.3
                reasons.append(f"File path {file_path} matches story keywords")
        
        return {
            'relevance_score': min(relevance_score, 1.0),  # Normalize to 0-1
            'reasons': reasons,
            'recommendation': self.generate_recommendation(relevance_score, reasons)
        }

    def generate_recommendation(self, relevance_score: float, reasons: list) -> str:
        """Generate recommendations based on the analysis"""
        if relevance_score >= 0.7:
            return "Changes appear to be highly relevant to the JIRA story. Proceed with the review."
        elif relevance_score >= 0.4:
            return "Changes have moderate relevance. Consider reviewing the alignment with the JIRA story requirements."
        else:
            return "Changes show low relevance. Recommend reviewing the changes and ensuring they align with the JIRA story scope."

    @system_message
    def analyze_repository(self, repo_url: str):
        """Main function to analyze repository commits and JIRA stories"""
        # Get commit summary
        commits = self.get_commit_summary(repo_url)
        if isinstance(commits, str):  # Error occurred
            return commits
        
        results = []
        for commit in commits:
            # Extract JIRA ID
            jira_id = self.extract_jira_id(commit['message'])
            if not jira_id:
                continue
            
            # Get JIRA story
            jira_story = self.get_jira_story(jira_id)
            if isinstance(jira_story, str):  # Error occurred
                continue
            
            # Analyze changes
            analysis = self.analyze_changes(commit, jira_story)
            
            results.append({
                'commit': commit,
                'jira_story': jira_story,
                'analysis': analysis
            })
        
        return results

if __name__ == "__main__":
    try:
        analyzer = GitJiraAnalyzer()
        # Get GitHub repository URL
        repo_url = input("Enter the GitHub repository URL (e.g., https://github.com/owner/repo): ")
        results = analyzer.analyze_repository(repo_url)
        
        # Print results
        for result in results:
            print("\n" + "="*50)
            print(f"Commit: {result['commit']['hash']}")
            print(f"Message: {result['commit']['message']}")
            print(f"Author: {result['commit']['author']}")
            print(f"Date: {result['commit']['date']}")
            print("\nModified Files:")
            for file in result['commit']['files']:
                print(f"- {file}")
            print(f"\nJIRA Story: {result['jira_story']['key']} - {result['jira_story']['summary']}")
            print(f"Status: {result['jira_story']['status']}")
            print(f"Relevance Score: {result['analysis']['relevance_score']:.2f}")
            print("\nReasons:")
            for reason in result['analysis']['reasons']:
                print(f"- {reason}")
            print(f"\nRecommendation: {result['analysis']['recommendation']}")
            print("="*50)
            
    except Exception as e:
        print(f"Error: {str(e)}")