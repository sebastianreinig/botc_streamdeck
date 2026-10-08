import asyncio
import os
import signal
import sys
import subprocess

from botc_deck.config import Config
from botc_deck.state import State
from botc_deck.audio import AudioEngine
from botc_deck.tts import TTSEngine
from botc_deck.timers import TimerManager
from botc_deck.bluetooth import BluetoothManager
from botc_deck.render import ButtonRenderer
from botc_deck.deck import StreamDeckController
from botc_deck.pages.main import MainPage

class BotCApp:
    def __init__(self, config_path=None):
        self.config = Config(config_path)
        state_file = self.config.resolve_path(self.config.get("paths", "state_file", default="state.json"))
        self.state = State(state_file)

        self.audio = AudioEngine(self.config, self.state)
        self.tts = TTSEngine(self.config, self.audio)
        self.timers = TimerManager(self.audio, on_tick=self._on_timer_tick)
        self.bluetooth = BluetoothManager(self.config, self.state, tts_engine=self.tts)
        self.renderer = ButtonRenderer(self.config.resolve_path(self.config.get("paths", "assets_dir", default="assets/icons")))
        self.deck_ctrl = StreamDeckController(self)

        self.brightness_steps = self.config.get("system", "brightness_steps", default=[100, 50, 15])
        self.current_page = None
        self._running = True

    def get_current_brightness(self):
        idx = self.state.brightness_idx % len(self.brightness_steps)
        return self.brightness_steps[idx]

    def cycle_brightness(self):
        self.state.brightness_idx = (self.state.brightness_idx + 1) % len(self.brightness_steps)
        self.state.save()
        val = self.get_current_brightness()
        self.deck_ctrl.set_brightness(val)
        print(f"[App] Brightness set to {val}%")

    async def _on_timer_tick(self, remaining, total, mins):
        # Refresh timer buttons on main page if currently displayed
        if isinstance(self.current_page, MainPage):
            # Keys 5, 6, 7, 8 are timer buttons
            for k in (5, 6, 7, 8):
                await self.refresh_key(k)

    async def set_page(self, page):
        self.current_page = page
        await self.refresh_page()

    async def refresh_page(self):
        if not self.current_page:
            return
        for k in range(15):
            await self.refresh_key(k)

    async def refresh_key(self, key_idx):
        if not self.current_page:
            return
        try:
            img = await self.current_page.get_image(key_idx)
            await self.deck_ctrl.update_key(key_idx, img)
        except Exception as e:
            print(f"[App] Error rendering key {key_idx}: {e}")

    async def start(self):
        print("=" * 60)
        print("  Blood on the Clocktower - Stream Deck Controller")
        print("=" * 60)

        # Optional: Disable WiFi on Pi for interference-free Bluetooth audio
        if self.config.get("system", "disable_wifi_on_start", default=False):
            self._disable_wifi()

        # Connect Deck hardware
        has_deck = await self.deck_ctrl.init_deck()
        if not has_deck:
            print("[App] Running without hardware deck (mock/virtual mode).")

        # Start Bluetooth auto-reconnect
        await self.bluetooth.start()

        # Load initial MainPage
        await self.set_page(MainPage(self))

        # Background maintenance loop
        while self._running:
            await asyncio.sleep(5.0)
            self.state.save()

    def _disable_wifi(self):
        print("[System] Disabling WiFi to prioritize Bluetooth bandwidth...")
        try:
            subprocess.run(["rfkill", "block", "wifi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            try:
                subprocess.run(["nmcli", "radio", "wifi", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    async def shutdown(self):
        print("\n[App] Shutting down BotC Stream Deck...")
        self._running = False
        await self.timers.cancel_timer(trigger_bell=False)
        await self.audio.stop()
        self.state.save()
        self.deck_ctrl.close()

async def main():
    app = BotCApp()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(app.shutdown()))
        except (NotImplementedError, RuntimeError):
            pass

    try:
        await app.start()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
