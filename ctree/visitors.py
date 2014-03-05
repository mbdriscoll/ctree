"""
For now, just use visitors defined by Python's AST library.
"""
import ast

NodeVisitor = ast.NodeVisitor
NodeTransformer = ast.NodeTransformer
