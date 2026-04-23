"""
Configuration management for data sources and API keys.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration for the email finder."""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.find_email'
        self.config_dir.mkdir(exist_ok=True)

        self.config_file = self.config_dir / 'config.json'
        self.api_keys_file = self.config_dir / 'api_keys.json'

        self.config = self._load_config()
        self.api_keys = self._load_api_keys()

    def _load_config(self) -> Dict[str, Any]:
        """Load main configuration."""
        default_config = {
            'data_sources': {
                'tianyancha': {'enabled': True, 'rate_limit': 2.0},
                'qichacha': {'enabled': True, 'rate_limit': 2.0},
                'github': {'enabled': True, 'rate_limit': 1.0},
                'stackoverflow': {'enabled': True, 'rate_limit': 1.0}
            },
            'verification': {
                'dnsbl_check': True,
                'smtp_timeout': 10,
                'max_retries': 3
            },
            'ai_learning': {
                'enabled': True,
                'history_limit': 1000,
                'auto_learn': True
            },
            'output': {
                'default_format': 'text',
                'show_debug': False
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    user_config = json.load(f)
                    # Deep merge with defaults
                    self._deep_merge(default_config, user_config)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")

        return default_config

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys."""
        default_keys = {
            'tianyancha': '',
            'qichacha': '',
            'github': '',
            'stackoverflow': '',
            'hunterio': '',
            'zerointel': '',
            'apollo': ''
        }

        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file) as f:
                    user_keys = json.load(f)
                    default_keys.update(user_keys)
            except Exception as e:
                print(f"Warning: Could not load API keys: {e}")

        # Also check environment variables
        for key in default_keys:
            env_key = f"{key.upper()}_API_KEY"
            if env_key in os.environ:
                default_keys[key] = os.environ[env_key]

        return default_keys

    def _deep_merge(self, base: dict, update: dict):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def save_api_keys(self):
        """Save API keys to file."""
        # Only save non-empty keys
        keys_to_save = {k: v for k, v in self.api_keys.items() if v}
        with open(self.api_keys_file, 'w') as f:
            json.dump(keys_to_save, f, indent=2)

    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service."""
        return self.api_keys.get(service)

    def set_api_key(self, service: str, key: str):
        """Set API key for a service."""
        self.api_keys[service] = key
        self.save_api_keys()

    def get_config(self, section: str = None) -> Dict[str, Any]:
        """Get configuration section."""
        if section:
            return self.config.get(section, {})
        return self.config

    def update_config(self, section: str, key: str, value: Any):
        """Update configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()

    def is_data_source_enabled(self, source: str) -> bool:
        """Check if a data source is enabled."""
        return self.config.get('data_sources', {}).get(source, {}).get('enabled', False)

    def get_data_source_config(self, source: str) -> Dict[str, Any]:
        """Get configuration for a data source."""
        return self.config.get('data_sources', {}).get(source, {})

    def get_enabled_data_sources(self) -> list:
        """Get list of enabled data sources."""
        sources = []
        for name, config in self.config.get('data_sources', {}).items():
            if config.get('enabled', False):
                sources.append(name)
        return sources

    def create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = {
            'data_sources': {
                'tianyancha': {
                    'enabled': True,
                    'rate_limit': 2.0,
                    'description': 'Chinese business information API'
                },
                'qichacha': {
                    'enabled': True,
                    'rate_limit': 2.0,
                    'description': 'Chinese business information API'
                },
                'github': {
                    'enabled': True,
                    'rate_limit': 1.0,
                    'description': 'GitHub public data'
                },
                'stackoverflow': {
                    'enabled': True,
                    'rate_limit': 1.0,
                    'description': 'Stack Overflow public data'
                }
            },
            'verification': {
                'dnsbl_check': True,
                'smtp_timeout': 10,
                'max_retries': 3,
                'description': 'Email verification settings'
            },
            'ai_learning': {
                'enabled': True,
                'history_limit': 1000,
                'auto_learn': True,
                'description': 'AI pattern learning settings'
            },
            'output': {
                'default_format': 'text',
                'show_debug': False,
                'description': 'Output formatting settings'
            }
        }

        sample_file = self.config_dir / 'sample_config.json'
        with open(sample_file, 'w') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)

        return str(sample_file)

    def create_sample_api_keys(self):
        """Create a sample API keys file."""
        sample_keys = {
            'tianyancha': 'your_tianyancha_api_key_here',
            'qichacha': 'your_qichacha_api_key_here',
            'github': 'your_github_personal_access_token',
            'stackoverflow': 'your_stackexchange_api_key',
            'hunterio': 'your_hunterio_api_key',
            'zerointel': 'your_zerointel_api_key',
            'apollo': 'your_apollo_api_key',
            'note': 'Replace with your actual API keys. You can also set them as environment variables.'
        }

        sample_file = self.config_dir / 'sample_api_keys.json'
        with open(sample_file, 'w') as f:
            json.dump(sample_keys, f, indent=2, ensure_ascii=False)

        return str(sample_file)