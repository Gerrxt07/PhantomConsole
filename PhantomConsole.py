import scripts.Startup
import scripts.Database
from colorama import init, Style, Fore
import msvcrt
import os
import time
import threading
from scripts.logging import logger
init(autoreset=True)

# Global variables for session management
current_user = None
last_activity_time = None
SESSION_TIMEOUT = 300  # 5 minutes in seconds

def update_activity():
    global last_activity_time
    last_activity_time = time.time()

def check_session_timeout():
    while True:
        if current_user and last_activity_time:
            if time.time() - last_activity_time > SESSION_TIMEOUT:
                logger.info(f"Session timeout for user: {current_user}")
                print(f"\n{Fore.YELLOW}Session timed out due to inactivity{Style.RESET_ALL}")
                handle_logout()
        time.sleep(1)

def handle_logout():
    global current_user
    if current_user:
        prev_user = current_user
        current_user = None
        os.system('cls')
        logger.info(f"User logged out: {prev_user}")
        print(f"\n{Fore.GREEN}Logged out successfully{Style.RESET_ALL}")
        return True
    return False

def get_password(prompt):
    print(prompt, end='', flush=True)
    password = ""
    while True:
        char = msvcrt.getch()
        if char in [b'\r', b'\n']:  # Enter key
            print()
            return password
        elif char == b'\x08':  # Backspace
            if password:
                password = password[:-1]
                print('\b \b', end='', flush=True)  # Remove last * 
        elif char == b'\x03':  # Ctrl+C
            raise KeyboardInterrupt
        else:
            char_str = char.decode('utf-8', errors='ignore')
            if char_str.isprintable():
                password += char_str
                print('*', end='', flush=True)

def handle_create_user():
    if scripts.Database.get_user_role(current_user) != 'root':
        logger.warning(f"User {current_user} attempted to create user without root access")
        print(f"{Fore.RED}✖ Access denied. Root privileges required.{Style.RESET_ALL}")
        return True

    print(f"\n┌─ {Fore.CYAN}Create New User {Fore.WHITE}───────────────────┐")
    print(f"│ Please enter the new user details   │")
    print(f"└─────────────────────────────────────┘{Style.RESET_ALL}\n")

    username = input(f"{Fore.CYAN}► Username: {Style.RESET_ALL}")
    password = get_password(f"{Fore.CYAN}► Password: {Style.RESET_ALL}")
    confirm_password = get_password(f"{Fore.CYAN}► Confirm password: {Style.RESET_ALL}")
    
    if password != confirm_password:
        print(f"\n{Fore.RED}✖ Passwords do not match{Style.RESET_ALL}")
        return True
        
    print(f"\n{Fore.YELLOW}Select role:")
    print(f"1) Admin")
    print(f"2) User{Style.RESET_ALL}")
    
    while True:
        role_choice = input(f"{Fore.CYAN}► Choice (1-2): {Style.RESET_ALL}")
        if role_choice == "1":
            role = "admin"
            break
        elif role_choice == "2":
            role = "user"
            break
        print(f"{Fore.RED}✖ Invalid choice{Style.RESET_ALL}")
    
    scripts.Database.add_user(username, password, role)
    return True

def handle_user_command(username: str, args: list):
    # Check if user has root privileges
    if scripts.Database.get_user_role(username) != 'root':
        logger.warning(f"User {username} attempted to use user management commands without root access")
        print(f"{Fore.RED}✖ Access denied. Root privileges required.{Style.RESET_ALL}")
        return True

    if not args:
        print_user_help()
        return True

    subcommand = args[0].lower()
    
    if subcommand == "delete":
        if len(args) != 2:
            print(f"{Fore.RED}✖ Usage: user delete <username>{Style.RESET_ALL}")
            return True
            
        target_user = args[1]
        user_role = scripts.Database.get_user_role(target_user)
        
        if not user_role:
            print(f"{Fore.RED}✖ User {target_user} not found{Style.RESET_ALL}")
            return True
            
        if user_role == 'root':
            print(f"{Fore.RED}✖ Cannot delete root users{Style.RESET_ALL}")
            return True
            
        scripts.Database.delete_user(target_user)
        
    elif subcommand == "list":
        users = scripts.Database.list_users()
        if users:
            print(f"\n┌─ {Fore.CYAN}User List {Fore.WHITE}──────────────────┐")
            for user, role in users:
                role_color = {
                    'root': Fore.RED,
                    'admin': Fore.YELLOW,
                    'user': Fore.GREEN
                }.get(role, Fore.WHITE)
                print(f"│ {user:15} | {role_color}{role:10}{Fore.WHITE} │")
            print(f"└──────────────────────────────┘{Style.RESET_ALL}")
    
    elif subcommand == "create":
        return handle_create_user()

    elif subcommand == "update":
        if len(args) != 2:
            print(f"{Fore.RED}✖ Usage: user update <username>{Style.RESET_ALL}")
            return True
            
        target_user = args[1]
        user_role = scripts.Database.get_user_role(target_user)
        
        if not user_role:
            print(f"{Fore.RED}✖ User {target_user} not found{Style.RESET_ALL}")
            return True
            
        print(f"\n{Fore.YELLOW}Select field to update:")
        print(f"1) Username")
        print(f"2) Password")
        if user_role != 'root':
            print(f"3) Role{Style.RESET_ALL}")
        
        while True:
            field_choice = input(f"{Fore.CYAN}► Choice: {Style.RESET_ALL}")
            if field_choice == "1":
                new_value = input(f"{Fore.CYAN}► New username: {Style.RESET_ALL}")
                scripts.Database.update_user(target_user, new_name=new_value)
                break
            elif field_choice == "2":
                new_value = get_password(f"{Fore.CYAN}► New password: {Style.RESET_ALL}")
                confirm = get_password(f"{Fore.CYAN}► Confirm password: {Style.RESET_ALL}")
                if new_value != confirm:
                    print(f"{Fore.RED}✖ Passwords do not match{Style.RESET_ALL}")
                    continue
                scripts.Database.update_user(target_user, new_password=new_value)
                break
            elif field_choice == "3" and user_role != 'root':
                print(f"\n{Fore.YELLOW}Select new role:")
                print(f"1) Admin")
                print(f"2) User{Style.RESET_ALL}")
                while True:
                    role_choice = input(f"{Fore.CYAN}► Choice (1-2): {Style.RESET_ALL}")
                    if role_choice == "1":
                        scripts.Database.update_user(target_user, new_role="admin")
                        break
                    elif role_choice == "2":
                        scripts.Database.update_user(target_user, new_role="user")
                        break
                    print(f"{Fore.RED}✖ Invalid choice{Style.RESET_ALL}")
                break
            print(f"{Fore.RED}✖ Invalid choice{Style.RESET_ALL}")
    else:
        print_user_help()
    
    return True

