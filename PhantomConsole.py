import os
import scripts.Database
import scripts.Startup
from colorama import init, Fore, Style
import getpass
import time
import threading
from scripts.logging import logger
from scripts.session import current_session
from scripts.command_handler import command_handler
import msvcrt
init(autoreset=True)

# Global variables for session management
current_user = None
SESSION_TIMEOUT = 300  # 5 minutes in seconds

def update_activity():
    current_session.update_activity()

def check_session_timeout():
    global current_user
    while True:
        if current_user and not current_session.validate(current_session.token):
            prev_user = current_user
            current_user = None
            logger.info(f"Session timeout for user: {prev_user}")
            print(f"\n{Fore.YELLOW}Session timed out due to inactivity{Style.RESET_ALL}")
            handle_logout()
        time.sleep(1)

def handle_logout():
    global current_user
    if current_user:
        prev_user = current_user
        current_user = None
        current_session.clear()
        os.system('cls')
        logger.info(f"User logged out: {prev_user}")
        print(f"\n{Fore.GREEN}Logged out successfully{Style.RESET_ALL}")
        return True
    return True

def get_password(prompt):
    """Get password input with asterisk masking"""
    password = ""
    cursor_pos = 0
    print(prompt, end='', flush=True)
    
    while True:
        char = msvcrt.getch()
        if char in [b'\r', b'\n']:  # Enter
            print()
            return password
        elif char == b'\x08':  # Backspace
            if cursor_pos > 0:
                password = password[:cursor_pos-1] + password[cursor_pos:]
                cursor_pos -= 1
                print('\b \b', end='', flush=True)
        elif char == b'\x03':  # Ctrl+C
            raise KeyboardInterrupt
        else:
            try:
                char_str = char.decode('utf-8')
                if char_str.isprintable():
                    password = password[:cursor_pos] + char_str + password[cursor_pos:]
                    cursor_pos += 1
                    print('*', end='', flush=True)
            except UnicodeDecodeError:
                pass

