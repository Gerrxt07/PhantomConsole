import sqlite3
from colorama import init, Fore, Style
import bcrypt
from scripts.logging import logger
init(autoreset=True)

database = 'resources/database.db'

def startup():
    logger.info("Initializing database")
    # Create database connection
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    
    # Create user table with hashed password field
    cursor.execute('''CREATE TABLE IF NOT EXISTS user (
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL
                    )''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    logger.debug("Generating password hash")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    # Verify the password against the stored hash
    try:
        logger.debug("Verifying password hash")
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def add_user(name: str, password: str, role: str):
    logger.info(f"Adding new user: {name} with role: {role}")
    try:
        # Hash the password before storing
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO user (name, password_hash, role) VALUES (?, ?, ?)",
                      (name, password_hash, role))
        
        conn.commit()
        logger.info(f"User {name} added successfully")
        return True
    except sqlite3.Error as e:
        error_msg = f"Database error while adding user {name}: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        return False
    finally:
        conn.close()

def verify_credentials(username: str, password: str):
    logger.info(f"Verifying credentials for user: {username}")
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        # Get the stored hash for the user
        cursor.execute("SELECT password_hash, role FROM user WHERE name = ?", (username,))
        result = cursor.fetchone()
        
        if result and verify_password(password, result[0]):
            logger.success(f"Authentication successful for user: {username}")
            return result[1]  # Return the role if password matches
        
        logger.warning(f"Authentication failed for user: {username}")
        return None
        
    except sqlite3.Error as e:
        error_msg = f"Database error during authentication: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        return None
    finally:
        conn.close()

def get_user_role(username: str):
    logger.debug(f"Getting role for user: {username}")
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM user WHERE name = ?", (username,))
        result = cursor.fetchone()
        if result:
            logger.debug(f"Found role for user {username}: {result[0]}")
        else:
            logger.warning(f"No role found for user: {username}")
        return result[0] if result else None
    except sqlite3.Error as e:
        error_msg = f"Database error while getting user role: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        return None
    finally:
        conn.close()

def has_root_user():
    logger.debug("Checking for root user existence")
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'root'")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count > 0:
        logger.debug("Root user found")
    else:
        logger.info("No root user exists")
    return count > 0

def delete_user(name: str):
    logger.info(f"Attempting to delete user: {name}")
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT name FROM user WHERE name = ?", (name,))
        if cursor.fetchone() is None:
            msg = f"User {name} not found"
            logger.warning(msg)
            print(f"{Fore.RED}{msg}{Style.RESET_ALL}")
            return False
            
        # Delete the user
        cursor.execute("DELETE FROM user WHERE name = ?", (name,))
        conn.commit()
        
        msg = f"User {name} deleted successfully"
        logger.info(msg)
        print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}\n")
        return True
        
    except sqlite3.Error as e:
        error_msg = f"Database error while deleting user: {e}"
        logger.error(error_msg)
        print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
        return False
    finally:
        conn.close()

def update_user(name: str, new_name: str = None, new_password: str = None, new_role: str = None):
    logger.info(f"Attempting to update user: {name}")
    try:
        conn = sqlite3.connect(database)
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
        conn = sqlite3.connect(database)
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