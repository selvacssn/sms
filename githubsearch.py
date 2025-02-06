import requests
import ast
import json

class FunctionPrinter(ast.NodeVisitor):
    def __init__(self, query):
        self.query = query
        self.matched_definitions = []

    def visit_ClassDef(self, node):
        print(f"Class name: {node.name}")
        # Traverse inside the class definition
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Check if the node is a method inside a class
        #print(node.name)
        if isinstance(node.parent, ast.ClassDef):
            if self.query in node.name: 
                print(f"Method name: {node.name} (inside class {node.parent.name})")
        else:
            if self.query in node.name: 
                print(f"Function name: {node.name}")

        #print("Definition:")
        if self.query in ast.unparse(node):
            print(ast.unparse(node))  # This works for Python 3.9 and above
            self.matched_definitions.append({'method_definition':ast.unparse(node)})
        #print("----")

    def generic_visit(self, node):
        # Assign parent to each node
        for child in ast.iter_child_nodes(node):
            child.parent = node
        super().generic_visit(node)
    
    def get_matched_definitions(self):
        return self.matched_definitions


def github_search(query, language, repo, token):
    """
    Search GitHub for code matching the query in a specific language and repository.

    Args:
    query (str): The search keyword or phrase.
    language (str): Programming language to filter by.
    repo (str): Repository to search in the format 'username/repository'.
    token (str): GitHub personal access token.

    Returns:
    json: Search results in JSON format.
    """
    url = 'https://api.github.com/search/code'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    query_va = f'"{query}"+in:file+language:{language}+repo:{repo}'

    full_url = f"{url}?q={query_va}"
    print(url,headers)
    response = requests.get(full_url, headers=headers)
    print(response.url)
    return response.json()

def download_github_file(owner, repo, file_path, token):
    """
    Download a file from a GitHub repository.

    Args:
    owner (str): GitHub username or organization.
    repo (str): Repository name.
    file_path (str): Path to the file in the repository.
    token (str): GitHub personal access token.

    Returns:
    str: Content of the file.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.raw'  # Ensures you get the raw file content
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text  # or response.content if binary file
        #with open('downloaded_file.py', 'w') as file:
        #    file.write(file_content)
        #print("File downloaded and saved as 'downloaded_file.py'.")
    else:
        raise Exception(f"Failed to download file: {response.content}")
    
def _query_github_data(sql_query):
    # User inputs
    matched_definitions_final=[]
    GITHUB_TOKEN = ''  # Replace with your GitHub token
    REPO = ''  # Format: 'username/repository'
    LANGUAGE = 'python'
    QUERY = sql_query  # Example: 'def calculate'

    # Perform the search
    search_results = github_search(QUERY, LANGUAGE, REPO, GITHUB_TOKEN)
    print(search_results['total_count'])
    for item in search_results['items']:
        file_path=item['path']
        file_content = download_github_file( file_path, GITHUB_TOKEN)
        tree = ast.parse(file_content)
        visitor = FunctionPrinter(QUERY)
        visitor.visit(tree)
        templist=visitor.get_matched_definitions()
        for res in templist:
            matched_definitions_final.append(res)

    result = json.dumps(matched_definitions_final)
    return result

print(_query_github_data('copy_from_sftp'))
    