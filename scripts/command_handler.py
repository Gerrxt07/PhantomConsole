import os
from typing import List, Dict, Optional
import msvcrt
from colorama import Fore, Style
import scripts.Database
import readline

class CommandHandler:
    def __init__(self):
        self.commands: Dict[str, str] = {
            'clear & cls': 'Clear the console screen',
            'help': 'Show this help message',
            'user': 'Open the user management',
            'logout': 'Log out current user',
            'exit': 'Exit Phantom Console',
            'info': 'Show informations'
        }
        self.command_history: List[str] = []
        self.history_file = os.path.join(os.getenv('APPDATA'), 'PhantomConsole', 'command_history.txt')
        self.history_index = 0
        self._load_history()
        
        self.commandlist = ["user", "logout", "exit", "help", "info"]
        readline.set_completer(self.completer)
        readline.parse_and_bind("tab: complete")

    def completer(self, text, state):
        options = [cmd for cmd in self.commandlist if cmd.startswith(text)]
        return options[state] if state < len(options) else None

    def _load_history(self):
        """Load command history from file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.command_history = [line.strip() for line in f.readlines()]
                    self.history_index = len(self.command_history)
        except Exception:
            self.command_history = []
            self.history_index = 0
        
    def save_history(self):
        """Save command history to file"""
        try:
            with open(self.history_file, 'w') as f:
                f.write('\n'.join(self.command_history[-1000:]))  # Keep last 1000 commands
        except Exception:
            pass

    def add_to_history(self, command: str):
        """Add a command to history"""
        if command and (not self.command_history or command != self.command_history[-1]):
            self.command_history.append(command)
            self.history_index = len(self.command_history)

    def get_previous_command(self) -> Optional[str]:
        """Get previous command from history"""
        if not self.command_history or self.history_index <= 0:
            return None
        self.history_index = max(0, self.history_index - 1)
        return self.command_history[self.history_index]

    def get_next_command(self) -> Optional[str]:
        """Get next command from history"""
        if not self.command_history or self.history_index >= len(self.command_history):
            return None
        self.history_index = min(len(self.command_history), self.history_index + 1)
        return self.command_history[self.history_index - 1] if self.history_index > 0 else None

    def get_input(self, prompt: str) -> str:
        """Get input with command history support"""
        current_input = ""
        cursor_pos = 0
        print(prompt, end='', flush=True)
        
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                
                if char in [b'\r', b'\n']:  # Enter
                    print()
                    if current_input.strip():
                        self.add_to_history(current_input)
                    return current_input
                    
                elif char == b'\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                    
                elif char == b'\xe0':  # Special keys
                    second_char = msvcrt.getch()
                    if second_char == b'H':  # Up arrow
                        prev_cmd = self.get_previous_command()
                        if prev_cmd is not None:
                            # Clear current line
                            print('\r' + ' ' * (len(prompt) + len(current_input)) + '\r', end='')
                            print(prompt + prev_cmd, end='', flush=True)
                            current_input = prev_cmd
                            cursor_pos = len(current_input)
                    elif second_char == b'P':  # Down arrow
                        next_cmd = self.get_next_command()
                        if next_cmd is not None:
                            # Clear current line
                            print('\r' + ' ' * (len(prompt) + len(current_input)) + '\r', end='')
                            print(prompt + next_cmd, end='', flush=True)
                            current_input = next_cmd
                            cursor_pos = len(current_input)
                            
                elif char == b'\x08':  # Backspace
                    if cursor_pos > 0:
                        current_input = current_input[:cursor_pos-1] + current_input[cursor_pos:]
                        cursor_pos -= 1
                        # Redraw the line
                        print('\r' + ' ' * (len(prompt) + len(current_input) + 1) + '\r', end='')
                        print(prompt + current_input, end='', flush=True)
                        if cursor_pos < len(current_input):
                            # Move cursor back to position
                            print('\b' * (len(current_input) - cursor_pos), end='', flush=True)
                            
                else:  # Regular character
                    try:
                        char_str = char.decode('utf-8')
                        if char_str.isprintable():
                            current_input = (
                                current_input[:cursor_pos] + 
                                char_str + 
                                current_input[cursor_pos:]
                            )
                            cursor_pos += 1
                            # Redraw the line
                            print('\r' + prompt + current_input, end='', flush=True)
                    except UnicodeDecodeError:
                        pass

    def print_help(self, current_user: str = None):
        """Print available commands with descriptions"""
        print(f"\n┌─ {Fore.CYAN}Available Commands {Fore.WHITE}─────────────────────┐")
        
        # Get user role, handling dev user case
        user_role = scripts.Database.get_user_role(current_user) if current_user else None
        
        for cmd, desc in self.commands.items():
            # Skip root-only commands for non-root users
            if cmd.startswith('user') and user_role != 'root':
                continue
            print(f"│ {cmd:12} - {desc:25} │")
            
        print(f"└──────────────────────────────────────────┘{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Tips:{Style.RESET_ALL}")
        print("• Use Up/Down arrows for command history")
        print("• Type 'help' to see this message again\n")

# Initialize command handler
command_handler = CommandHandler()
