import toml
import requests
import os
from colorama import Fore
import zipfile
import io
import shutil
import time
import requests

# --------------- [ Update Script ] --------------- #

def update():
    with open('config.toml', mode='r') as config_file:
        config = toml.load(config_file)

    version = config['Version']

    def get_latest_version():
        url = 'https://api.github.com/repos/Gerrxt07/PhantomConsole/releases/latest'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    latest_release = get_latest_version()

    if latest_release:
        latest_version = latest_release['tag_name']

        if latest_version == version:
            pass
        else:
            print(Fore.YELLOW + 'New Update found: ' + Fore.WHITE + latest_version + Fore.YELLOW + ' | Downloading...')
            
            # Download new Version
            try:
                # Get the zipball URL from the latest release
                download_url = latest_release['zipball_url']
                response = requests.get(download_url)
                
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
                    print(Fore.GREEN + f'Successfully updated to version {latest_version}!')
                    print(Fore.YELLOW + 'Please restart the application to apply the update.')
                    time.sleep(3000)
                else:
                    print(Fore.RED + 'Failed to download the update.')
            except Exception as e:
                print(Fore.RED + f'Error during update: {str(e)}')
    else:
        print(Fore.RED + 'Could not check for updates.')