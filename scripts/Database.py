from colorama import init, Fore, Style
import sqlite3
import bcrypt
import time
import toml
from scripts.logging import logger

init(autoreset=True)

# Load configuration
with open('config.toml', 'r', encoding='utf-8') as f:
    config = toml.load(f)

database = 'resources/database.db'

def get_db_connection():
    return sqlite3.connect(database)

def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password strength acceptable"

def create_login_tracking_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                username TEXT,
                attempt_time TIMESTAMP,
                success BOOLEAN
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error creating login tracking table: {e}")

def track_login_attempt(username: str, success: bool):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_attempts (username, attempt_time, success) VALUES (?, datetime('now'), ?)",
            (username, success)
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error tracking login attempt: {e}")

def is_account_locked(username: str) -> bool:
    """Check if an account is locked due to too many failed attempts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT login_attempts, last_attempt FROM user WHERE name = ?", (username,))
        result = cursor.fetchone()
        
        if not result:
            return False
            
        attempts, last_attempt = result
        
        # If user has less than max attempts, account is not locked
        if attempts < config['security']['max_login_attempts']:
            return False
            
        # If no last attempt recorded, account is not locked
        if not last_attempt:
            return False
            
        # Check if lockout period has expired
        time_passed = int(time.time()) - last_attempt
        if time_passed > config['security']['lockout_duration']:
            # Reset attempts if lockout period expired
            cursor.execute("UPDATE user SET login_attempts = 0, last_attempt = NULL WHERE name = ?", (username,))
            conn.commit()
            return False
            
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error while checking account lock: {e}")
        return False
    finally:
        conn.close()

def startup():
    """Initialize the database with required tables"""
    logger.info("Initializing database")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create user table with login attempt tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            name TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            login_attempts INTEGER DEFAULT 0,
            last_attempt INTEGER
        )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')  # Store as string

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def add_user(name: str, password: str, role: str):
    logger.info(f"Adding new user: {name} with role: {role}")
    try:
        # Validate password strength
        valid, msg = validate_password_strength(password)
        if not valid:
            logger.warning(msg)
            print(f"{Fore.RED}✖ {msg}{Style.RESET_ALL}")
            return False
        
        # Hash the password before storing
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT COUNT(*) FROM user WHERE name = ?", (name,))
        if cursor.fetchone()[0] > 0:
            logger.warning(f"Username {name} already exists")
            print(f"{Fore.RED}✖ Username already exists{Style.RESET_ALL}")
            return False
        
        cursor.execute("INSERT INTO user (name, password_hash, role) VALUES (?, ?, ?)",
                      (name, password_hash, role))
        
        conn.commit()
        logger.info(f"User {name} added successfully")
        return True
    except sqlite3.Error as e:
        error_msg = f"Database error while adding user {name}: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}✖ {error_msg}{Style.RESET_ALL}")
        return False
    finally:
        conn.close()

def verify_credentials(name: str, password: str) -> str:
    """Verify user credentials and return their role if valid"""
    logger.debug(f"Verifying credentials for user: {name}")
    
    # Check dev user credentials if dev mode is enabled
    if config['dev']['enabled'] and name == config['dev']['username'] and password == config['dev']['password']:
        logger.info("Dev user login successful")
        return "root"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if account is locked
        if is_account_locked(name):
            print(f"{Fore.RED}✖ Account is locked. Please try again later.{Style.RESET_ALL}")
            return None
        
        cursor.execute("SELECT password_hash, role, login_attempts FROM user WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"Failed login attempt: User {name} not found")
            return ""
            
        stored_hash, role, attempts = result
        
        if verify_password(password, stored_hash):
            # Reset login attempts on successful login
            cursor.execute("UPDATE user SET login_attempts = 0, last_attempt = NULL WHERE name = ?", (name,))
            conn.commit()
            logger.info(f"User {name} logged in successfully")
            return role
        else:
            # Increment login attempts
            new_attempts = attempts + 1
            cursor.execute("UPDATE user SET login_attempts = ?, last_attempt = ? WHERE name = ?",
                         (new_attempts, int(time.time()), name))
            conn.commit()
            
            if new_attempts >= config['security']['max_login_attempts']:
                logger.warning(f"Account {name} locked due to too many failed attempts")
                print(f"{Fore.RED}✖ Too many failed attempts. Account has been locked.{Style.RESET_ALL}")
            else:
                remaining = config['security']['max_login_attempts'] - new_attempts
                print(f"{Fore.YELLOW}⚠ {remaining} attempts remaining{Style.RESET_ALL}")
                
            return ""
            
    except sqlite3.Error as e:
        logger.error(f"Database error while verifying credentials: {e}")
        return ""
    finally:
        conn.close()

def get_user_role(username: str) -> str:
    """Get the role of a user"""
    # Check if dev mode is enabled and this is the dev user
    if config['dev']['enabled'] and username == config['dev']['username']:
        return 'root'
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM user WHERE name = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            logger.warning(f"No role found for user: {username}")
            return None
            
    except sqlite3.Error as e:
        logger.error(f"Database error while getting user role: {e}")
        return None
    finally:
        conn.close()

def has_root_user():
    """Check if any root user exists in the database"""
    logger.debug("Checking for root user existence")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'root'")
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        logger.error(f"Database error while checking for root user: {e}")
        return False
    finally:
        conn.close()

def delete_user(name: str) -> bool:
    """Delete a user from the database"""
    logger.info(f"Attempting to delete user: {name}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists and get their role
        cursor.execute("SELECT role FROM user WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"User {name} not found")
            print(f"{Fore.RED}✖ User not found{Style.RESET_ALL}")
            return False
            
        if result[0] == 'root':
            logger.warning(f"Attempted to delete root user {name}")
            print(f"{Fore.RED}✖ Cannot delete root users{Style.RESET_ALL}")
            return False
        
        cursor.execute("DELETE FROM user WHERE name = ?", (name,))
        conn.commit()
        
        logger.info(f"Successfully deleted user {name}")
        return True
        
    except sqlite3.Error as e:
        error_msg = f"Database error while deleting user: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}✖ {error_msg}{Style.RESET_ALL}")
        return False
    finally:
        conn.close()

def update_user(name: str, new_name: str = None, new_password: str = None, new_role: str = None):
    logger.info(f"Attempting to update user: {name}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists and get current role
        cursor.execute("SELECT role FROM user WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if not result:
            msg = f"User {name} not found"
            logger.warning(msg)
            print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
            return False
            
        current_role = result[0]
        
        # Prevent modifying root users
        if current_role == 'root' and (new_role or new_name):
            msg = "Cannot modify root user's name or role"
            logger.warning(msg)
            print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
            return False
        
        # Build update query dynamically
        updates = []
        params = []
        
        if new_name:
            updates.append("name = ?")
            params.append(new_name)
            
        if new_password:
            # Validate password strength
            valid, msg = validate_password_strength(new_password)
            if not valid:
                logger.warning(msg)
                print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
                return False
            
            updates.append("password_hash = ?")
            params.append(hash_password(new_password))
            
        if new_role:
            if new_role not in ['admin', 'user']:
                msg = "Invalid role. Must be 'admin' or 'user'"
                logger.warning(msg)
                print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
                return False
            updates.append("role = ?")
            params.append(new_role)
            
        if not updates:
            msg = "No updates specified"
            logger.warning(msg)
            print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")
            return False
            
        # Add the WHERE clause parameter
        params.append(name)
        
        # Execute update
        query = f"UPDATE user SET {', '.join(updates)} WHERE name = ?"
        cursor.execute(query, params)
        conn.commit()
        
        msg = f"User {name} updated successfully"
        logger.info(msg)
        print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}\n")
        return True
        
    except sqlite3.Error as e:
        error_msg = f"Database error while updating user: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        return False
    finally:
        conn.close()

def list_users():
    logger.info("Listing all users")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, role FROM user ORDER BY role DESC, name ASC")
        users = cursor.fetchall()
        return users
    except sqlite3.Error as e:
        error_msg = f"Database error while listing users: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        return None
    finally:
        conn.close()

def validate_role(role: str) -> bool:
    return role.lower() in ['admin', 'user', 'root']

def verify_root_password(password: str) -> bool:
    """Verify the root user's password"""
    logger.debug("Verifying root password")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM user WHERE role = 'root' LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            logger.error("No root user found")
            return False
            
        stored_hash = result[0]
        return verify_password(password, stored_hash)
    except Exception as e:
        logger.error(f"Error verifying root password: {e}")
        return False
    finally:
        conn.close()

