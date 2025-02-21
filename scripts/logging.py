import os
import datetime
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

class Logger:
    def __init__(self):
        # Get AppData\Roaming path
        self.base_path = os.path.join(os.getenv('APPDATA'), 'PhantomConsole')
        self.logs_path = os.path.join(self.base_path, 'logs')
        self.current_log_file = None
        self.ensure_directories()
        self.create_new_log()
    
    def ensure_directories(self):
        """Ensure the log directory exists"""
        Path(self.logs_path).mkdir(parents=True, exist_ok=True)
    
    def create_new_log(self):
        """Create a new log file with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_log_file = os.path.join(self.logs_path, f"{timestamp}.log")
        
        # Log the session start
        self.log("SESSION", "New logging session started")
        
    def format_message(self, level: str, message: str) -> str:
        """Format the log message with timestamp and level"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [{level.upper():8}] {message}"
    
    def log(self, level: str, message: str, print_to_console: bool = False):
        """Write a log message to the current log file"""
        try:
            formatted_message = self.format_message(level, message)
            
            # Write to log file
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
            
            # Print to console if requested
            if print_to_console:
                color = {
                    'ERROR': Fore.RED,
                    'WARNING': Fore.YELLOW,
                    'INFO': Fore.WHITE,
                    'SUCCESS': Fore.GREEN,
                    'DEBUG': Fore.CYAN
                }.get(level.upper(), Fore.WHITE)
                
                print(f"{color}{formatted_message}{Style.RESET_ALL}")
                
        except Exception as e:
            # If we can't write to the log file, at least print to console
            print(f"{Fore.RED}Logging error: {str(e)}{Style.RESET_ALL}")
    
    def error(self, message: str, print_to_console: bool = True):
        self.log("ERROR", message, print_to_console)
    
    def warning(self, message: str, print_to_console: bool = True):
        self.log("WARNING", message, print_to_console)
    
    def info(self, message: str, print_to_console: bool = False):
        self.log("INFO", message, print_to_console)
    
    def success(self, message: str, print_to_console: bool = True):
        self.log("SUCCESS", message, print_to_console)
    
    def debug(self, message: str, print_to_console: bool = False):
        self.log("DEBUG", message, print_to_console)

# Create a global logger instance
logger = Logger()
