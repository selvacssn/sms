import requests

def get_org_repositories(org_name, token):
    repositories = []
    url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {
        "Authorization": f"token {token}"
    }
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repositories.extend(response.json())
            # Check if there is a link to the next page of results
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None
        else:
            print(f"Failed to fetch repositories: {response.status_code}")
            return []
    return repositories

if __name__ == "__main__":
    org_name = ""  # Replace with the GitHub organization name correctly
    token = ""  # Replace with your personal access token
    repos = get_org_repositories(org_name, token)
    
    if repos:
        for repo in repos:
            print(f"Repository Name: {repo['name']}")
            """print(f"Description: {repo['description']}")
            print(f"Stars: {repo['stargazers_count']}")
            print(f"Forks: {repo['forks_count']}")
            print(f"URL: {repo['html_url']}")
            print("-" * 40)"""
    else:
        print("No repositories found or an error occurred during processing.")