def upgrade_to_root(name: str) -> bool:
    """Upgrade a user to root privileges"""
    logger.info(f"Attempting to upgrade user {name} to root")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists and isn't already root
        cursor.execute("SELECT role FROM user WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"User {name} not found")
            print(f"{Fore.RED}✖ User not found{Style.RESET_ALL}")
            return False
            
        if result[0] == 'root':
            logger.warning(f"User {name} is already root")
            print(f"{Fore.YELLOW}⚠ User is already root{Style.RESET_ALL}")
            return False
        
        print(f"\n{Fore.YELLOW}⚠ Warning: You are about to upgrade '{name}' to root privileges{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}Please enter the root password to confirm:{Style.RESET_ALL}")
        from PhantomConsole import get_password
        root_password = get_password(f"{Fore.MAGENTA}► Root Password: {Style.RESET_ALL}")
        
        if not verify_root_password(root_password):
            logger.warning("Root password verification failed")
            print(f"{Fore.RED}✖ Root password verification failed{Style.RESET_ALL}")
            return False
        
        # Update user role to root
        cursor.execute("UPDATE user SET role = 'root' WHERE name = ?", (name,))
        conn.commit()
        
        logger.info(f"Successfully upgraded {name} to root")
        print(f"{Fore.GREEN}✓ Successfully upgraded user to root{Style.RESET_ALL}")
        return True
        
    except sqlite3.Error as e:
        error_msg = f"Database error while upgrading user: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}✖ {error_msg}{Style.RESET_ALL}")
        return False
    finally:
        conn.close()

def handle_password_change(username: str) -> bool:
    print(f"\n{Fore.YELLOW}Password Requirements:{Style.RESET_ALL}")
    print("• Minimum 8 characters")
    print("• At least one uppercase letter")
    print("• At least one lowercase letter")
    print("• At least one number")
    print("• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
    
    while True:
        new_pass = get_password(f"\n{Fore.CYAN}► New Password: {Style.RESET_ALL}")
        confirm = get_password(f"{Fore.CYAN}► Confirm Password: {Style.RESET_ALL}")
        
        if new_pass != confirm:
            print(f"{Fore.RED}✖ Passwords do not match{Style.RESET_ALL}")
            continue
            
        valid, msg = validate_password_strength(new_pass)
        if not valid:
            print(f"{Fore.RED}✖ {msg}{Style.RESET_ALL}")
            continue
            
        return update_user(username, new_password=new_pass)

def get_new_password() -> str:
    return get_password(f"{Fore.CYAN}► Enter your new password to login: {Style.RESET_ALL}")