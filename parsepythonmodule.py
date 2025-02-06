import ast

class FunctionPrinter(ast.NodeVisitor):
    def visit_ClassDef(self, node):
        print(f"Class name: {node.name}")
        # Traverse inside the class definition
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Check if the node is a method inside a class
        if isinstance(node.parent, ast.ClassDef):
            print(f"Method name: {node.name} (inside class {node.parent.name})")
        else:
            print(f"Function name: {node.name}")

        print("Definition:")
        print(ast.unparse(node))  # This works for Python 3.9 and above
        print("----")

    def generic_visit(self, node):
        # Assign parent to each node
        for child in ast.iter_child_nodes(node):
            child.parent = node
        super().generic_visit(node)

# Example Python code to parse
code = """
class Greeter:
    def hello(self):
        print('Hello, world!')

    def goodbye(self):
        print('Goodbye, world!')

def global_function():
    print('This is a global function.')
"""

# Parse the code into an AST and visit each node
#with open('getbitbucketdata.py', 'r') as file:
#    code = file.read()

tree = ast.parse(code)
visitor = FunctionPrinter()
visitor.visit(tree)
