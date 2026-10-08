import asyncio
import os
import platform
import re
import shutil
import subprocess

class BluetoothManager:
    """
    Manages Bluetooth scanning, pairing, trusting, and connecting.
    Designed for screenless Raspberry Pi 3 usage.
    Falls back to mock mode on macOS or when BlueZ is unavailable.
    """
    def __init__(self, config, state, tts_engine=None):
        self.config = config
        self.state = state
        self.tts = tts_engine

        self.is_linux = platform.system() == "Linux"
        self.is_scanning = False
        self.is_connecting = False
        self.connected_device = None  # {"mac": ..., "name": ...}
        self.discovered_devices = []  # list of {"mac": ..., "name": ..., "rssi": ...}
        self._reconnect_task = None

        if self.state.last_bt_device_mac:
            self.last_mac = self.state.last_bt_device_mac
            self.last_name = self.state.last_bt_device_name or self.last_mac
        else:
            self.last_mac = None
            self.last_name = None

    async def start(self):
        """Initial check and auto-reconnect."""
        if self.is_linux:
            try:
                await asyncio.create_subprocess_exec(
                    "rfkill", "unblock", "bluetooth",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.create_subprocess_exec(
                    "bluetoothctl", "power", "on",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
            except Exception:
                pass
            # Check currently connected device
            await self._refresh_connection_status()
            if self.connected_device:
                await self._set_bluetooth_as_default_sink(self.connected_device["mac"])
            elif self.config.get("system", "auto_reconnect_bluetooth", default=True):
                if self.last_mac:
                    asyncio.create_task(self.connect_device(self.last_mac, self.last_name, silent=True))
        else:
            print("[Bluetooth] Non-Linux environment (macOS): Running in Mock Bluetooth mode.")

    async def _refresh_connection_status(self):
        if not self.is_linux or not shutil.which("bluetoothctl"):
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode("utf-8", errors="ignore")
            # If a device is connected: "Device AA:BB:CC:DD:EE:FF ... Connected: yes"
            if "Connected: yes" in out:
                mac_match = re.search(r"Device\s+([0-9A-Fa-f:]{17})", out)
                name_match = re.search(r"Name:\s+(.*)", out)
                mac = mac_match.group(1) if mac_match else None
                name = name_match.group(1).strip() if name_match else mac
                if mac:
                    self.connected_device = {"mac": mac, "name": name}
                    self.last_mac = mac
                    self.last_name = name
                    self.state.last_bt_device_mac = mac
                    self.state.last_bt_device_name = name
                    self.state.save()
                    return
            self.connected_device = None
        except Exception as e:
            print(f"[Bluetooth] Refresh status error: {e}")

    async def start_scan(self, duration=12):
        """Scan for nearby Bluetooth audio devices."""
        if self.is_scanning:
            return
        self.is_scanning = True
        self.discovered_devices = []

        if self.tts:
            await self.tts.speak("Suche nach Bluetooth Geräten.")

        print("[Bluetooth] Starting discovery scan...")
        if not self.is_linux:
            # Mock scan for testing on Mac
            await asyncio.sleep(2)
            self.discovered_devices = [
                {"mac": "11:22:33:44:55:66", "name": "JBL Charge 5", "rssi": -45},
                {"mac": "AA:BB:CC:DD:EE:FF", "name": "Sony WH-1000", "rssi": -55},
                {"mac": "12:34:56:78:9A:BC", "name": "Bose SoundLink", "rssi": -65},
            ]
            self.is_scanning = False
            return self.discovered_devices

        # Linux / BlueZ scan
        try:
            # 0. Ensure Bluetooth adapter is unblocked and powered on
            await asyncio.create_subprocess_exec(
                "rfkill", "unblock", "bluetooth",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "power", "on",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "default-agent",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )

            # Interactive scan session to capture newly broadcasted devices
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            proc.stdin.write(b"scan on\n")
            await proc.stdin.drain()

            dev_map = {}
            loop = asyncio.get_running_loop()
            start_t = loop.time()

            while loop.time() - start_t < duration:
                try:
                    line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="ignore").strip()

                    # 1. Matches Name or Alias change: "[CHG] Device AA:BB:CC:DD:EE:FF Name: MySpeaker"
                    m_name = re.search(r"Device\s+([0-9A-Fa-f:]{17})\s+(?:Name|Alias):\s*(.+)$", line)
                    if m_name:
                        mac, name = m_name.group(1), m_name.group(2).strip()
                        if self._is_valid_device_name(name, mac):
                            dev_map[mac] = name
                            continue

                    # 2. Matches new broadcast: "[NEW] Device AA:BB:CC:DD:EE:FF MySpeaker"
                    m_new = re.search(r"\[NEW\]\s+Device\s+([0-9A-Fa-f:]{17})\s+(.+)$", line)
                    if m_new:
                        mac, name = m_new.group(1), m_new.group(2).strip()
                        if self._is_valid_device_name(name, mac):
                            dev_map[mac] = name
                except asyncio.TimeoutError:
                    pass

            try:
                proc.stdin.write(b"scan off\nquit\n")
                await proc.stdin.drain()
                proc.stdin.close()
                await proc.wait()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

            # Also query all known devices from BlueZ cache
            p2 = await asyncio.create_subprocess_exec(
                "bluetoothctl", "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout2, _ = await p2.communicate()
            lines = stdout2.decode("utf-8", errors="ignore").splitlines()

            for line in lines:
                m = re.match(r"^Device\s+([0-9A-Fa-f:]{17})\s+(.*)$", line.strip())
                if m:
                    mac, name = m.group(1), m.group(2).strip()
                    if self._is_valid_device_name(name, mac):
                        dev_map[mac] = name

            # Prioritize devices by checking if they are audio sinks
            scored_devices = []
            for mac, name in dev_map.items():
                is_audio = await self._check_is_audio_device(mac)
                scored_devices.append({"mac": mac, "name": name, "is_audio": is_audio})

            # Sort: audio devices first!
            scored_devices.sort(key=lambda d: 0 if d["is_audio"] else 1)

            self.discovered_devices = scored_devices
            print(f"[Bluetooth] Scan complete. Found {len(self.discovered_devices)} valid devices: {self.discovered_devices}")

            if not self.discovered_devices and self.tts:
                await self.tts.speak("Keine Geräte gefunden.")
        except Exception as e:
            print(f"[Bluetooth] Scan failed: {e}")
        finally:
            self.is_scanning = False

        return self.discovered_devices

    async def connect_device(self, mac, name=None, silent=False):
        """Pair, trust, and connect to a device by MAC address."""
        if self.is_connecting:
            return False

        self.is_connecting = True
        display_name = name or mac
        print(f"[Bluetooth] Connecting to {display_name} ({mac})...")

        if not self.is_linux:
            # Mock mode on Mac
            await asyncio.sleep(1.5)
            self.connected_device = {"mac": mac, "name": display_name}
            self.last_mac = mac
            self.last_name = display_name
            self.state.last_bt_device_mac = mac
            self.state.last_bt_device_name = display_name
            self.state.save()
            self.is_connecting = False
            if self.tts and not silent:
                await self.tts.speak(f"Bluetooth verbunden mit {display_name}.")
            return True

        # Linux bluetoothctl pairing / trust / connect
        success = False
        try:
            # 1. Trust
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "trust", mac,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            # 2. Pair (if not already paired)
            p_pair = await asyncio.create_subprocess_exec(
                "bluetoothctl", "pair", mac,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await p_pair.communicate()

            # 3. Connect
            p_conn = await asyncio.create_subprocess_exec(
                "bluetoothctl", "connect", mac,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await p_conn.communicate()
            out = stdout.decode("utf-8", errors="ignore")

            if "Connection successful" in out or "already connected" in out:
                success = True
            else:
                # Double check with info
                await asyncio.sleep(1.0)
                await self._refresh_connection_status()
                if self.connected_device and self.connected_device["mac"] == mac:
                    success = True

            if success:
                self.connected_device = {"mac": mac, "name": display_name}
                self.last_mac = mac
                self.last_name = display_name
                self.state.last_bt_device_mac = mac
                self.state.last_bt_device_name = display_name
                self.state.save()
                print(f"[Bluetooth] Connected successfully to {display_name}!")

                # Switch default audio sink to Bluetooth speaker in PipeWire
                await self._set_bluetooth_as_default_sink(mac)

                if self.tts and not silent:
                    await self.tts.speak(f"Bluetooth verbunden mit {display_name}.")
            else:
                print(f"[Bluetooth] Failed to connect to {display_name}.")
                if self.tts and not silent:
                    await self.tts.speak("Verbindung fehlgeschlagen.")

        except Exception as e:
            print(f"[Bluetooth] Connection exception: {e}")
        finally:
            self.is_connecting = False

        return success

    async def disconnect(self):
        """Disconnect active device."""
        if not self.connected_device and not self.last_mac:
            return

        target = self.connected_device["mac"] if self.connected_device else self.last_mac
        print(f"[Bluetooth] Disconnecting {target}...")

        if not self.is_linux:
            self.connected_device = None
            if self.tts:
                await self.tts.speak("Bluetooth getrennt.")
            return

        try:
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "disconnect", target,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            self.connected_device = None
            if self.tts:
                await self.tts.speak("Bluetooth getrennt.")
        except Exception as e:
            print(f"[Bluetooth] Disconnect error: {e}")

    async def forget_last_device(self):
        """Remove pairing/trust of the last device."""
        if self.last_mac:
            if self.is_linux:
                try:
                    await asyncio.create_subprocess_exec(
                        "bluetoothctl", "remove", self.last_mac,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                except Exception:
                    pass
            self.connected_device = None
            self.last_mac = None
            self.last_name = None
            self.state.last_bt_device_mac = None
            self.state.last_bt_device_name = None
            self.state.save()
            if self.tts:
                await self.tts.speak("Gerät vergessen.")

    def _is_valid_device_name(self, name, mac):
        if not name:
            return False
        clean = name.strip()
        clean_lower = clean.lower()

        ignored_prefixes = (
            "manufacturerdata", "txpower", "rssi", "servicedata", "uuids",
            "modalias", "class", "icon", "connected", "paired", "trusted",
            "blocked", "legacy", "services", "appearance"
        )
        for ign in ignored_prefixes:
            if clean_lower.startswith(ign):
                return False

        # Reject if identical to MAC or pure MAC format
        if clean.replace(":", "-").lower() == mac.replace(":", "-").lower():
            return False
        if re.match(r"^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$", clean):
            return False
        return True

    async def _check_is_audio_device(self, mac):
        """Check whether the device supports Bluetooth audio (A2DP / Sink / Headset)."""
        if not self.is_linux:
            return True
        try:
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl", "info", mac,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            out = stdout.decode("utf-8", errors="ignore").lower()
            # Audio indicators in BlueZ info
            audio_markers = [
                "audio", "sound", "headset", "speaker", "soundlink", "charge", "flip",
                "0000110b", "0000110d", "0000110a", "0000111e"
            ]
            for marker in audio_markers:
                if marker in out:
                    return True
            if "icon: audio" in out:
                return True
        except Exception:
            pass
        return False

    async def _set_bluetooth_as_default_sink(self, mac):
        """Find the PipeWire/Pulse sink corresponding to the BT device and set it as default."""
        if not self.is_linux:
            return
        mac_clean = mac.replace(":", "_").lower()
        # Retry for up to 3 seconds as WirePlumber initializes the A2DP profile
        for _ in range(6):
            await asyncio.sleep(0.5)
            try:
                proc = await asyncio.create_subprocess_exec(
                    "pactl", "list", "sinks", "short",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL
                )
                stdout, _ = await proc.communicate()
                lines = stdout.decode("utf-8", errors="ignore").splitlines()
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        sink_name = parts[1]
                        if "bluez" in sink_name.lower() or mac_clean in sink_name.lower():
                            print(f"[Bluetooth] Found Bluetooth audio sink: {sink_name}. Setting as default output.")
                            await asyncio.create_subprocess_exec(
                                "pactl", "set-default-sink", sink_name,
                                stdout=asyncio.subprocess.DEVNULL,
                                stderr=asyncio.subprocess.DEVNULL
                            )
                            await asyncio.create_subprocess_exec(
                                "pactl", "set-sink-mute", sink_name, "0",
                                stdout=asyncio.subprocess.DEVNULL,
                                stderr=asyncio.subprocess.DEVNULL
                            )
                            return
            except Exception as e:
                print(f"[Bluetooth] Error setting default sink: {e}")
