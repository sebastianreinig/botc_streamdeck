import json
import os
from pathlib import Path

class State:
    def __init__(self, state_file_path):
        self.path = Path(state_file_path)
        self.day_position = 0.0
        self.night_position = 0.0
        self.volume = 70
        self.brightness_idx = 0
        self.last_bt_device_mac = None
        self.last_bt_device_name = None
        self.active_mode = "day"  # Default is "day" (clean white text)
        self.load()


    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.day_position = float(data.get("day_position", 0.0))
                    self.night_position = float(data.get("night_position", 0.0))
                    self.volume = int(data.get("volume", 70))
                    self.brightness_idx = int(data.get("brightness_idx", 0))
                    self.last_bt_device_mac = data.get("last_bt_device_mac")
                    self.last_bt_device_name = data.get("last_bt_device_name")
                    # Game session always starts fresh in Day mode (white text)
                    self.active_mode = "day"
            except Exception as e:

                print(f"[State] Error loading state: {e}")

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "day_position": self.day_position,
                "night_position": self.night_position,
                "volume": self.volume,
                "brightness_idx": self.brightness_idx,
                "last_bt_device_mac": self.last_bt_device_mac,
                "last_bt_device_name": self.last_bt_device_name,
                "active_mode": self.active_mode,
            }
            tmp_path = self.path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)
        except Exception as e:
            print(f"[State] Error saving state: {e}")
