import toml
import requests
import os
import ssl
import certifi
from colorama import Fore
import zipfile
import io
import shutil
import time
import scripts.logging

logger = scripts.logging.logger

# --------------- [ Secure Update Script ] --------------- #

def update():
    logger.info("Updater started.")
    # Use context managers for file operations
    with open('config.toml', 'r', encoding='utf-8') as config_file:
        config = toml.load(config_file)

    version = config['Version']

    def get_latest_version():
        logger.info("Checking for the latest release from GitHub.")
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
            logger.error("SSL Certificate verification failed. Update aborted.")
            print(Fore.RED + "SSL Certificate Verification Failed. Update Aborted.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Update check failed: {e}")
            print(Fore.RED + f"Update Check Failed: {e}")
            return None

    latest_release = get_latest_version()

    if latest_release:
        logger.info(f"Latest release found: {latest_release['tag_name']}")
        latest_version = latest_release['tag_name']

        if latest_version == version:
            pass
        else:
            print(Fore.YELLOW + 'New Update found: ' + Fore.WHITE + latest_version + Fore.YELLOW + ' | Downloading...')
            
            # Download new Version
            try:
                logger.info(f"Attempting to download version {latest_release['tag_name']}")
                # Get the zipball URL from the latest release
                download_url = latest_release['zipball_url']
                
                # Use the same secure request pattern
                headers = {
                    'User-Agent': 'PhantomConsole-Updater',
                    'Accept': 'application/octet-stream'
                }
                
                response = requests.get(
                    download_url,
                    headers=headers,
                    verify=certifi.where(),
                    timeout=30  # Longer timeout for download
                )
                response.raise_for_status()
                
                if response.status_code == 200:
                    # Create a temporary directory for the update
                    temp_dir = 'temp_update'
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir)

                    # Extract the downloaded zip
                    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Get the extracted folder name (it will be the only folder in temp_dir)
                    extracted_dir = os.path.join(temp_dir, os.listdir(temp_dir)[0])
                    
                    # Copy new files to current directory
                    for item in os.listdir(extracted_dir):
                        source = os.path.join(extracted_dir, item)
                        destination = os.path.join('.', item)
                        
                        if os.path.isdir(source):
                            if os.path.exists(destination):
                                shutil.rmtree(destination)
                            shutil.copytree(source, destination)
                        else:
                            shutil.copy2(source, destination)
                    
                    # Update the version in config.toml
                    config['Version'] = latest_version
                    with open('config.toml', 'w') as f:
                        toml.dump(config, f)
                    
                    # Clean up
                    shutil.rmtree(temp_dir)
                    logger.info(f"Successfully updated to version {latest_version}")
                    print(Fore.GREEN + f'Successfully updated to version {latest_version}!')
                    print(Fore.YELLOW + 'Please restart the application to apply the update.')
                    time.sleep(3000)
            except requests.exceptions.SSLError:
                logger.error("SSL Certificate verification failed during download.")
                print(Fore.RED + "SSL Certificate Verification Failed during download. Update Aborted.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Download failed: {e}")
                print(Fore.RED + f"Download Failed: {e}")
            except Exception as e:
                logger.error(f"Error during update: {str(e)}")
                print(Fore.RED + f'Error during update: {str(e)}')
    else:
        logger.error("Could not check for updates.")
        print(Fore.RED + 'Could not check for updates.')