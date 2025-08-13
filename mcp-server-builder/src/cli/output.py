"""Output formatting and user feedback utilities."""

import sys
import time
from typing import Optional, List, Dict, Any
from enum import Enum


class Color(Enum):
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


class VerbosityLevel(Enum):
    """Verbosity levels for output formatting."""
    QUIET = 0      # Only errors
    NORMAL = 1     # Normal output (success, info, warnings, errors)
    VERBOSE = 2    # Include verbose messages and detailed progress
    DEBUG = 3      # Include debug information and traces


class OutputFormatter:
    """Handles formatted output with colors and progress indicators."""
    
    def __init__(self, use_colors: bool = None, verbosity: int = 0):
        """
        Initialize output formatter.
        
        Args:
            use_colors: Whether to use colored output (auto-detect if None)
            verbosity: Verbosity level (0-3)
        """
        self.verbosity = verbosity
        self.verbosity_level = VerbosityLevel(min(verbosity, 3))
        
        # Auto-detect color support if not specified
        if use_colors is None:
            self.use_colors = self._supports_color()
        else:
            self.use_colors = use_colors
    
    def _supports_color(self) -> bool:
        """Check if terminal supports color output."""
        # Check if stdout is a TTY and not redirected
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check environment variables
        import os
        if os.environ.get('NO_COLOR'):
            return False
        
        if os.environ.get('FORCE_COLOR'):
            return True
        
        # Check TERM environment variable
        term = os.environ.get('TERM', '')
        if 'color' in term or term in ['xterm', 'xterm-256color', 'screen']:
            return True
        
        # Windows terminal detection
        if sys.platform == 'win32':
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                # Check for Windows 10+ with ANSI support
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                    return True
                except:
                    return False
        
        return False
    
    def colorize(self, text: str, color: Color) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_colors:
            return text
        return f"{color.value}{text}{Color.RESET.value}"
    
    def success(self, message: str) -> None:
        """Print success message."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        icon = "✅" if self.use_colors else "[SUCCESS]"
        colored_msg = self.colorize(message, Color.GREEN)
        print(f"{icon} {colored_msg}")
    
    def error(self, message: str, file=None) -> None:
        """Print error message (always shown, even in quiet mode)."""
        if file is None:
            file = sys.stderr
        icon = "❌" if self.use_colors else "[ERROR]"
        colored_msg = self.colorize(message, Color.RED)
        print(f"{icon} {colored_msg}", file=file)
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        icon = "⚠️" if self.use_colors else "[WARNING]"
        colored_msg = self.colorize(message, Color.YELLOW)
        print(f"{icon} {colored_msg}")
    
    def info(self, message: str) -> None:
        """Print info message."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        icon = "ℹ️" if self.use_colors else "[INFO]"
        colored_msg = self.colorize(message, Color.BLUE)
        print(f"{icon} {colored_msg}")
    
    def debug(self, message: str) -> None:
        """Print debug message if verbosity is high enough."""
        if self.verbosity >= 3:
            icon = "🐛" if self.use_colors else "[DEBUG]"
            colored_msg = self.colorize(message, Color.DIM)
            print(f"{icon} {colored_msg}")
    
    def verbose(self, message: str, level: int = 1) -> None:
        """Print verbose message if verbosity level is met."""
        if self.verbosity >= level:
            if level == 1:
                icon = "💬" if self.use_colors else "[VERBOSE]"
                color = Color.CYAN
            elif level == 2:
                icon = "🔍" if self.use_colors else "[DETAIL]"
                color = Color.BRIGHT_CYAN
            else:  # level >= 3
                icon = "🔬" if self.use_colors else "[TRACE]"
                color = Color.DIM
            
            colored_msg = self.colorize(message, color)
            print(f"{icon} {colored_msg}")
    
    def header(self, title: str, subtitle: str = None) -> None:
        """Print formatted header."""
        if self.use_colors:
            print(f"\n🚀 {self.colorize(title, Color.BOLD)}")
        else:
            print(f"\n=== {title} ===")
        
        if subtitle:
            if self.use_colors:
                print(f"   {self.colorize(subtitle, Color.DIM)}")
            else:
                print(f"    {subtitle}")
        
        print("-" * 50)
    
    def section(self, title: str) -> None:
        """Print section header."""
        if self.use_colors:
            print(f"\n📋 {self.colorize(title, Color.BOLD)}")
        else:
            print(f"\n--- {title} ---")
    
    def list_item(self, item: str, indent: int = 0) -> None:
        """Print list item with proper indentation."""
        prefix = "  " * indent
        if self.use_colors:
            print(f"{prefix}• {item}")
        else:
            print(f"{prefix}- {item}")
    
    def key_value(self, key: str, value: Any, indent: int = 0) -> None:
        """Print key-value pair."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        prefix = "  " * indent
        if self.use_colors:
            colored_key = self.colorize(key, Color.CYAN)
            print(f"{prefix}{colored_key}: {value}")
        else:
            print(f"{prefix}{key}: {value}")
    
    def status_update(self, message: str, status: str = "INFO") -> None:
        """Print a status update with timestamp."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if status.upper() == "SUCCESS":
            icon = "✅" if self.use_colors else "[SUCCESS]"
            color = Color.GREEN
        elif status.upper() == "ERROR":
            icon = "❌" if self.use_colors else "[ERROR]"
            color = Color.RED
        elif status.upper() == "WARNING":
            icon = "⚠️" if self.use_colors else "[WARNING]"
            color = Color.YELLOW
        else:
            icon = "ℹ️" if self.use_colors else "[INFO]"
            color = Color.BLUE
        
        if self.verbosity >= 2:  # Show timestamp in verbose mode
            timestamp_str = self.colorize(f"[{timestamp}]", Color.DIM) if self.use_colors else f"[{timestamp}]"
            colored_msg = self.colorize(message, color)
            print(f"{timestamp_str} {icon} {colored_msg}")
        else:
            colored_msg = self.colorize(message, color)
            print(f"{icon} {colored_msg}")
    
    def step_start(self, step_name: str, step_number: int = None, total_steps: int = None) -> None:
        """Mark the start of a processing step."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        
        if step_number and total_steps:
            progress_info = f"[{step_number}/{total_steps}]"
            if self.use_colors:
                progress_info = self.colorize(progress_info, Color.DIM)
            print(f"\n🔄 {progress_info} Starting: {step_name}")
        else:
            print(f"\n🔄 Starting: {step_name}")
    
    def step_complete(self, step_name: str, duration: float = None) -> None:
        """Mark the completion of a processing step."""
        if self.verbosity_level == VerbosityLevel.QUIET:
            return
        
        duration_str = f" ({format_duration(duration)})" if duration else ""
        self.success(f"Completed: {step_name}{duration_str}")
    
    def progress_bar(self, current: int, total: int, width: int = 40) -> str:
        """Generate a progress bar string."""
        if total == 0:
            percentage = 100
        else:
            percentage = int((current / total) * 100)
        
        filled = int((current / total) * width) if total > 0 else width
        bar = "█" * filled + "░" * (width - filled)
        
        if self.use_colors:
            colored_bar = self.colorize(bar, Color.GREEN if percentage == 100 else Color.BLUE)
            return f"{colored_bar} {percentage:3d}% ({current}/{total})"
        else:
            return f"[{bar}] {percentage:3d}% ({current}/{total})"


class ProgressIndicator:
    """Animated progress indicator for long-running operations."""
    
    def __init__(self, message: str, formatter: OutputFormatter):
        self.message = message
        self.formatter = formatter
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"] if formatter.use_colors else ["|", "/", "-", "\\"]
        self.current_frame = 0
        self.running = False
        self.start_time = None
    
    def start(self) -> None:
        """Start the progress indicator."""
        self.running = True
        self.start_time = time.time()
        self._update()
    
    def stop(self, success_message: str = None) -> None:
        """Stop the progress indicator."""
        self.running = False
        # Clear the line
        print("\r" + " " * (len(self.message) + 20), end="\r")
        
        if success_message:
            elapsed = time.time() - self.start_time if self.start_time else 0
            duration_str = format_duration(elapsed)
            self.formatter.success(f"{success_message} ({duration_str})")
    
    def update_message(self, new_message: str) -> None:
        """Update the progress message."""
        self.message = new_message
        if self.running:
            self._update()
    
    def _update(self) -> None:
        """Update the progress indicator frame."""
        if not self.running:
            return
        
        frame = self.frames[self.current_frame]
        elapsed = time.time() - self.start_time if self.start_time else 0
        duration_str = format_duration(elapsed)
        print(f"\r{frame} {self.message} [{duration_str}]", end="", flush=True)
        self.current_frame = (self.current_frame + 1) % len(self.frames)


def create_summary_report(
    title: str,
    data: Dict[str, Any],
    formatter: OutputFormatter,
    next_steps: List[str] = None,
    warnings: List[str] = None,
    errors: List[str] = None,
    show_timestamp: bool = True
) -> None:
    """Create a formatted summary report."""
    if show_timestamp:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatter.header(title, f"Generated at {timestamp}")
    else:
        formatter.header(title)
    
    # Show errors first if any
    if errors:
        formatter.section("❌ Errors")
        for error in errors:
            # Use list_item instead of error to keep it in stdout for reports
            formatter.list_item(f"❌ {error}" if formatter.use_colors else f"[ERROR] {error}")
        print()
    
    # Show warnings if any
    if warnings:
        formatter.section("⚠️ Warnings")
        for warning in warnings:
            formatter.warning(warning)
        print()
    
    # Main data
    formatter.section("📊 Summary")
    for key, value in data.items():
        if isinstance(value, list):
            formatter.key_value(key, f"{len(value)} items")
            for item in value[:5]:  # Show first 5 items
                formatter.list_item(str(item), indent=1)
            if len(value) > 5:
                formatter.list_item(f"... and {len(value) - 5} more", indent=1)
        elif isinstance(value, dict):
            formatter.key_value(key, f"{len(value)} items")
            for k, v in list(value.items())[:3]:  # Show first 3 items
                formatter.key_value(k, v, indent=1)
            if len(value) > 3:
                formatter.list_item(f"... and {len(value) - 3} more", indent=1)
        else:
            formatter.key_value(key, value)
    
    # Next steps
    if next_steps:
        formatter.section("🚀 Next Steps")
        for i, step in enumerate(next_steps, 1):
            formatter.list_item(f"{i}. {step}")
    
    print()


def create_detailed_report(
    title: str,
    sections: Dict[str, Dict[str, Any]],
    formatter: OutputFormatter,
    show_timestamp: bool = True
) -> None:
    """Create a detailed multi-section report."""
    if show_timestamp:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatter.header(title, f"Generated at {timestamp}")
    else:
        formatter.header(title)
    
    for section_title, section_data in sections.items():
        formatter.section(section_title)
        
        for key, value in section_data.items():
            if isinstance(value, list):
                if value:  # Only show non-empty lists
                    formatter.key_value(key, f"{len(value)} items")
                    for item in value[:10]:  # Show first 10 items for detailed reports
                        formatter.list_item(str(item), indent=1)
                    if len(value) > 10:
                        formatter.list_item(f"... and {len(value) - 10} more", indent=1)
                else:
                    formatter.key_value(key, "None")
            elif isinstance(value, dict):
                if value:  # Only show non-empty dicts
                    formatter.key_value(key, f"{len(value)} items")
                    for k, v in list(value.items())[:5]:  # Show first 5 items
                        formatter.key_value(k, v, indent=1)
                    if len(value) > 5:
                        formatter.list_item(f"... and {len(value) - 5} more", indent=1)
                else:
                    formatter.key_value(key, "None")
            else:
                formatter.key_value(key, value)
        
        print()  # Add spacing between sections


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def create_progress_summary(
    operation: str,
    total_steps: int,
    completed_steps: int,
    current_step: str,
    formatter: OutputFormatter,
    start_time: float = None
) -> None:
    """Create a progress summary display."""
    percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
    
    # Progress bar
    progress_bar = formatter.progress_bar(completed_steps, total_steps, width=30)
    
    # Time information
    time_info = ""
    if start_time:
        elapsed = time.time() - start_time
        if completed_steps > 0:
            avg_time_per_step = elapsed / completed_steps
            remaining_steps = total_steps - completed_steps
            estimated_remaining = avg_time_per_step * remaining_steps
            time_info = f" | Elapsed: {format_duration(elapsed)} | ETA: {format_duration(estimated_remaining)}"
        else:
            time_info = f" | Elapsed: {format_duration(elapsed)}"
    
    # Current step info
    step_info = f"Step {completed_steps + 1}/{total_steps}: {current_step}" if current_step else ""
    
    print(f"\r{operation} {progress_bar}{time_info}")
    if step_info and formatter.verbosity >= 1:
        print(f"  {step_info}")


def create_status_table(
    headers: List[str],
    rows: List[List[str]],
    formatter: OutputFormatter,
    title: str = None
) -> None:
    """Create a formatted status table."""
    if not rows:
        formatter.warning("No data to display")
        return
    
    if title:
        formatter.section(title)
    
    # Calculate column widths
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Create separator
    separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
    
    # Print table
    print(separator)
    
    # Headers
    header_row = "|"
    for i, header in enumerate(headers):
        if formatter.use_colors:
            colored_header = formatter.colorize(header, Color.BOLD)
            header_row += f" {colored_header:<{col_widths[i]}} |"
        else:
            header_row += f" {header:<{col_widths[i]}} |"
    print(header_row)
    print(separator)
    
    # Data rows
    for row in rows:
        data_row = "|"
        for i, cell in enumerate(row):
            if i < len(col_widths):
                data_row += f" {str(cell):<{col_widths[i]}} |"
        print(data_row)
    
    print(separator)
    print()


def create_step_by_step_guide(
    title: str,
    steps: List[Dict[str, str]],
    formatter: OutputFormatter
) -> None:
    """Create a step-by-step guide with commands and descriptions."""
    formatter.header(title)
    
    for i, step in enumerate(steps, 1):
        step_title = step.get('title', f'Step {i}')
        description = step.get('description', '')
        command = step.get('command', '')
        note = step.get('note', '')
        
        # Step header
        if formatter.use_colors:
            step_header = formatter.colorize(f"{i}. {step_title}", Color.BOLD)
            print(f"\n{step_header}")
        else:
            print(f"\n{i}. {step_title}")
        
        # Description
        if description:
            print(f"   {description}")
        
        # Command
        if command:
            if formatter.use_colors:
                colored_command = formatter.colorize(command, Color.GREEN)
                print(f"   $ {colored_command}")
            else:
                print(f"   $ {command}")
        
        # Note
        if note:
            if formatter.use_colors:
                colored_note = formatter.colorize(f"Note: {note}", Color.YELLOW)
                print(f"   {colored_note}")
            else:
                print(f"   Note: {note}")
    
    print()


def format_validation_results(
    results: Dict[str, Any],
    formatter: OutputFormatter
) -> None:
    """Format validation results in a user-friendly way."""
    total_tests = results.get('total_tests', 0)
    passed_tests = results.get('passed_tests', 0)
    failed_tests = results.get('failed_tests', 0)
    warnings = results.get('warnings', [])
    errors = results.get('errors', [])
    
    # Overall status
    if failed_tests == 0 and len(errors) == 0:
        formatter.success(f"All {total_tests} validation tests passed!")
    else:
        formatter.error(f"{failed_tests} of {total_tests} validation tests failed")
    
    # Test summary table
    if total_tests > 0:
        test_data = [
            ["Total Tests", str(total_tests)],
            ["Passed", str(passed_tests)],
            ["Failed", str(failed_tests)],
            ["Success Rate", f"{(passed_tests/total_tests)*100:.1f}%"]
        ]
        
        create_status_table(["Metric", "Value"], test_data, formatter, "Test Results Summary")
    
    # Show errors
    if errors:
        formatter.section("❌ Errors Found")
        for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
            formatter.list_item(f"{error}")
        
        if len(errors) > 10:
            formatter.list_item(f"... and {len(errors) - 10} more errors")
    
    # Show warnings
    if warnings:
        formatter.section("⚠️ Warnings")
        for warning in warnings[:5]:  # Show first 5 warnings
            formatter.list_item(f"{warning}")
        
        if len(warnings) > 5:
            formatter.list_item(f"... and {len(warnings) - 5} more warnings")