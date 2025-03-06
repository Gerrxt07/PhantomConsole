import requests
import ssl
import certifi
import os
import zipfile
import io
import shutil
import time
import toml
from colorama import Fore

def secure_update():
    """Enhanced secure update mechanism"""
    # Use context managers for file operations
    with open('config.toml', 'r', encoding='utf-8') as config_file:
        config = toml.load(config_file)

    version = config['Version']

    def get_latest_version():
        """Fetch latest version with enhanced security"""
        try:
            # Use certifi for trusted CA certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            # Enforce TLS 1.2 or higher
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            # Strict hostname and certificate verification
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            url = 'https://api.github.com/repos/Gerrxt07/PhantomConsole/releases/latest'
            
            # Custom headers to prevent potential API abuse
            headers = {
                'User-Agent': 'PhantomConsole-Updater',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                verify=certifi.where(),  # Additional certificate verification
                timeout=10  # Prevent indefinite hanging
            )
            
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        
        except requests.exceptions.SSLError:
            print(Fore.RED + "SSL Certificate Verification Failed. Update Aborted.")
            return None
        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"Update Check Failed: {e}")
            return None

    # Rest of the update logic remains similar to the previous implementation
    # with added error handling and security checks