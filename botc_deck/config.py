import os
from pathlib import Path
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

DEFAULT_CONFIG = {
    "paths": {
        "music_dir": "music",
        "day_track": "music/day.mp3",
        "night_track": "music/night.mp3",
        "bell_sound": "music/bell.mp3",
        "state_file": "state.json",
        "tts_cache_dir": "cache_tts",
        "assets_dir": "assets/icons",
    },
    "audio": {
        "default_volume": 70,
        "volume_step": 5,
        "fade_duration": 1.5,
    },
    "timers": {
        "options": [10, 8, 5, 3],
    },
    "system": {
        "disable_wifi_on_start": False,
        "auto_reconnect_bluetooth": True,
        "tts_enabled": True,
        "brightness_steps": [100, 50, 15],
    },
}

class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            self.project_root = Path(__file__).resolve().parent.parent
            self.config_path = self.project_root / "config.yaml"
        else:
            self.config_path = Path(config_path)
            self.project_root = self.config_path.parent

        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if self.config_path.exists() and HAS_YAML:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = yaml.safe_load(f) or {}
                    self._deep_merge(self.data, user_cfg)
            except Exception as e:
                print(f"[Config] Error loading {self.config_path}: {e}")
        elif self.config_path.exists() and not HAS_YAML:
            print("[Config] PyYAML not installed in current environment; using default configuration.")

    def _deep_merge(self, base, override):
        for k, v in override.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def resolve_path(self, rel_or_abs):
        p = Path(rel_or_abs)
        if not p.is_absolute():
            return str(self.project_root / p)
        return str(p)

    def get(self, *keys, default=None):
        curr = self.data
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr
