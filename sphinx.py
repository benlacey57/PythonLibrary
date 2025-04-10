#!/usr/bin/env python3
"""
PyLib Sphinx Documentation Utility

This script simplifies managing Sphinx documentation by providing commands for:
- Setting up initial documentation
- Building the documentation
- Serving the documentation locally
- Cleaning documentation build files

Features:
---------
1. Documentation Setup
   - Creates docs directory structure
   - Generates Sphinx configuration files
   - Creates placeholder documentation files
   - Adds standard Sphinx extensions

2. Build Management
   - Cleans and rebuilds documentation
   - Handles autoapi generation
   - Creates searchable HTML documentation

3. Local Preview
   - Serves documentation on localhost
   - Auto-rebuilds if documentation is missing

4. Git Integration
   - Pre-push hooks to keep documentation updated
   - Ensures documentation is current before sharing

5. Documentation Structure
   - Organized by component category
   - API reference generated automatically
   - Cross-referencing between sections

Usage Examples:
--------------
# Initial setup with Git hooks
```
python sphinx_setup.py setup --git-hooks
```

# Build documentation
```
python sphinx_setup.py build
```

# Clean and rebuild documentation
```
python sphinx_setup.py build --clean
```

# Remove all generated documentation
```
python sphinx_setup.py clean
```

# Preview documentation in browser
```
python sphinx_setup.py serve
```

# Install Git hooks separately
```
python sphinx_setup.py git-hooks
```

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent
DOCS_DIR = PROJECT_ROOT / "docs"
BUILD_DIR = DOCS_DIR / "_build"
SOURCE_DIR = PROJECT_ROOT / "src"
STATIC_DIR = DOCS_DIR / "_static"
TEMPLATES_DIR = DOCS_DIR / "_templates"

def create_directory(path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {path}")

def run_command(cmd, cwd=None):
    """Run a command and print output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def setup_docs():
    """Set up initial Sphinx documentation structure."""
    print("Setting up Sphinx documentation...")
    
    # Create necessary directories
    create_directory(DOCS_DIR)
    create_directory(STATIC_DIR)
    create_directory(TEMPLATES_DIR)
    
    # Create logo placeholder
    logo_path = STATIC_DIR / "logo.png"
    if not logo_path.exists():
        print(f"Note: Add your logo to {logo_path}")
        
    # Create favicon placeholder
    favicon_path = STATIC_DIR / "favicon.ico"
    if not favicon_path.exists():
        print(f"Note: Add your favicon to {favicon_path}")
    
    # Create custom CSS file
    css_path = STATIC_DIR / "custom.css"
    if not css_path.exists():
        with open(css_path, 'w') as f:
            f.write("""/* Custom styles for PyLib documentation */

/* Make the sidebar wider */
.wy-nav-side {
    width: 350px;
}

.wy-side-nav-search {
    background-color: #2980B9;
}

/* Adjust code block styling */
.highlight {
    background: #f5f5f5;
}

/* Style API documentation */
.class > dt, .function > dt {
    padding: 10px;
    background-color: #e7f2fa;
    border-top: 3px solid #6ab0de;
}

/* Improve table styling */
table.docutils {
    width: 100%;
    margin-bottom: 1.5em;
}

/* Highlight note and warning sections */
.admonition.note {
    background-color: #e7f2fa;
}

.admonition.warning {
    background-color: #ffedcc;
}
""")
        print(f"Created: {css_path}")
    
    # Create conf.py
    conf_path = DOCS_DIR / "conf.py"
    if not conf_path.exists():
        with open(conf_path, 'w') as f:
            f.write('''# Configuration file for the Sphinx documentation builder.
import os
import sys
from datetime import datetime

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'PyLib'
copyright = f'{datetime.now().year}, Your Name'
author = 'Your Name'
release = '0.1.0'

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx_rtd_theme',
    'sphinx_copybutton',
    'autoapi.extension',
    'myst_parser',
]

# Extension configurations
autoapi_type = 'python'
autoapi_dirs = ['../src']
autoapi_keep_files = False
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
    'imported-members',
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# Theme configuration
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'logo_only': False,
    'display_version': True,
}

# Additional HTML options
html_static_path = ['_static']
html_css_files = ['custom.css']
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'

# Intersphinx mapping to other docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/14/', None),
    'rich': ('https://rich.readthedocs.io/en/latest/', None),
}

# Other configurations
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_suffix = ['.rst', '.md']
master_doc = 'index'
language = 'en'
pygments_style = 'sphinx'
todo_include_todos = True
''')
        print(f"Created: {conf_path}")
        
    # Create index.rst
    index_path = DOCS_DIR / "index.rst"
    if not index_path.exists():
        with open(index_path, 'w') as f:
            f.write('''Welcome to PyLib's documentation!
==================================

.. toctree::
   :maxdepth: 1
   :caption: Getting Started:

   getting_started
   installation
   configuration

.. toctree::
   :maxdepth: 1
   :caption: Core Components:

   database
   storage
   ai
   webhooks

.. toctree::
   :maxdepth: 1
   :caption: User Interface:

   terminal_ui
   templates

.. toctree::
   :maxdepth: 1
   :caption: Service Integrations:

   google_services
   cms_integration
   productivity_tools
   payment_services

.. toctree::
   :maxdepth: 1
   :caption: Development:

   api_reference
   contributing
   testing
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
''')
        print(f"Created: {index_path}")
    
    # Create placeholder documentation files
    doc_files = [
        "getting_started.rst",
        "installation.rst",
        "configuration.rst",
        "database.rst",
        "storage.rst",
        "ai.rst",
        "webhooks.rst",
        "terminal_ui.rst",
        "templates.rst",
        "google_services.rst",
        "cms_integration.rst",
        "productivity_tools.rst",
        "payment_services.rst",
        "api_reference.rst",
        "contributing.rst",
        "testing.rst"
    ]
    
    for doc_file in doc_files:
        file_path = DOCS_DIR / doc_file
        if not file_path.exists():
            title = doc_file.replace('.rst', '').replace('_', ' ').title()
            with open(file_path, 'w') as f:
                f.write(f'''{title}
{'=' * len(title)}

.. toctree::
   :maxdepth: 2

Introduction
-----------
This section covers {title.lower()}.

Features
--------
* Feature 1
* Feature 2
* Feature 3

Usage Examples
-------------

Basic Usage
~~~~~~~~~~

.. code-block:: python

    # Example code
    from pylib import example
    
    # Use the library
    result = example.function()

Advanced Usage
~~~~~~~~~~~~~

.. code-block:: python

    # Advanced example
    from pylib import advanced
    
    # Configure options
    config = advanced.Config(option1=True)
    
    # Use advanced features
    result = advanced.process(data, config)

API Reference
------------
See the :ref:`api_reference` for detailed API information.
''')
            print(f"Created placeholder: {file_path}")
    
    print("Sphinx documentation structure set up successfully!")

