import asyncio
import time

try:
    from StreamDeck.DeviceManager import DeviceManager
    from StreamDeck.ImageHelpers import PILHelper
    HAS_STREAMDECK = True
except ImportError:
    HAS_STREAMDECK = False

LONG_PRESS_THRESHOLD = 1.3  # seconds

class StreamDeckController:
    def __init__(self, app):
        self.app = app
        self.deck = None
        self.key_press_times = {}
        self.long_press_fired = set()
        self._key_count = 15
        self.loop = None

    async def init_deck(self):
        self.loop = asyncio.get_running_loop()
        if not HAS_STREAMDECK:
            print("[Deck] python-elgato-streamdeck not available. Running headless/mock deck.")
            return False

        decks = DeviceManager().enumerate()
        if not decks:
            print("[Deck] No Elgato Stream Deck found. Running in mock/waiting mode.")
            return False

        self.deck = decks[0]
        self.deck.open()
        self.deck.reset()

        self._key_count = self.deck.key_count()
        print(f"[Deck] Connected to {self.deck.deck_type()} with {self._key_count} keys.")

        # Set initial brightness
        b = self.app.get_current_brightness()
        self.deck.set_brightness(b)

        # Register hardware callback
        self.deck.set_key_callback(self._on_key_change_raw)
        return True

    def _on_key_change_raw(self, deck, key_idx, state):
        """Called by StreamDeck SDK background thread."""
        if not self.loop:
            return
        asyncio.run_coroutine_threadsafe(self._handle_key_event(key_idx, state), self.loop)

    async def _handle_key_event(self, key_idx, is_pressed):
        page = self.app.current_page
        if not page:
            return

        now = time.monotonic()
        if is_pressed:
            self.key_press_times[key_idx] = now
            self.long_press_fired.discard(key_idx)
            # Immediate press action
            await page.on_press(key_idx)
            # Spawn long press watcher
            asyncio.create_task(self._watch_long_press(key_idx, now))
        else:
            press_time = self.key_press_times.pop(key_idx, None)
            was_long = key_idx in self.long_press_fired
            self.long_press_fired.discard(key_idx)
            if not was_long:
                await page.on_release(key_idx)

    async def _watch_long_press(self, key_idx, press_time):
        await asyncio.sleep(LONG_PRESS_THRESHOLD)
        if key_idx in self.key_press_times and self.key_press_times[key_idx] == press_time:
            self.long_press_fired.add(key_idx)
            page = self.app.current_page
            if page:
                await page.on_long_press(key_idx)

    async def update_key(self, key_idx, pil_image):
        if not self.deck:
            return
        try:
            native_img = PILHelper.to_native_key_format(self.deck, pil_image)
            self.deck.set_key_image(key_idx, native_img)
        except Exception as e:
            print(f"[Deck] Error updating key {key_idx}: {e}")

    def set_brightness(self, percent):
        if self.deck:
            try:
                self.deck.set_brightness(percent)
            except Exception as e:
                print(f"[Deck] Error setting brightness: {e}")

    def close(self):
        if self.deck:
            try:
                self.deck.reset()
                self.deck.close()
            except Exception:
                pass
            self.deck = None