def print_user_help():
    print(f"\n┌─ {Fore.CYAN}User Management Commands {Fore.WHITE}───────────────────┐")
    print(f"│ user create                                  │")
    print(f"│ user delete <username>                       │")
    print(f"│ user list                                    │")
    print(f"│ user update <username>                       │")
    print(f"│ logout                                       │")
    print(f"└──────────────────────────────────────────────┘{Style.RESET_ALL}\n")

def handle_command(command):
    update_activity()
    
    args = command.split()
    if not args:
        return True
        
    cmd = args[0].lower()
    if cmd == "exit":
        logger.info("User requested exit")
        return False
    elif cmd in ["clear", "cls"]:
        logger.debug("Clearing screen")
        clear_screen()
        return True
    elif cmd == "help":
        logger.debug("Showing help menu")
        print(f"\n┌─ {Fore.CYAN}Available Commands {Fore.WHITE}───────────────────┐")
        print(f"│ clear, cls  - Clear the console        │")
        print(f"│ help        - Show this help message   │")
        print(f"│ user        - User management (root)   │")
        print(f"│ logout      - Log out current user     │")
        print(f"│ exit        - Exit Phantom Console     │")
        print(f"└────────────────────────────────────────┘{Style.RESET_ALL}\n")
        return True
    elif cmd == "user":
        return handle_user_command(current_user, args[1:] if len(args) > 1 else [])
    elif cmd == "logout":
        return handle_logout()
    else:
        # Add your command handling logic here
        logger.info(f"Executing command: {command}")
        print(f"{Fore.YELLOW}► Executing: {command}{Style.RESET_ALL}")
        return True

def handle_login():
    if not scripts.Database.has_root_user():
        print(f"\n┌─ {Fore.YELLOW}First Time Setup {Fore.WHITE}──────────────────────┐")
        print(f"│ No root account found. Let's create one │")
        print(f"└─────────────────────────────────────────┘{Style.RESET_ALL}\n")
        
        while True:
            username = input(f"{Fore.CYAN}► Username: {Style.RESET_ALL}")
            password = get_password(f"{Fore.CYAN}► Password: {Style.RESET_ALL}")
            confirm_password = get_password(f"{Fore.CYAN}► Confirm password: {Style.RESET_ALL}")
            
            if password != confirm_password:
                logger.warning("Password confirmation failed during root account creation")
                print(f"\n{Fore.RED}✖ Passwords do not match. Please try again.{Style.RESET_ALL}\n")
                continue
            
            scripts.Database.add_user(username, password, "root")
            logger.info(f"Root account created for user: {username}")
            print(f"\n{Fore.GREEN}✓ Root account created successfully!{Style.RESET_ALL}\n")
            return username
    
    while True:
        username = input(f"{Fore.CYAN}► Username: {Style.RESET_ALL}")
        password = get_password(f"{Fore.CYAN}► Password: {Style.RESET_ALL}")
        
        role = scripts.Database.verify_credentials(username, password)
        if role:
            logger.info(f"User {username} logged in successfully")
            print(f"\n{Fore.GREEN}✓ Authentication successful!{Style.RESET_ALL}")
            return username
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            print(f"\n{Fore.RED}✖ Invalid credentials. Please try again.{Style.RESET_ALL}\n")

def clear_screen():
    os.system('cls')

def main():
    logger.info("Starting Phantom Console")
    scripts.Startup.start()
    
    # Start session timeout checker in a separate thread
    timeout_thread = threading.Thread(target=check_session_timeout, daemon=True)
    timeout_thread.start()
    
    while True:
        global current_user
        current_user = handle_login()
        update_activity()
        clear_screen()
        logger.info(f"Starting command loop for user: {current_user}")
        
        while current_user:
            try:
                prompt = f"{Fore.GREEN}{current_user}@Phantom{Fore.CYAN}~{Fore.WHITE}$: {Style.RESET_ALL}"
                command = input(prompt).strip()
                
                if not command:
                    continue
                
                if not handle_command(command):
                    logger.info("Shutting down Phantom Console")
                    return
                
            except KeyboardInterrupt:
                logger.warning("KeyboardInterrupt received")
                print(f"\n{Fore.YELLOW}► Use 'exit' to quit Phantom Console{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                print(f"\n{Fore.RED}✖ Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()