def handle_create_user():
    user_role = scripts.Database.get_user_role(current_user)
    if user_role != "root":
        print(f"{Fore.RED}✖ Access denied. Root privileges required.{Style.RESET_ALL}")
        return True

    print(f"\n┌─ {Fore.CYAN}Create New User {Fore.WHITE}───────────────────┐")
    print(f"│ Please enter the new user details   │")
    print(f"└─────────────────────────────────────┘{Style.RESET_ALL}\n")

    username = command_handler.get_input(f"{Fore.CYAN}► Username: {Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Password Requirements:{Style.RESET_ALL}")
    print("• Minimum 8 characters")
    print("• At least one uppercase letter")
    print("• At least one lowercase letter")
    print("• At least one number")
    print("• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    
    password = get_password(f"\n{Fore.CYAN}► Password: {Style.RESET_ALL}")
    confirm = get_password(f"{Fore.CYAN}► Confirm Password: {Style.RESET_ALL}")

    if password != confirm:
        print(f"{Fore.RED}✖  Passwords do not match{Style.RESET_ALL}")
        return True

    print(f"\nSelect role:")
    print("1. Admin")
    print("2. User")
    role_choice = command_handler.get_input(f"{Fore.CYAN}► Choice (1-2): {Style.RESET_ALL}")

    role = ""
    if role_choice == "1":
        role = "admin"
    elif role_choice == "2":
        role = "user"
    else:
        print(f"{Fore.RED}✖  Invalid role choice{Style.RESET_ALL}")
        return True

    return scripts.Database.add_user(username, password, role)

def handle_login():
    global current_user
    
    # Check if root user exists
    if not scripts.Database.has_root_user():
        print(f"\n┌─ {Fore.YELLOW}First Time Setup {Fore.WHITE}──────────────────────┐")
        print(f"│ No root account found. Let's create one │")
        print(f"└─────────────────────────────────────────┘{Style.RESET_ALL}\n")
        
        while True:
            username = command_handler.get_input(f"{Fore.CYAN}► Root Username: {Style.RESET_ALL}")
            
            print(f"\n{Fore.YELLOW}Password Requirements:{Style.RESET_ALL}")
            print("• Minimum 8 characters")
            print("• At least one uppercase letter")
            print("• At least one lowercase letter")
            print("• At least one number")
            print("• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
            
            password = get_password(f"\n{Fore.CYAN}► Password: {Style.RESET_ALL}")
            confirm = get_password(f"{Fore.CYAN}► Confirm Password: {Style.RESET_ALL}")
            
            if password != confirm:
                print(f"\n{Fore.RED}✖  Passwords do not match. Please try again.{Style.RESET_ALL}\n")
                continue
                
            valid, msg = scripts.Database.validate_password_strength(password)
            if not valid:
                print(f"\n{Fore.RED}✖  {msg}{Style.RESET_ALL}\n")
                continue
            
            if scripts.Database.add_user(username, password, "root"):
                print(f"\n{Fore.GREEN}✓  Root account created successfully!{Style.RESET_ALL}")
                current_user = username
                current_session.create(username)
                return True
            else:
                print(f"\n{Fore.RED}✖  Failed to create root account. Please try again.{Style.RESET_ALL}\n")
    
    # Regular login process
    print(f"\n┌─ {Fore.CYAN}Login {Fore.WHITE}──────────────────────────┐")
    print(f"│ Please enter your credentials    │")
    print(f"└──────────────────────────────────┘{Style.RESET_ALL}\n")
    
    username = command_handler.get_input(f"{Fore.CYAN}►  Username: {Style.RESET_ALL}")
    password = get_password(f"\n{Fore.CYAN}►  Password: {Style.RESET_ALL}")
    
    role = scripts.Database.verify_credentials(username, password)
    
    if role:
        current_user = username
        current_session.create(username)
        print(f"\n{Fore.GREEN}Welcome back, {username}!{Style.RESET_ALL}")
        return True
    else:
        if role is None:  # Account might be locked
            return True
        print(f"{Fore.RED}✖  Invalid username or password{Style.RESET_ALL}")
        return True

def handle_update_user(target_user):
    user_role = scripts.Database.get_user_role(target_user)
    
    if not user_role:
        print(f"{Fore.RED}✖  User {target_user} not found{Style.RESET_ALL}")
        return True
        
    if user_role == "root" and target_user == "root":
        print(f"{Fore.RED}✖  Cannot modify the primary root user{Style.RESET_ALL}")
        return True

    while True:
        print(f"\n┌─ {Fore.CYAN}Update User {Fore.WHITE}──────────────────┐")
        print(f"│ 1. Update Username              │")
        print(f"│ 2. Update Password              │")
        print(f"│ 3. Update Role                  │")
        print(f"│ 4. Exit                         │")
        print(f"└──────────────────────────────────┘{Style.RESET_ALL}")
        
        choice = command_handler.get_input(f"{Fore.CYAN}►  Choice (1-4): {Style.RESET_ALL}")
        
        if choice == "1":
            new_name = command_handler.get_input(f"{Fore.CYAN}►  New Username: {Style.RESET_ALL}")
            return scripts.Database.update_user(target_user, new_name=new_name)
        elif choice == "2":
            print(f"\n{Fore.YELLOW}Password Requirements:{Style.RESET_ALL}")
            print("• Minimum 8 characters")
            print("• At least one uppercase letter")
            print("• At least one lowercase letter")
            print("• At least one number")
            print("• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
            
            new_pass = get_password(f"\n{Fore.CYAN}►  New Password: {Style.RESET_ALL}")
            confirm = get_password(f"{Fore.CYAN}►  Confirm Password: {Style.RESET_ALL}")
            
            if new_pass != confirm:
                print(f"{Fore.RED}✖  Passwords do not match{Style.RESET_ALL}")
                continue
                
            return scripts.Database.update_user(target_user, new_password=new_pass)
        elif choice == "3":
            print("\nSelect new role:")
            print("1. Admin")
            print("2. User")
            role_choice = command_handler.get_input(f"{Fore.CYAN}►  Choice (1-2): {Style.RESET_ALL}")
            
            new_role = ""
            if role_choice == "1":
                new_role = "admin"
            elif role_choice == "2":
                new_role = "user"
            else:
                print(f"{Fore.RED}✖  Invalid role choice{Style.RESET_ALL}")
                continue
                
            return scripts.Database.update_user(target_user, new_role=new_role)
        elif choice == "4":
            return True
        else:
            print(f"{Fore.RED}✖  Invalid choice{Style.RESET_ALL}")

def handle_user_command(args):
    """Handle user management commands"""
    if not args:
        print(f"\n┌─ {Fore.CYAN}User Management {Fore.WHITE}────────────────────┐")
        print(f"│ Available Commands:                  │")
        print(f"│ • user create  - Create a new user   │")
        print(f"│ • user delete  - Delete a user       │")
        print(f"│ • user list    - List all users      │")
        print(f"│ • user update  - Update user details │")
        print(f"│ • user upgrade - Upgrade to root     │")
        print(f"└──────────────────────────────────────┘{Style.RESET_ALL}\n")
        return True

    subcommand = args[0]
    
    # Special handling for dev user
    if scripts.Database.config['dev']['enabled'] and current_user == scripts.Database.config['dev']['username']:
        user_role = 'root'
    else:
        user_role = scripts.Database.get_user_role(current_user)
    
    # Debug logging if enabled
    if scripts.Database.config['console']['debug']:
        print(f"\nDEBUG: Current User: {current_user}")
        print(f"DEBUG: User Role: {user_role}")
    
    if subcommand == "create":
        if user_role != 'root':
            print(f"{Fore.RED}✖  Access denied. Root privileges required.{Style.RESET_ALL}")
            return True
        return handle_create_user()
    
    elif subcommand == "delete":
        if user_role != 'root':
            print(f"{Fore.RED}✖  Access denied. Root privileges required.{Style.RESET_ALL}")
            return True
            
        if len(args) != 2:
            print(f"{Fore.RED}✖  Usage: user delete <username>{Style.RESET_ALL}")
            return True
            
        username = args[1]
        if username == current_user:
            print(f"{Fore.RED}✖  Cannot delete your own account{Style.RESET_ALL}")
            return True
            
        print(f"\n{Fore.YELLOW}⚠  Warning: You are about to delete user '{username}'{Style.RESET_ALL}")
        confirm = command_handler.get_input("Are you sure? (y/N): ").lower()
        if confirm != 'y':
            print(f"{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            return True
            
        if scripts.Database.delete_user(username):
            print(f"{Fore.GREEN}✓  User deleted successfully{Style.RESET_ALL}")
        return True
    
    elif subcommand == "list":
        users = scripts.Database.list_users(current_user)
        if users:
            print(f"\n┌─ {Fore.CYAN}User List {Fore.WHITE}────────────────┐")
            for user, role in users:
                # Calculate the actual visible length of the username (excluding ANSI codes)
                visible_length = len(user) - (len(Fore.GREEN) + len(Style.RESET_ALL)) if Fore.GREEN in user else len(user)
                padding = ' ' * (15 - visible_length)  # Adjust padding based on visible length
                
                role_color = {
                    'root': Fore.RED,
                    'admin': Fore.YELLOW,
                    'user': Fore.GREEN
                }.get(role, Fore.WHITE)
                print(f"│ {user}{padding} | {role_color}{role:8}{Style.RESET_ALL} │")
            print(f"└────────────────────────────┘{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.YELLOW}No users found{Style.RESET_ALL}")
        return True
    
    elif subcommand == "update":
        if user_role != 'root':
            print(f"{Fore.RED}✖  Access denied. Root privileges required.{Style.RESET_ALL}")
            return True
            
        if len(args) != 2:
            print(f"{Fore.RED}✖  Usage: user update <username>{Style.RESET_ALL}")
            return True
            
        return handle_update_user(args[1])
    
    elif subcommand == "upgrade":
        if user_role != 'root':
            print(f"{Fore.RED}✖  Access denied. Root privileges required.{Style.RESET_ALL}")
            return True
            
        if len(args) != 2:
            print(f"{Fore.RED}✖  Usage: user upgrade <username>{Style.RESET_ALL}")
            return True
            
        username = args[1]
        print(f"\n{Fore.YELLOW}⚠  Warning: You are about to upgrade '{username}' to root privileges{Style.RESET_ALL}")
        root_password = get_password("Please enter the root password to confirm:\n► Root Password: ")
        
        if scripts.Database.verify_root_password(root_password):
            scripts.Database.upgrade_to_root(username)
        else:
            print(f"{Fore.RED}✖  Invalid root password{Style.RESET_ALL}")
        return True
    
    else:
        print(f"{Fore.RED}✖  Unknown subcommand: {subcommand}{Style.RESET_ALL}")
        return True

def print_user_help():
    print(f"\n┌─ {Fore.CYAN}User Management Commands {Fore.WHITE}───────────────────┐")
    print(f"│ user create                                  │")
    print(f"│ user delete <username>                       │")
    print(f"│ user list                                    │")
    print(f"│ user update <username>                       │")
    print(f"│ user upgrade <username>                      │")
    print(f"│ logout                                       │")
    print(f"└──────────────────────────────────────────────┘{Style.RESET_ALL}\n")

def check_session():
    """Check if the current session is valid"""
    global current_user
    if not current_user:
        return False
        
    if not current_session.validate(current_session.token):
        prev_user = current_user
        current_user = None
        logger.info(f"Session expired for user: {prev_user}")
        print(f"\n{Fore.YELLOW}Session expired. Please log in again.{Style.RESET_ALL}")
        return False
        
    remaining = current_session.get_remaining_time()
    if remaining <= 60:  # Show warning when less than 1 minute remains
        print(f"\n{Fore.YELLOW}Warning: Session will expire in {remaining} seconds{Style.RESET_ALL}")
        
    return True

def print_banner():
    """Print the console banner"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║             P H A N T O M   C O N S O L E                 ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def get_prompt():
    """Get the command prompt with appropriate styling"""
    if not current_user:
        return f"{Fore.WHITE}phantom>{Style.RESET_ALL} "
        
    # Special dev user styling
    if scripts.Database.config['dev']['enabled'] and current_user == scripts.Database.config['dev']['username']:
        return f"{Fore.MAGENTA}[DEV]{Style.RESET_ALL} {Fore.CYAN}{current_user}@phantom>{Style.RESET_ALL} "
        
    # Normal user styling based on role
    role = scripts.Database.get_user_role(current_user)
    role_color = {
        'root': Fore.RED,
        'admin': Fore.YELLOW,
        'user': Fore.GREEN
    }.get(role, Fore.WHITE)
    
    return f"{role_color}{current_user}@phantom>{Style.RESET_ALL} "

def print_dev_warning():
    """Print a warning when dev mode is enabled"""
    if scripts.Database.config['dev']['enabled']:
        print(f"\n{Fore.MAGENTA}╔════════════════════════════════════════╗")
        print(f"{Fore.MAGENTA}║{Style.RESET_ALL}  ⚠  DEVELOPMENT MODE IS ENABLED        {Fore.MAGENTA}║")
        print(f"{Fore.MAGENTA}║{Style.RESET_ALL}  Username: {scripts.Database.config['dev']['username']:<25} {Fore.MAGENTA}  ║")
        print(f"{Fore.MAGENTA}║{Style.RESET_ALL}  Password: {scripts.Database.config['dev']['password']:<25} {Fore.MAGENTA}  ║")
        print(f"{Fore.MAGENTA}╚════════════════════════════════════════╝{Style.RESET_ALL}\n")

def clear_screen():
    os.system('cls')

def print_info():
    """Print information about Phantom Console"""
    version = scripts.Database.config['Version']
    print(f"\n┌─ {Fore.CYAN}About Phantom Console {Fore.WHITE}─────────────┐")
    print(f"│ Version: {Fore.GREEN}{version}{Style.RESET_ALL}{' ' * (27 - len(version))}│")
    print(f"│ Created by: {Fore.YELLOW}Gerrxt{Style.RESET_ALL}{' ' * 18}│")
    print(f"│ GitHub: {Fore.MAGENTA}https://github.com/gerrxt07{Style.RESET_ALL} │")
    print(f"└─────────────────────────────────────┘{Style.RESET_ALL}\n")

def main():
    global current_user
    
    # Start session timeout thread
    timeout_thread = threading.Thread(target=check_session_timeout, daemon=True)
    timeout_thread.start()
    
    clear_screen()
    print_banner()
    print_dev_warning()  # Show dev mode warning if enabled
    
    while True:
        try:
            if not current_user:
                if not handle_login():
                    continue
                clear_screen()
                print_banner()
                command_handler.print_help(current_user)
            
            command = command_handler.get_input(get_prompt()).strip()
            
            if not command:
                continue
                
            if not handle_command(command):
                break
                
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"\n{Fore.RED}An unexpected error occurred. Please try again.{Style.RESET_ALL}")
    
    # Save command history before exit
    command_handler.save_history()
    print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")

def handle_command(command: str) -> bool:
    """Handle a console command"""
    try:
        args = command.strip().split()
        if not args:
            return True
            
        cmd = args[0].lower()
        
        if cmd in ["clear", "cls"]:
            clear_screen()
            print_banner()
            if scripts.Database.config['dev']['enabled']:
                print_dev_warning()
        elif cmd == "help":
            command_handler.print_help(current_user)
        elif cmd == "user":
            return handle_user_command(args[1:] if len(args) > 1 else [])
        elif cmd == "logout":
            return handle_logout()
        elif cmd == "exit":
            return False
        elif cmd == "info":
            print_info()
        else:
            print(f"{Fore.RED}✖  Unknown command: {cmd}{Style.RESET_ALL}")
            command_handler.print_help(current_user)
            
        return True
        
    except Exception as e:
        logger.error(f"Command error: {e}")
        print(f"{Fore.RED}✖  Error executing command: {e}{Style.RESET_ALL}")
        return True

if __name__ == "__main__":
    logger.info("Starting Phantom Console")
    scripts.Startup.start()
    main()