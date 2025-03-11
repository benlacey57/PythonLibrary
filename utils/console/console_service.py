import json
from typing import Any, List, Dict, Optional, Union, Iterable
from contextlib import contextmanager

from core.base.base_service import BaseService
from core.interfaces.configurable import Configurable
from core.interfaces.loggable import Loggable

class ConsoleService(BaseService, Configurable, Loggable):
    """
    Service for enhanced console output using Rich library.
    
    Provides methods for printing styled text, tables, JSON, progress bars, etc.
    """
    
    def __init__(self, config=None):
        """
        Initialize the ConsoleService.
        
        Args:
            config: Configuration for the service.
        """
        self.configure(config)
        self.initialize_logger("console_service")
        
        # Import Rich components
        try:
            from rich.console import Console
            from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
            from rich.table import Table
            from rich.syntax import Syntax
            from rich.panel import Panel
            from rich.markdown import Markdown
            from rich.rule import Rule
            
            self._rich_available = True
            self._console = Console()
            self._rich_modules = {
                "Console": Console,
                "Progress": Progress,
                "BarColumn": BarColumn,
                "TextColumn": TextColumn,
                "TimeRemainingColumn": TimeRemainingColumn,
                "Table": Table,
                "Syntax": Syntax,
                "Panel": Panel,
                "Markdown": Markdown,
                "Rule": Rule
            }
            
            self.logger.info("Rich library loaded successfully")
        except ImportError:
            self._rich_available = False
            self._console = None
            self.logger.warning("Rich library not available. Install with: pip install rich")
    
    def print(self, *args, style: Optional[str] = None, **kwargs) -> None:
        """
        Print text to the console with optional styling.
        
        Args:
            args: Positional arguments to print.
            style: Rich style string.
            kwargs: Keyword arguments for Rich console.print.
        """
        if self._rich_available:
            self._console.print(*args, style=style, **kwargs)
        else:
            print(*args)
    
    def print_table(self, data: List[List[str]], headers: Optional[List[str]] = None, 
                   title: Optional[str] = None) -> None:
        """
        Print data as a table.
        
        Args:
            data: Table data as a list of rows.
            headers: Optional column headers.
            title: Optional table title.
        """
        if not self._rich_available:
            # Fallback to simple table printing
            if headers:
                print("\t".join(headers))
                print("-" * (sum(len(h) for h in headers) + len(headers) * 2))
            
            for row in data:
                print("\t".join(str(cell) for cell in row))
            return
            
        Table = self._rich_modules["Table"]
        table = Table(title=title)
        
        # Add headers
        if headers:
            for header in headers:
                table.add_column(header)
                
        # Add rows
        for row in data:
            table.add_row(*[str(cell) for cell in row])
            
        self._console.print(table)
    
    def print_json(self, data: Any, title: Optional[str] = None) -> None:
        """
        Print data as formatted JSON.
        
        Args:
            data: Data to format as JSON.
            title: Optional title.
        """
        if not self._rich_available:
            # Fallback to simple JSON printing
            if title:
                print(f"=== {title} ===")
            print(json.dumps(data, indent=2))
            return
            
        Syntax = self._rich_modules["Syntax"]
        Panel = self._rich_modules["Panel"]
        
        json_str = json.dumps(data, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", word_wrap=True)
        
        if title:
            panel = Panel(syntax, title=title)
            self._console.print(panel)
        else:
            self._console.print(syntax)
    
    def print_markdown(self, markdown_text: str) -> None:
        """
        Print markdown text with formatting.
        
        Args:
            markdown_text: Markdown formatted text.
        """
        if not self._rich_available:
            # Fallback to simple text printing
            print(markdown_text)
            return
            
        Markdown = self._rich_modules["Markdown"]
        markdown = Markdown(markdown_text)
        self._console.print(markdown)
    
    def print_rule(self, title: Optional[str] = None, style: str = "bright_blue") -> None:
        """
        Print a horizontal rule with optional title.
        
        Args:
            title: Optional title to display in the rule.
            style: Rule style.
        """
        if not self._rich_available:
            # Fallback to simple rule
            width = 80
            if title:
                padding = (width - len(title) - 2) // 2
                print(f"{'-' * padding} {title} {'-' * padding}")
            else:
                print("-" * width)
            return
            
        Rule = self._rich_modules["Rule"]
        rule = Rule(title=title, style=style)
        self._console.print(rule)
    
    @contextmanager
    def progress_bar(self, total: int, description: str = "Progress") -> Any:
        """
        Create a progress bar.
        
        Args:
            total: Total number of steps.
            description: Description of the task.
            
        Yields:
            Progress object that can be advanced.
        """
        if not self._rich_available:
            # Fallback to simple progress reporting
            print(f"{description}: Starting...")
            
            class SimpleProgress:
                def advance(self, amount=1):
                    nonlocal total
                    nonlocal description
                    print(f"{description}: Advanced by {amount}")
                    
            yield SimpleProgress()
            print(f"{description}: Complete!")
            return
            
        Progress = self._rich_modules["Progress"]
        BarColumn = self._rich_modules["BarColumn"]
        TextColumn = self._rich_modules["TextColumn"]
        TimeRemainingColumn = self._rich_modules["TimeRemainingColumn"]
        
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn()
        ) as progress:
            task_id = progress.add_task(description, total=total)
            
            class ProgressWrapper:
                def __init__(self, progress, task_id):
                    self.progress = progress
                    self.task_id = task_id
                    
                def advance(self, amount=1):
                    self.progress.update(self.task_id, advance=amount)
                    
            yield ProgressWrapper(progress, task_id)
    
    @contextmanager
    def status(self, message: str) -> None:
        """
        Create a status spinner with a message.
        
        Args:
            message: Status message to display.
        """
        if not self._rich_available:
            # Fallback to simple status
            print(f"{message}...")
            yield
            print(f"{message}... Done!")
            return
            
        with self._console.status(message) as _:
            yield
    
    def clear(self) -> None:
        """
        Clear the console screen.
        """
        if self._rich_available:
            self._console.clear()
        else:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_console(self) -> Any:
        """
        Get the underlying Rich console object.
        
        Returns:
            Console: Rich console object or None if Rich is not available.
        """
        return self._console