import asyncio
import os
import socket
import subprocess
import sys
import time
from botc_deck.pages.base import BasePage
from botc_deck.render import (
    COLOR_CANCEL, COLOR_BT_OK, COLOR_BT_WAIT, COLOR_BT_OFF
)

class SystemPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.shutdown_confirm_until = 0

    async def get_image(self, key_idx):
        self.renderer.is_night = (self.state.active_mode == "night")
        r = self.renderer
        now = time.monotonic()

        # ---------------- Row 0: Back & Hardware Settings ----------------
        if key_idx == 0:
            return r.render_button(label="Zurück", icon_name="back")

        elif key_idx == 1:
            # Bluetooth status & access
            bt = self.bluetooth
            if bt.connected_device:
                name = bt.connected_device.get("name", "Verbunden")
                short_name = (name[:9] + "…") if len(name) > 10 else name
                return r.render_button(
                    label="BT Aktiv",
                    sublabel=short_name,
                    icon_name="bluetooth",
                    is_active=True,
                    highlight_color=COLOR_BT_OK
                )
            elif bt.is_connecting or bt.is_scanning:
                return r.render_button(
                    label="BT Sucht",
                    sublabel="Warten…",
                    icon_name="bluetooth",
                    is_active=True,
                    highlight_color=COLOR_BT_WAIT
                )
            else:
                return r.render_button(
                    label="Bluetooth",
                    sublabel="Koppeln",
                    icon_name="bluetooth",
                    border_color=COLOR_BT_OFF
                )

        elif key_idx == 2:
            # Brightness cycle
            curr_b = self.app.get_current_brightness()
            return r.render_button(
                label="Licht",
                sublabel=f"{curr_b}%",
                icon_name="brightness"
            )

        elif key_idx == 3:
            # WiFi toggle
            wifi_on = self._is_wifi_enabled()
            return r.render_button(
                label="WLAN",
                sublabel="Aktiv" if wifi_on else "Aus",
                icon_name="wifi",
                is_active=wifi_on,
                highlight_color=COLOR_BT_OK if wifi_on else None,
                border_color=COLOR_BT_OK if wifi_on else COLOR_CANCEL
            )

        elif key_idx == 4:
            # TTS voice toggle
            tts_on = self.tts.enabled
            return r.render_button(
                label="Sprache",
                sublabel="Aktiv" if tts_on else "Stumm",
                icon_name="speaker",
                is_active=tts_on,
                highlight_color=COLOR_BT_OK if tts_on else None
            )

        # ---------------- Row 1: Maintenance & System Tools ----------------
        elif key_idx == 5:
            # Music 0:00 Reset
            return r.render_button(
                label="Musik",
                sublabel="Reset 0:00",
                icon_name="reconnect",
                border_color=COLOR_CANCEL
            )

        elif key_idx == 6:
            # Audio Engine Reinit
            return r.render_button(
                label="Audio",
                sublabel="Neustart",
                icon_name="speaker",
                border_color=COLOR_BT_OK
            )

        elif key_idx == 7:
            # Speak IP
            return r.render_button(
                label="IP Adresse",
                sublabel="Ansage",
                icon_name="status"
            )

        elif key_idx == 8:
            # Restart Application
            return r.render_button(
                label="App Neu",
                sublabel="Neustart",
                icon_name="reconnect"
            )

        elif key_idx == 9:
            # Shutdown Pi (2-click safety)
            is_confirm = now < self.shutdown_confirm_until
            lbl = "SICHER?" if is_confirm else "Power Off"
            sub = "Nochmal!" if is_confirm else "2x drücken"
            return r.render_button(
                label=lbl,
                sublabel=sub,
                icon_name="power",
                border_color=COLOR_CANCEL,
                is_active=is_confirm,
                highlight_color=COLOR_CANCEL
            )

        return r.render_button(label="")

    async def on_press(self, key_idx):
        now = time.monotonic()

        if key_idx == 0:
            # Back to MainPage
            from botc_deck.pages.main import MainPage
            await self.app.set_page(MainPage(self.app))

        elif key_idx == 1:
            # Open Bluetooth page
            from botc_deck.pages.bluetooth import BluetoothPage
            await self.app.set_page(BluetoothPage(self.app))

        elif key_idx == 2:
            # Cycle brightness
            self.app.cycle_brightness()
            await self.app.refresh_key(2)

        elif key_idx == 3:
            # Toggle WiFi
            await self._toggle_wifi()
            await self.app.refresh_key(3)
            await self.app.refresh_key(7)  # IP address may change

        elif key_idx == 4:
            # Toggle TTS
            self.tts.enabled = not self.tts.enabled
            await self.app.refresh_key(4)

        elif key_idx == 5:
            # Reset both day and night positions to 0:00
            print("[System] Resetting Day & Night positions to 0:00...")
            await self.audio.reset_positions()
            if self.tts:
                await self.tts.speak("Musik auf Anfang gesetzt.")
            await self.app.refresh_key(5)

        elif key_idx == 6:
            # Reinit audio engine & re-bind Bluetooth default sink
            print("[System] Reinitializing audio subsystem...")
            self.audio.reinit_audio()
            if self.bluetooth.connected_device:
                await self.bluetooth._set_bluetooth_as_default_sink(self.bluetooth.connected_device["mac"])
            if self.tts:
                await self.tts.speak("Audio neu initialisiert.")
            await self.app.refresh_key(6)

        elif key_idx == 7:
            # Speak IP
            ip = self._get_ip()
            print(f"[System] IP Address: {ip}")
            if self.tts:
                ip_spoken = ip.replace(".", " Punkt ")
                await self.tts.speak(f"IP Adresse lautet {ip_spoken}")

        elif key_idx == 8:
            # Restart App
            print("[System] Restarting application...")
            if self.tts:
                await self.tts.speak("App wird neu gestartet.")
            await self.audio.stop()
            self.state.save()
            os._exit(0)

        elif key_idx == 9:
            # Shutdown Pi (2-click confirmation)
            if now < self.shutdown_confirm_until:
                print("[System] Shutting down Raspberry Pi...")
                if self.tts:
                    await self.tts.speak("System wird heruntergefahren.")
                await self.audio.stop()
                self.state.save()

                # Turn off Stream Deck screen immediately so it's pitch black
                self.app.deck_ctrl.set_brightness(0)
                self.app.deck_ctrl.close()

                # Execute shutdown commands
                for cmd in [
                    ["sudo", "shutdown", "-h", "now"],
                    ["sudo", "poweroff"],
                    ["systemctl", "poweroff"]
                ]:
                    try:
                        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                        if res.returncode == 0:
                            print(f"[System] Shutdown triggered: {' '.join(cmd)}")
                            break
                        else:
                            print(f"[System] Failed {' '.join(cmd)}: {res.stderr.strip()}")
                    except Exception as e:
                        print(f"[System] Error running {' '.join(cmd)}: {e}")

                os._exit(0)
            else:
                self.shutdown_confirm_until = now + 3.5
                await self.app.refresh_key(9)




    def _is_wifi_enabled(self):
        try:
            res = subprocess.run(["rfkill", "list", "wifi"], capture_output=True, text=True)
            if "Soft blocked: yes" in res.stdout or "Hard blocked: yes" in res.stdout:
                return False
            if "Wireless LAN" in res.stdout:
                return True
        except Exception:
            pass
        try:
            res = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True)
            if "disabled" in res.stdout.lower():
                return False
            if "enabled" in res.stdout.lower():
                return True
        except Exception:
            pass
        return True

    async def _toggle_wifi(self):
        currently_on = self._is_wifi_enabled()
        print(f"[System] Toggling WiFi from currently_on={currently_on}")
        try:
            if currently_on:
                subprocess.run(["sudo", "rfkill", "block", "wifi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["sudo", "nmcli", "radio", "wifi", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if self.tts:
                    await self.tts.speak("WLAN deaktiviert.")
            else:
                subprocess.run(["sudo", "rfkill", "unblock", "wifi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if self.tts:
                    await self.tts.speak("WLAN aktiviert.")
        except Exception as e:
            print(f"[System] WiFi toggle error: {e}")

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Nicht im Netzwerk"
