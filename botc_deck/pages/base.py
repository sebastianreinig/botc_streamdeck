class BasePage:
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self.audio = app.audio
        self.state = app.state
        self.renderer = app.renderer
        self.tts = app.tts
        self.timers = app.timers
        self.bluetooth = app.bluetooth

    async def get_image(self, key_idx):
        """Return PIL Image for key index (0..14). Subclasses override."""
        raise NotImplementedError

    async def on_press(self, key_idx):
        """Called when key is pressed down."""
        pass

    async def on_release(self, key_idx):
        """Called when key is released."""
        pass

    async def on_long_press(self, key_idx):
        """Called if key is held for >= threshold (default 1.5s)."""
        pass

    async def on_tick(self):
        """Periodic background refresh hook."""
        pass