def build_docs(clean=False):
    """Build Sphinx documentation."""
    if clean:
        clean_docs()
    
    print("Building documentation...")
    return run_command(['sphinx-build', '-b', 'html', DOCS_DIR, BUILD_DIR / 'html'])

def clean_docs():
    """Clean documentation build files."""
    print("Cleaning documentation build files...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"Removed: {BUILD_DIR}")
    
    autoapi_dir = DOCS_DIR / 'autoapi'
    if autoapi_dir.exists():
        shutil.rmtree(autoapi_dir)
        print(f"Removed: {autoapi_dir}")

def serve_docs():
    """Serve documentation locally."""
    html_dir = BUILD_DIR / 'html'
    if not html_dir.exists():
        print("Documentation not built yet. Building...")
        if not build_docs():
            return
    
    print(f"Serving documentation at http://localhost:8000")
    run_command(['python', '-m', 'http.server', '8000'], cwd=html_dir)

def setup_git_hooks():
    """Set up Git pre-push hook to regenerate documentation."""
    git_dir = PROJECT_ROOT / '.git'
    hooks_dir = git_dir / 'hooks'
    
    if not git_dir.exists():
        print("Git repository not found. Initialize Git first.")
        return False
    
    create_directory(hooks_dir)
    
    pre_push_hook = hooks_dir / 'pre-push'
    with open(pre_push_hook, 'w') as f:
        f.write('''#!/bin/sh
# Pre-push hook to regenerate documentation

echo "Pre-push hook: Regenerating documentation..."
python sphinx_setup.py build
git add docs/_build
echo "Documentation updated and added to commit."
''')
    
    # Make the hook executable
    os.chmod(pre_push_hook, 0o755)
    print(f"Git pre-push hook set up at: {pre_push_hook}")
    return True

def create_readme_index():
    """Create a README_INDEX.md file with links to component READMEs."""
    print("Creating README index...")
    
    # Find all README files in the project
    readme_files = []
    for path in PROJECT_ROOT.rglob('README.md'):
        if path.name == 'README.md' and path != PROJECT_ROOT / 'README.md':
            relative_path = path.relative_to(PROJECT_ROOT)
            component_name = path.parent.name
            readme_files.append((component_name, str(relative_path)))
    
    # Create index file
    index_path = PROJECT_ROOT / 'README_INDEX.md'
    with open(index_path, 'w') as f:
        f.write('''# PyLib Component Documentation Index

This file provides links to documentation for all PyLib components.

## Core Components

''')
        
        # Group READMEs by directory
        components = {}
        for name, path in readme_files:
            directory = os.path.dirname(path).split('/')[0]
            if directory not in components:
                components[directory] = []
            components[directory].append((name, path))
        
        # Write grouped links
        for directory, items in sorted(components.items()):
            f.write(f"### {directory.title()}\n\n")
            for name, path in sorted(items):
                f.write(f"* [{name}]({path})\n")
            f.write("\n")
        
        f.write('''
## Full Documentation

For complete documentation, please see the [generated documentation](docs/_build/html/index.html)
or run `python sphinx_setup.py serve` to view it in your browser.
''')
    
    print(f"README index created at: {index_path}")
    return True

def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="PyLib Documentation Utility")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up initial documentation')
    setup_parser.add_argument('--git-hooks', action='store_true', help='Also set up Git hooks')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build documentation')
    build_parser.add_argument('--clean', action='store_true', help='Clean before building')
    
    # Clean command
    subparsers.add_parser('clean', help='Clean documentation build files')
    
    # Serve command
    subparsers.add_parser('serve', help='Serve documentation locally')
    
    # Git hooks command
    subparsers.add_parser('git-hooks', help='Set up Git hooks')
    
    # README index command
    subparsers.add_parser('readme-index', help='Create README index')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_docs()
        if args.git_hooks:
            setup_git_hooks()
    elif args.command == 'build':
        build_docs(clean=args.clean)
    elif args.command == 'clean':
        clean_docs()
    elif args.command == 'serve':
        serve_docs()
    elif args.command == 'git-hooks':
        setup_git_hooks()
    elif args.command == 'readme-index':
        create_readme_index()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()