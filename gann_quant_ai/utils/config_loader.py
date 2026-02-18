import yaml
from loguru import logger
from typing import Dict
import os

def load_config(path: str) -> Dict:
    """Loads a single YAML configuration file."""
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at: {path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration from {path}: {e}")
        return {}

def load_all_configs(config_dir: str = "config") -> Dict:
    """
    Loads all .yaml configuration files from a directory into a nested dictionary.
    """
    logger.info(f"Loading all configurations from directory: '{config_dir}'")

    all_configs = {}
    config_files = [f for f in os.listdir(config_dir) if f.endswith(('.yaml', '.yml'))]

    for file_name in config_files:
        config_key = file_name.replace('.yaml', '').replace('.yml', '')
        file_path = os.path.join(config_dir, file_name)
        config_data = load_config(file_path)
        if config_data:
            all_configs[config_key] = config_data

    if not all_configs:
        logger.error("No configuration files were loaded. The system may not function correctly.")
        return {}

    logger.success("All configuration files loaded successfully.")
    return all_configs

# Example Usage
if __name__ == '__main__':
    # Assuming this is run from the root of the gann_quant_ai project
    configs = load_all_configs()

    if configs:
        print("\n--- Loaded Configurations ---")
        import json
        # Printing strategy_config as an example
        print("Strategy Config:", json.dumps(configs.get('strategy_config'), indent=2))
        print("\nRisk Config:", json.dumps(configs.get('risk_config'), indent=2))
        print("---------------------------")
