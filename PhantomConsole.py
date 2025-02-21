import scripts.Startup
import scripts.Database
from colorama import init, Style, Fore
import msvcrt
import os
from scripts.logging import logger
init(autoreset=True)

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

def handle_login():
    if not scripts.Database.has_root_user():
        print(f"\n┌─ {Fore.YELLOW}First Time Setup {Fore.WHITE}─────────────────────┐")
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

def handle_command(command):
    if command.lower() == "exit":
        logger.info("User requested exit")
        return False
    elif command.lower() in ["clear", "cls"]:
        logger.debug("Clearing screen")
        clear_screen()
        return True
    elif command.lower() == "help":
        logger.debug("Showing help menu")
        print(f"\n┌─ {Fore.CYAN}Available Commands {Fore.WHITE}───────────────────┐")
        print(f"│ clear, cls  - Clear the console        │")
        print(f"│ help        - Show this help message   │")
        print(f"│ exit        - Exit Phantom Console     │")
        print(f"└────────────────────────────────────────┘{Style.RESET_ALL}\n")
        return True
    else:
        # Add your command handling logic here
        logger.info(f"Executing command: {command}")
        print(f"{Fore.YELLOW}► Executing: {command}{Style.RESET_ALL}")
        return True

def main():
    logger.info("Starting Phantom Console")
    scripts.Startup.start()
    
    username = handle_login()
    clear_screen()
    logger.info(f"Starting command loop for user: {username}")
    
    while True:
        try:
            prompt = f"{Fore.GREEN}{username}@Phantom{Fore.CYAN}~{Fore.WHITE}$ {Style.RESET_ALL}"
            command = input(prompt).strip()
            
            if not command:
                continue
            
            if not handle_command(command):
                logger.info("Shutting down Phantom Console")
                break
            
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt received")
            print(f"\n{Fore.YELLOW}► Use 'exit' to quit Phantom Console{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            print(f"\n{Fore.RED}✖ Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()