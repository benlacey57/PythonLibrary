from ..config.config_manager import ConfigManager

class Configurable:
    """
    Interface for components that need configuration.
    
    Provides standard methods for configuration management.
    """
    
    def configure(self, config=None):
        """
        Configure the component.
        
        Args:
            config: Configuration source (ConfigManager, dict, or None).
        """
        if config is None:
            self.config = ConfigManager()
        elif isinstance(config, dict):
            self.config = ConfigManager()
            for key, value in config.items():
                if isinstance(value, dict):
                    for subkey, subvalue in self._flatten_dict(value, prefix=key):
                        self.config.set(subkey, subvalue)
                else:
                    self.config.set(key, value)
        else:
            self.config = config
    
    def _flatten_dict(self, d, prefix=""):
        """
        Flatten a nested dictionary with dot notation.
        
        Args:
            d (dict): Dictionary to flatten.
            prefix (str): Prefix for keys.
            
        Yields:
            tuple: (key, value) pairs with flattened keys.
        """
        for key, value in d.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                yield from self._flatten_dict(value, new_key)
            else:
                yield (new_key, value)