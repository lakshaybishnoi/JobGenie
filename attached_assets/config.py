import json
import os
from typing import Any, Dict

class Config:
    """Configuration manager for JobGenie application."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default config."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._get_default_config()
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return {
            'job_keywords': '',
            'location': '',
            'experience_level': '',
            'job_type': '',
            'max_results': 25,
            'min_match_score': 50,
            'scraping_delay': 1,  # seconds between requests
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def save_config(self) -> None:
        """Save current settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.settings.get(key, default)
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a specific setting."""
        self.settings[key] = value
        self.save_config()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update multiple settings at once."""
        self.settings.update(new_settings)
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self.settings = self._get_default_config()
        self.save_config()
