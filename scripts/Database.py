import sqlite3
from colorama import init, Fore, Style
import bcrypt
init(autoreset=True)

database = 'resources/database.db'

def startup():
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
    print(Fore.GREEN + "Database initialized successfully!")

def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    # Verify the password against the stored hash
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def add_user(name: str, password: str, role: str) -> bool:
    try:
        # Hash the password before storing
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO user (name, password_hash, role) VALUES (?, ?, ?)",
                      (name, password_hash, role))
        
        conn.commit()
        conn.close()
        print(Fore.GREEN + f"User" + Fore.WHITE + f" {name}" + Fore.GREEN + f" added successfully!")
        return True
    except sqlite3.IntegrityError:
        print(Fore.RED + f"Error: User" + Fore.WHITE + f" {name}" + Fore.RED + f" already exists!")
        return False
    except sqlite3.Error as e:
        print(Fore.RED + f"Database error: {e}")
        return False

def delete_user(name: str) -> bool:
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        # Check if user exists and get role
        cursor.execute("SELECT role FROM user WHERE name = ?", (name,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print(Fore.RED + "Error: User" + Fore.WHITE + f" {name}" + Fore.RED + " not found!")
            return False
            
        role = user_data[0]
        if role.lower() == "root":
            print(Fore.RED + "Error: User" + Fore.WHITE + f" {name}" + Fore.RED + " is root and cannot be deleted!")
            return False
            
        # Delete the user
        cursor.execute("DELETE FROM user WHERE name = ?", (name,))
        conn.commit()
        conn.close()
        print(Fore.GREEN + "User" + Fore.WHITE + f" {name}" + Fore.GREEN + " deleted successfully!")
        return True
        
    except sqlite3.Error as e:
        print(Fore.RED + f"Database error: {e}")
        return False

def has_root_user():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'root'")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def verify_credentials(username: str, password: str):
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        
        # Get the stored hash for the user
        cursor.execute("SELECT password_hash, role FROM user WHERE name = ?", (username,))
        result = cursor.fetchone()
        
        if result and verify_password(password, result[0]):
            return result[1]  # Return the role if password matches
        return None
        
    except sqlite3.Error as e:
        print(Fore.RED + f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_user_role(username: str):
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM user WHERE name = ?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(Fore.RED + f"Database error: {e}")
        return None
    finally:
        conn.close()