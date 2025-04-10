# Python Library

A comprehensive Python utility library designed to accelerate development by providing consistent interfaces and implementations for common services and tasks. PyLib provides integrations with databases, storage providers, AI services, and more, all with a consistent API.

## Key Features

- **Consistent Interfaces**: Common interfaces across all service types ensure easy swapping of implementations
- **Rich Console Tools**: Pre-built terminal UI components and templates for rapid CLI development
- **Database Integration**: Unified access to MySQL, PostgreSQL, SQLite, AirTable, and more
- **Storage Services**: Easy file operations with Google Drive, OneDrive, Dropbox, and local storage
- **API Integrations**: Pre-built clients for Google services, WordPress, Jira, Trello, and more
- **AI Services**: Simplified access to OpenAI and Claude AI APIs
- **Templating**: Jinja2 templates for emails, reports, and web content
- **Error Handling**: Comprehensive exception hierarchy with separate production and development messages
- **Configuration**: Flexible configuration from multiple sources (JSON, YAML, ENV)

----

# Installation
To install this python library locally we can use pip:

```
pip install -e /path/to/my_package
```

The `-e` flag installs in "editable" mode, which means changes to your source code will be reflected immediately without needing to reinstall.

Once installed, you can import your package in any Python script.

```python
import python_library
from python_library import core.config
from python_library import core.base.base_client
```

----

## Library Structure

```
pylib/
├── core/            # Core functionality and interfaces
├── interfaces/      # Interface definitions
├── exceptions/      # Exception hierarchy
├── db/              # Database integrations
├── storage/         # Storage service integrations
├── ai/              # AI service integrations
├── webhooks/        # Webhook handlers
├── integrations/    # Third-party service integrations
├── console/         # Rich console components and templates
├── templates/       # Jinja2 templates
└── utils/           # Utility functions
```

----

## Quick Start

### Database Operations

```python
from pylib.db import SQLiteDatabase, MySQLDatabase, PostgresDatabase

# Use SQLite for development
db = SQLiteDatabase("development.db")

# Switch to MySQL in production with the same interface
# db = MySQLDatabase(host="localhost", user="user", password="pass", database="mydb")

# Execute a query
results = db.query("SELECT * FROM users WHERE active = ?", [True])

# Use the query builder
users = db.table("users").where("active", True).limit(10).get()
```

### Storage Operations

```python
from pylib.storage import GoogleDriveStorage, LocalStorage

# Google Drive storage
storage = GoogleDriveStorage(config_path="credentials.json")

# Upload a file
file_id = storage.upload("local_file.txt", "remote_path/file.txt")

# List files in a folder
files = storage.list_files(folder_id="my_folder_id")

# Download a file
storage.download(file_id, "downloaded_file.txt")
```

### Rich Console Interfaces

```python
from pylib.console.templates import MainMenu, Dashboard, SetupWizard

# Create a main menu
menu = MainMenu("My Application", subtitle="v1.0")
menu.add_option("1", "Configure Settings", configure_settings)
menu.add_option("2", "Run Process", run_process)
menu.add_option("3", "View Results", view_results)
menu.display()

# Create a dashboard
dashboard = Dashboard("System Monitor", refresh_rate=2.0)
dashboard.set_header(get_system_info)
dashboard.set_main_panel("CPU Usage", get_cpu_metrics)
dashboard.add_side_panel("Memory Usage", get_memory_metrics)
dashboard.add_side_panel("Disk Space", get_disk_metrics)
dashboard.run()
```

### AI Integration

```python
from pylib.ai import ClaudeAI, OpenAI

# Use Claude AI
claude = ClaudeAI(api_key="your_api_key")
response = claude.generate("Explain quantum computing in simple terms")

# Switch to OpenAI with the same interface
openai = OpenAI(api_key="your_api_key")
response = openai.generate("Explain quantum computing in simple terms")
```

----

## Service Integrations

### Database Providers
- SQLite
- MySQL
- PostgreSQL
- AirTable

### Storage Providers
- Google Drive
- OneDrive
- Dropbox
- Local Storage

### AI Services
- Claude AI
- OpenAI

### Google Services
- Google Docs
- Google Sheets
- Google Slides
- Google Drive
- Google Analytics
- Google Ads

### CMS Systems
- WordPress
- Joomla

### Tools
- Jira
- Trello

### Communication
- Slack
- Discord

### Email Services
- SendGrid
- Mailchimp

### Payment Processors
- Stripe
- PayPal

----

## Design Principles

PyLib is built on these core principles:

1. **Consistency**: Uniform interfaces across all service types
2. **Simplicity**: Clean, intuitive APIs that hide complexity
3. **Reliability**: Comprehensive error handling and testing
4. **Flexibility**: Easy to extend and customize
5. **Documentation**: Thorough documentation with examples

## Development Status

PyLib is currently in active development. The roadmap includes:

- Phase 1: Core Foundation
- Phase 2: Core Services
- Phase 3: Rich Console & Templates
- Phase 4: API Integrations
- Phase 5: Webhooks & Business Tools
- Phase 6: Documentation & Finalisation

----

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Rich](https://github.com/willmcgugan/rich) for terminal user interface components
- [Jinja2](https://jinja.palletsprojects.com/) for templating support
- [SQLAlchemy](https://www.sqlalchemy.org/) for database operations
- [Requests](https://requests.readthedocs.io/) for HTTP functionality
- And all the other open-source projects that made this library possible
```