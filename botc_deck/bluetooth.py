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
        self.connecting_mac = None
        self.connecting_name = None
        self.selected_controller_mac = None
        self.connected_device = None  # {"mac": ..., "name": ...}
        self.discovered_devices = []  # list of {"mac": ..., "name": ..., "rssi": ...}
        self._reconnect_task = None

        if self.state.last_bt_device_mac:
            self.last_mac = self.state.last_bt_device_mac
            self.last_name = self.state.last_bt_device_name or self.last_mac
        else:
            self.last_mac = None
            self.last_name = None

    async def _unblock_rfkill(self):
        """Unblock bluetooth via rfkill if the binary is present (handles /usr/sbin/rfkill)."""
        rfkill_bin = shutil.which("rfkill") or ("/usr/sbin/rfkill" if os.path.exists("/usr/sbin/rfkill") else None)
        if rfkill_bin:
            try:
                p = await asyncio.create_subprocess_exec(
                    rfkill_bin, "unblock", "bluetooth",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(p.wait(), timeout=1.5)
            except Exception:
                pass

    async def start(self):
        """Initial check and auto-reconnect."""
        if self.is_linux:
            await self._unblock_rfkill()
            # Prioritize USB Bluetooth dongle over onboard Pi radio
            await self._ensure_preferred_controller()
            # Check currently connected device
            await self._refresh_connection_status()
            # Pre-load known audio devices from BlueZ cache so they appear immediately in menu
            await self.load_cached_devices()
            if self.connected_device:
                await self._set_bluetooth_as_default_sink(self.connected_device["mac"])
            elif self.config.get("system", "auto_reconnect_bluetooth", default=True):
                if self.last_mac:
                    asyncio.create_task(self.connect_device(self.last_mac, self.last_name, silent=True))
        else:
            print("[Bluetooth] Non-Linux environment (macOS): Running in Mock Bluetooth mode.")

    async def load_cached_devices(self):
        """Pre-populate discovered_devices with known/paired audio devices from BlueZ cache."""
        if not self.is_linux:
            return self.discovered_devices

        try:
            p = await asyncio.create_subprocess_exec(
                "bluetoothctl", "devices",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await p.communicate()
            lines = stdout.decode("utf-8", errors="ignore").splitlines()

            dev_map = {}
            for l in lines:
                clean_l = self._clean_bt_str(l)
                m = re.match(r"^Device\s+([0-9A-Fa-f:]{17})\s*(.*)$", clean_l)
                if m:
                    mac, name = m.group(1), m.group(2).strip()
                    if self._is_valid_device_name(name, mac):
                        dev_map[mac] = name

            scored_devices = []
            for mac, name in dev_map.items():
                is_audio, real_name = await self._check_is_audio_device(mac)
                final_name = real_name or name
                if is_audio:
                    scored_devices.append({"mac": mac, "name": final_name, "is_audio": True})

            if scored_devices:
                self.discovered_devices = scored_devices
                print(f"[Bluetooth] Pre-loaded {len(self.discovered_devices)} known audio devices: {self.discovered_devices}")
        except Exception as e:
            print(f"[Bluetooth] Error loading cached devices: {e}")

        return self.discovered_devices

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

    async def _ensure_preferred_controller(self):
        """
        If multiple Bluetooth controllers exist (e.g. onboard Pi + USB dongle),
        detect them, prioritize the USB dongle, make it active via 'select',
        and power off the onboard Pi radio to avoid dual-radio interference.
        """
        if not self.is_linux or not shutil.which("bluetoothctl"):
            return None

        try:
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            out = self._clean_bt_str(stdout.decode("utf-8", errors="ignore"))

            controllers = []
            for line in out.splitlines():
                m = re.search(r"Controller\s+([0-9A-Fa-f:]{17})\s*(.*)", line)
                if m:
                    mac = m.group(1).upper()
                    info = m.group(2).strip()
                    controllers.append((mac, info))

            if not controllers:
                return None

            if len(controllers) == 1:
                self.selected_controller_mac = controllers[0][0]
                return self.selected_controller_mac

            # Multiple controllers detected!
            # Raspberry Pi onboard MAC addresses start with B8:27:EB, DC:A6:32, E4:5F:01, 28:CD:C1, D8:3A:DD
            pi_prefixes = ("B8:27:EB", "DC:A6:32", "E4:5F:01", "28:CD:C1", "D8:3A:DD")
            usb_controller = None
            internal_controller = None

            for mac, info in controllers:
                if any(mac.startswith(pfx) for pfx in pi_prefixes):
                    internal_controller = mac
                else:
                    usb_controller = mac

            chosen = usb_controller or controllers[0][0]
            self.selected_controller_mac = chosen
            print(f"[Bluetooth] Multiple controllers found! Prioritizing USB controller {chosen} over onboard {internal_controller}")

            # 1. Power off onboard controller so it does not conflict/interfere with the USB dongle
            if internal_controller and internal_controller != chosen:
                print(f"[Bluetooth] Powering down onboard controller {internal_controller}...")
                try:
                    await asyncio.create_subprocess_exec(
                        "bluetoothctl", "select", internal_controller,
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                    await asyncio.create_subprocess_exec(
                        "bluetoothctl", "power", "off",
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                except Exception:
                    pass

            # 2. Select and power on USB controller
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "select", chosen,
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

            return chosen
        except Exception as e:
            print(f"[Bluetooth] Controller prioritization error: {e}")
            return None

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
            # 0. Ensure Bluetooth adapter is unblocked and preferred USB controller is active
            await self._unblock_rfkill()
            await self._ensure_preferred_controller()
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "power", "on",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "default-agent",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            # Ensure any previous scan is stopped so discovery is not busy
            try:
                p_soff = await asyncio.create_subprocess_exec(
                    "bluetoothctl", "scan", "off",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(p_soff.wait(), timeout=1.5)
            except Exception:
                pass

            # Interactive scan session to capture newly broadcasted devices
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            if self.selected_controller_mac:
                proc.stdin.write(f"select {self.selected_controller_mac}\n".encode())
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
                    raw_line = line_bytes.decode("utf-8", errors="ignore")
                    line = self._clean_bt_str(raw_line)

                    # 1. Matches Name or Alias change: "[CHG] Device AA:BB:CC:DD:EE:FF Name: MySpeaker"
                    m_name = re.search(r"Device\s+([0-9A-Fa-f:]{17})\s+(?:Name|Alias):\s*(.+)$", line)
                    if m_name:
                        mac, name = m_name.group(1), m_name.group(2).strip()
                        if self._is_valid_device_name(name, mac):
                            dev_map[mac] = name
                            continue

                    # 2. Matches new broadcast: "[NEW] Device AA:BB:CC:DD:EE:FF MySpeaker"
                    m_new = re.search(r"Device\s+([0-9A-Fa-f:]{17})\s+(.+)$", line)
                    if m_new:
                        mac, name = m_new.group(1), m_new.group(2).strip()
                        if self._is_valid_device_name(name, mac):
                            dev_map[mac] = name
                        elif mac not in dev_map:
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

            # Also query all known and paired devices from BlueZ cache
            for cmd in (["bluetoothctl", "devices"], ["bluetoothctl", "devices", "Paired"]):
                try:
                    p2 = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout2, _ = await p2.communicate()
                    lines = stdout2.decode("utf-8", errors="ignore").splitlines()
                    for l in lines:
                        clean_l = self._clean_bt_str(l)
                        m = re.match(r"^Device\s+([0-9A-Fa-f:]{17})\s*(.*)$", clean_l)
                        if m:
                            mac, name = m.group(1), m.group(2).strip()
                            if self._is_valid_device_name(name, mac):
                                dev_map[mac] = name
                            elif mac not in dev_map:
                                dev_map[mac] = name or "Audio"
                except Exception:
                    pass

            # Prioritize devices by checking if they are audio sinks and resolve names
            scored_devices = []
            for mac, name in dev_map.items():
                is_audio, real_name = await self._check_is_audio_device(mac)
                final_name = real_name or name
                if not self._is_valid_device_name(final_name, mac):
                    final_name = "Audio Gerät" if is_audio else final_name
                scored_devices.append({"mac": mac, "name": final_name, "is_audio": is_audio})

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
            if not silent and self.tts:
                await self.tts.speak("Verbindung läuft bereits.")
            return False

        self.is_connecting = True
        self.connecting_mac = mac
        display_name = name or mac
        self.connecting_name = display_name
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
            self.connecting_mac = None
            self.connecting_name = None
            if self.tts and not silent:
                await self.tts.speak(f"Bluetooth verbunden mit {display_name}.")
            return True

        # Linux bluetoothctl pairing / trust / connect
        success = False
        try:
            await self._ensure_preferred_controller()
            if self.selected_controller_mac:
                await asyncio.create_subprocess_exec(
                    "bluetoothctl", "select", self.selected_controller_mac,
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )

            # 1. Trust
            await asyncio.create_subprocess_exec(
                "bluetoothctl", "trust", mac,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            # 2. Pair with automated PIN 0000 / confirmation support
            await self._pair_with_pin_support(mac)

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
            self.connecting_mac = None
            self.connecting_name = None

        return success

    async def disconnect(self):
        """Disconnect active device."""
        self.connecting_mac = None
        self.connecting_name = None
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

    async def _pair_with_pin_support(self, mac, timeout=12.0):
        """
        Pairs with device using an interactive session that automatically provides
        PIN '0000' or passes authorization if requested by legacy Bluetooth adapters.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Register agent and issue pair command on preferred controller
            commands = ""
            if self.selected_controller_mac:
                commands += f"select {self.selected_controller_mac}\n"
            commands += f"agent on\ndefault-agent\npair {mac}\n"
            proc.stdin.write(commands.encode("utf-8"))
            await proc.stdin.drain()

            loop = asyncio.get_running_loop()
            start_t = loop.time()

            while loop.time() - start_t < timeout:
                try:
                    line_bytes = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="ignore")
                    line_lower = line.lower()

                    if "enter pin code" in line_lower or "pin code:" in line_lower:
                        print(f"[Bluetooth] Device {mac} requested PIN. Sending '0000'...")
                        proc.stdin.write(b"0000\n")
                        await proc.stdin.drain()

                    elif "confirm passkey" in line_lower or "authorize" in line_lower or "(yes/no)" in line_lower:
                        print(f"[Bluetooth] Device {mac} requested confirmation. Sending 'yes'...")
                        proc.stdin.write(b"yes\n")
                        await proc.stdin.drain()

                    elif "pairing successful" in line_lower or "already paired" in line_lower:
                        print(f"[Bluetooth] Pairing successful for {mac}.")
                        break

                    elif "failed to pair" in line_lower:
                        print(f"[Bluetooth] Pairing note: {line.strip()}")
                        break
                except asyncio.TimeoutError:
                    pass

            try:
                proc.stdin.write(b"quit\n")
                await proc.stdin.drain()
                proc.stdin.close()
                await proc.wait()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        except Exception as e:
            print(f"[Bluetooth] Pair with PIN error: {e}")

    async def reset_bluetooth(self):
        """
        Hard reset of the Bluetooth subsystem:
        1. Cancels active scans and reconnection tasks.
        2. Disconnects active connections.
        3. Power cycles the Bluetooth chip (power off -> sleep -> power on).
        4. Re-registers default BlueZ agent.
        5. Restarts WirePlumber user audio daemon.
        """
        print("[Bluetooth] Starting Bluetooth subsystem reset...")
        self.is_scanning = False
        self.is_connecting = False
        self.connecting_mac = None
        self.connecting_name = None
        self.discovered_devices = []

        if not self.is_linux:
            self.connected_device = None
            if self.tts:
                await self.tts.speak("Bluetooth zurückgesetzt.")
            return

        try:
            # 1. Disconnect any active connection
            if self.connected_device or self.last_mac:
                target = self.connected_device["mac"] if self.connected_device else self.last_mac
                try:
                    p = await asyncio.create_subprocess_exec(
                        "bluetoothctl", "disconnect", target,
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                    await asyncio.wait_for(p.wait(), timeout=2.0)
                except Exception:
                    pass
            self.connected_device = None

            # 2. Power off Bluetooth controller
            try:
                p_off = await asyncio.create_subprocess_exec(
                    "bluetoothctl", "power", "off",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(p_off.wait(), timeout=3.0)
            except Exception:
                pass

            await asyncio.sleep(1.0)

            # 3. Unblock rfkill and power on
            try:
                await self._unblock_rfkill()
                p_on = await asyncio.create_subprocess_exec(
                    "bluetoothctl", "power", "on",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(p_on.wait(), timeout=3.0)
                await self._ensure_preferred_controller()
                await asyncio.create_subprocess_exec(
                    "bluetoothctl", "default-agent",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
            except Exception:
                pass

            # 4. Restart WirePlumber audio daemon if running
            try:
                p_wp = await asyncio.create_subprocess_exec(
                    "systemctl", "--user", "restart", "wireplumber",
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                )
                await asyncio.wait_for(p_wp.wait(), timeout=3.0)
            except Exception:
                pass

            print("[Bluetooth] Bluetooth reset completed successfully.")
            if self.tts:
                await self.tts.speak("Bluetooth zurückgesetzt.")
        except Exception as e:
            print(f"[Bluetooth] Error during Bluetooth reset: {e}")
            if self.tts:
                await self.tts.speak("Bluetooth Reset fehlgeschlagen.")

    def _clean_bt_str(self, text):
        """Strip ANSI escape sequences and whitespace."""
        if not text:
            return ""
        return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text).strip()

    def _is_valid_device_name(self, name, mac):
        if not name:
            return False
        clean = self._clean_bt_str(name)
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
        """Check whether the device supports Bluetooth audio (A2DP / Sink / Headset) and extract name."""
        if not self.is_linux:
            return True, None
        try:
            proc = await asyncio.create_subprocess_exec(
                "bluetoothctl", "info", mac,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            out = self._clean_bt_str(stdout.decode("utf-8", errors="ignore"))
            out_lower = out.lower()

            resolved_name = None
            m_name = re.search(r"^\s*(?:Name|Alias):\s*(.+)$", out, re.M)
            if m_name:
                cand = m_name.group(1).strip()
                if self._is_valid_device_name(cand, mac):
                    resolved_name = cand

            # Audio indicators in BlueZ info
            audio_markers = [
                "audio", "sound", "headset", "speaker", "soundlink", "charge", "flip",
                "0000110b", "0000110d", "0000110a", "0000111e"
            ]
            for marker in audio_markers:
                if marker in out_lower:
                    return True, resolved_name
            if "icon: audio" in out_lower:
                return True, resolved_name
            return False, resolved_name
        except Exception:
            pass
        return False, None

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
