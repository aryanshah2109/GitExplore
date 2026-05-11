from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tpython

PY_LANGUAGE = Language(tpython.language())

parser = Parser(PY_LANGUAGE)

def walk(node, depth=0):

    if node.is_named:

        print(" " * depth + f"{node.type} [{node.start_point[0] + 1} : {node.end_point[0] + 1}]")
        
        for i, child in enumerate(node.children):

            field_name = node.field_name_for_child(i)

            if field_name:
                print(" " * (depth + 1) + f"FIELD -> {field_name}")

            walk(child, depth + 2)

source_code = b"""
import os
import hashlib

class AuthService:
    \"\"\"Handles user authentication.\"\"\"
    
    def login(self, username: str, password: str) -> bool:
        \"\"\"Verify user credentials and return auth status.\"\"\"
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self._check_db(username, hashed)
    
    def _check_db(self, username, hashed_pw):
        # DB lookup logic here
        pass
"""

tree = parser.parse(source_code)

print(tree.root_node.type)
print(tree.root_node.child_count)

walk(tree.root_node)

function_code = """
(function_definition
   name: (identifier) @function.name
   parameters: (parameters) @function.parameters
   body: (block) @function.body
)
""" 


query = Query(PY_LANGUAGE, function_code)

cursor = QueryCursor(query)

captures = cursor.captures(tree.root_node)

print(captures)

for capture_name, nodes in captures.items():

    print(f"\nCapture: {capture_name}")

    for node in nodes:

        function_name = source_code[
            node.start_byte:node.end_byte
        ].decode()

        print("\nFunction Name:", function_name)

        parent = node.parent

        function_code = source_code[
            parent.start_byte:parent.end_byte
        ].decode()

        print("Function Code:")
        print(function_code)
