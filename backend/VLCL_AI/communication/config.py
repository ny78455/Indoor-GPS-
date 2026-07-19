# config.py
import yaml
from typing import Optional, Dict, Any

class CommunicationConfig:
    """Manages system-level configurations for the physical-layer communication simulator."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = {
            "enabled": True,
            "bandwidth_hz": 20e6,
            "sample_rate_hz": 50e6,
            "fft_size": 256,
            "cyclic_prefix_ratio": 0.125,
            "ofdm_type": "DCO_OFDM",
            "dc_bias_sigma": 3.0,
            "clipping": {
                "enabled": True,
                "min_value": 0.0,
                "max_value": 2.0
            },
            "modulation": {
                "default_order": 16,
                "supported_orders": [4, 16, 64, 256]
            },
            "subcarriers": {
                "guard_low": 4,
                "guard_high": 4,
                "pilot_spacing": 16,
                "reserve_localization_group": True
            },
            "led_frequency_response": {
                "enabled": True,
                "model": "first_order",
                "cutoff_frequency_hz": 20e6
            },
            "pre_equalization": {
                "enabled": False,
                "mode": "regularized",
                "regularization": 1e-4,
                "max_gain": 10.0
            },
            "receiver": {
                "equalizer": "MMSE",
                "perfect_csi": True
            },
            "adc": {
                "mode": "ideal",
                "bits": 12,
                "full_scale_voltage": 2.0
            },
            "simulation": {
                "bits_per_frame": 100000,
                "random_seed": 42
            }
        }
        
        if config_path:
            self.load_from_yaml(config_path)

    def load_from_yaml(self, config_path: str):
        """Loads configuration from YAML file and updates defaults."""
        try:
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data and "communication" in yaml_data:
                    self._update_dict(self.config, yaml_data["communication"])
        except Exception:
            # Fall back to default parameters if file is not found or malformed
            pass

    def _update_dict(self, target: dict, source: dict):
        """Recursively updates nested dictionaries."""
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._update_dict(target[k], v)
            else:
                target[k] = v
                
    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
