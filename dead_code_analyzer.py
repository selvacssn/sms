import os
import ast
import csv
import re
from typing import List, Dict, Set
from pathlib import Path

def get_folder_name(directory: str) -> str:
    """Extract the last folder name from a path"""
    return os.path.basename(os.path.normpath(directory))

def get_all_files(directory: str) -> Dict[str, List[str]]:
    """Get all relevant files grouped by type"""
    files = {
        'python': [],
        'javascript': [],
        'css': []
    }
    directory = os.path.normpath(directory)
    
    for root, _, filenames in os.walk(directory):
        if 'node_modules' in root or 'build' in root or 'dist' in root:
            continue
            
        for file in filenames:
            full_path = os.path.normpath(os.path.join(root, file))
            if file.endswith('.py'):
                files['python'].append(full_path)
            elif file.endswith(('.js', '.jsx')):
                files['javascript'].append(full_path)
            elif file.endswith('.css'):
                files['css'].append(full_path)
    
    return files

class PythonAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict]:
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find print statements
            print_pattern = r'print\s*\([^)]*\)'
            prints = re.findall(print_pattern, content)
            if prints:
                results.append({
                    'name': 'print',
                    'from': file_path,
                    'to': file_path,
                    'description': f"Found {len(prints)} print statements"
                })
            
            # Find TODO comments
            todo_pattern = r'#\s*TODO[:\s]([^\n]*)'
            todos = re.findall(todo_pattern, content)
            for todo in todos:
                results.append({
                    'name': 'TODO',
                    'from': file_path,
                    'to': file_path,
                    'description': f"TODO comment found: {todo.strip()}"
                })
            
            # Find unused imports, functions and classes
            tree = ast.parse(content)
            visitor = DeadCodeVisitor()
            visitor.current_file = file_path
            visitor.visit(tree)
            
            # Find unused functions
            for func in visitor.defined_functions - visitor.called_functions:
                if not func.startswith('test_'):
                    results.append({
                        'name': func,
                        'from': file_path,
                        'to': file_path,
                        'description': f"Unused Python function '{func}'"
                    })
            
            # Find unused classes
            for cls in visitor.defined_classes - visitor.used_classes:
                results.append({
                    'name': cls,
                    'from': file_path,
                    'to': file_path,
                    'description': f"Unused Python class '{cls}'"
                })
            
            return results
        except Exception as e:
            print(f"Error analyzing Python file {file_path}: {str(e)}")
            return []

class JavaScriptAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict]:
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find console.log statements
            console_pattern = r'console\.(log|debug|info|warn|error)\('
            console_logs = re.findall(console_pattern, content)
            if console_logs:
                results.append({
                    'name': 'console.log',
                    'from': file_path,
                    'to': file_path,
                    'description': f"Found {len(console_logs)} console statements"
                })
            
            # Find TODO comments
            todo_pattern = r'(?://|/\*)\s*TODO[:\s]([^\n]*)'
            todos = re.findall(todo_pattern, content)
            for todo in todos:
                results.append({
                    'name': 'TODO',
                    'from': file_path,
                    'to': file_path,
                    'description': f"TODO comment found: {todo.strip()}"
                })
            
            # Find unused exports
            export_pattern = r'export\s+(?:const|let|var|function|class)\s+(\w+)'
            exports = re.findall(export_pattern, content)
            for export in exports:
                if not re.search(rf'\b{export}\b', content.replace(f'export {export}', '')):
                    results.append({
                        'name': export,
                        'from': file_path,
                        'to': file_path,
                        'description': f"Potentially unused export '{export}'"
                    })
            
            return results
        except Exception as e:
            print(f"Error analyzing JavaScript file {file_path}: {str(e)}")
            return []

class CSSAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict]:
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find unused CSS classes (basic detection)
            class_pattern = r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)'
            classes = re.findall(class_pattern, content)
            
            # Find vendor prefixes
            vendor_prefix_pattern = r'(-webkit-|-moz-|-ms-|-o-)[a-zA-Z-]+'
            vendor_prefixes = re.findall(vendor_prefix_pattern, content)
            if vendor_prefixes:
                results.append({
                    'name': 'vendor-prefixes',
                    'from': file_path,
                    'to': file_path,
                    'description': f"Found {len(vendor_prefixes)} vendor prefixes that might need autoprefixer"
                })
            
            # Find TODO comments
            todo_pattern = r'/\*\s*TODO[:\s]([^\n]*)\*/'
            todos = re.findall(todo_pattern, content)
            for todo in todos:
                results.append({
                    'name': 'TODO',
                    'from': file_path,
                    'to': file_path,
                    'description': f"TODO comment found in CSS: {todo.strip()}"
                })
            
            return results
        except Exception as e:
            print(f"Error analyzing CSS file {file_path}: {str(e)}")
            return []

class DeadCodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()
        self.defined_functions = set()
        self.called_functions = set()
        self.defined_classes = set()
        self.used_classes = set()
        self.current_file = ""

    def visit_FunctionDef(self, node):
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.defined_classes.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.called_functions.add(node.func.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            if node.id in self.defined_classes:
                self.used_classes.add(node.id)
        self.generic_visit(node)

def analyze_directory(directory: str) -> Dict[str, List[Dict]]:
    folder_name = get_folder_name(directory)
    files = get_all_files(directory)
    results = {
        'python': [],
        'javascript': [],
        'css': []
    }
    
    print(f"\nAnalyzing {folder_name}:")
    print(f"Found {len(files['python'])} Python files")
    print(f"Found {len(files['javascript'])} JavaScript files")
    print(f"Found {len(files['css'])} CSS files")
    
    # Analyze Python files
    python_analyzer = PythonAnalyzer()
    for file_path in files['python']:
        print(f"Analyzing Python file: {file_path}")
        results['python'].extend(python_analyzer.analyze_file(file_path))
    
    # Analyze JavaScript files
    js_analyzer = JavaScriptAnalyzer()
    for file_path in files['javascript']:
        print(f"Analyzing JavaScript file: {file_path}")
        results['javascript'].extend(js_analyzer.analyze_file(file_path))
    
    # Analyze CSS files
    css_analyzer = CSSAnalyzer()
    for file_path in files['css']:
        print(f"Analyzing CSS file: {file_path}")
        results['css'].extend(css_analyzer.analyze_file(file_path))
    
    return results

def write_results(results: Dict[str, List[Dict]], folder_name: str):
    for file_type, findings in results.items():
        if findings:
            output_file = f"dead_code_results_{folder_name}_{file_type}.csv"
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'from', 'to', 'description'])
                writer.writeheader()
                writer.writerows(findings)
            print(f"Results written to {output_file}")

def main():
    directories = [
        r"C:\Users\SenthilSelvaNivasC\workspace\common_backend_ui\rendering_engine",
        r"C:\Users\SenthilSelvaNivasC\workspace\common_backend_ui\bff\src",
        r"C:\Users\SenthilSelvaNivasC\workspace\common-apis\src_mig"
    ]
    
    for directory in directories:
        folder_name = get_folder_name(directory)
        print(f"\nAnalyzing directory: {directory}")
        results = analyze_directory(directory)
        write_results(results, folder_name)

if __name__ == "__main__":
    main()
