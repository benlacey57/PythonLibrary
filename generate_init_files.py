"""
Script to scan the Python Utility Library codebase and automatically
generate __init__.py files with appropriate imports.
"""
import os
import re
import sys
from pathlib import Path
import importlib.util
import ast
from typing import Dict, List, Set, Tuple

# Configuration
LIBRARY_ROOT = "./"
EXCLUDE_DIRS = ["__pycache__", "tests", "venv"]
EXCLUDE_FILES = ["__init__.py"]
INDENT = "    "  # 4 spaces for indentation

def get_class_names_from_file(file_path: str) -> List[str]:
    """Extract class names from a Python file."""
    with open(file_path, 'r') as file:
        content = file.read()
    
    try:
        tree = ast.parse(content)
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    except SyntaxError:
        print(f"Syntax error in file: {file_path}")
        return []

def get_function_names_from_file(file_path: str) -> List[str]:
    """Extract function names from a Python file."""
    with open(file_path, 'r') as file:
        content = file.read()
    
    try:
        tree = ast.parse(content)
        return [node.name for node in ast.walk(tree) 
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')]
    except SyntaxError:
        print(f"Syntax error in file: {file_path}")
        return []

def generate_init_file(directory: str) -> None:
    """Generate an __init__.py file for the given directory."""
    dir_path = Path(directory)
    init_file = dir_path / "__init__.py"
    
    # Get directory name for module docstring
    dir_name = dir_path.name
    
    # Get a readable name for the module
    readable_name = ' '.join(word.capitalize() for word in dir_name.split('_'))
    
    # Scan directory for Python files
    python_files = []
    for file in dir_path.glob("*.py"):
        if file.name not in EXCLUDE_FILES:
            python_files.append(file)
    
    # Scan subdirectories
    subdirs = []
    for subdir in dir_path.iterdir():
        if subdir.is_dir() and subdir.name not in EXCLUDE_DIRS:
            subdirs.append(subdir)
    
    # If no Python files or subdirs, skip
    if not python_files and not subdirs:
        return
    
    # Create __init__.py content
    with open(init_file, 'w') as f:
        # Write docstring
        f.write(f'"""\n{readable_name} module for the Python Utility Library.\n"""\n\n')
        
        # Import from current directory's Python files
        imports = []
        all_items = []
        
        for file in sorted(python_files):
            module_name = file.stem
            class_names = get_class_names_from_file(str(file))
            function_names = get_function_names_from_file(str(file))
            
            if class_names or function_names:
                items = class_names + function_names
                if items:
                    imports.append(f"from .{module_name} import {', '.join(items)}")
                    all_items.extend(items)
        
        # Import subdirectories as modules
        for subdir in sorted(subdirs):
            if (subdir / "__init__.py").exists():
                imports.append(f"from . import {subdir.name}")
                all_items.append(subdir.name)
        
        # Write imports
        if imports:
            for import_line in imports:
                f.write(f"{import_line}\n")
            
            f.write("\n")
        
        # Write __all__
        if all_items:
            f.write("__all__ = [\n")
            for item in sorted(all_items):
                f.write(f"{INDENT}'{item}',\n")
            f.write("]\n")
    
    print(f"Generated __init__.py for {directory}")

def process_directory(directory: str) -> None:
    """Process a directory and its subdirectories."""
    dir_path = Path(directory)
    
    # Process current directory
    generate_init_file(directory)
    
    # Process subdirectories
    for subdir in dir_path.iterdir():
        if subdir.is_dir() and subdir.name not in EXCLUDE_DIRS:
            process_directory(str(subdir))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = LIBRARY_ROOT
    
    print(f"Generating __init__.py files for {root_dir}...")
    process_directory(root_dir)
    print("Generated all init files!")