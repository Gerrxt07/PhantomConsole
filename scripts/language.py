import json
import toml

# Load the configuration file
with open('config.toml', 'r', encoding='utf-8') as config_file:
    config = toml.load(config_file)

# Get the language setting from the configuration
lang = config['language']

# Load the language strings from the corresponding JSON file
with open(f"resources/lang/{lang}.json", 'r', encoding='utf-8') as f:
    strings = json.load(f)

def get_language(message):
    # Return the translated message if it exists, otherwise return the original message
    return strings.get(message, message)