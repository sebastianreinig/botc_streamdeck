import asyncio
from botc_deck.pages.base import BasePage
from botc_deck.render import (
    COLOR_BT_OK, COLOR_BT_WAIT, COLOR_BT_OFF, COLOR_CANCEL
)

class BluetoothPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.device_slots = []  # Discovered devices mapped to keys 5..13
        self._sync_device_slots()

    def _sync_device_slots(self):
        self.device_slots = self.bluetooth.discovered_devices[:9]

    async def get_image(self, key_idx):
        r = self.renderer
        bt = self.bluetooth

        # ---------------- Row 0: Actions ----------------
        if key_idx == 0:
            # Back
            return r.render_button(label="Zurück", icon_name="back")

        elif key_idx == 1:
            # Scan
            if bt.is_scanning:
                return r.render_button(
                    label="Scannt…",
                    sublabel="Bitte warten",
                    icon_name="search",
                    is_active=True,
                    highlight_color=COLOR_BT_WAIT
                )
            return r.render_button(
                label="Suchen",
                sublabel="Audio-Scan",
                icon_name="search"
            )

        elif key_idx == 2:
            # Reconnect Last
            has_last = bool(bt.last_mac)
            sub = bt.last_name[:8] if (has_last and bt.last_name) else "Keins"
            return r.render_button(
                label="Letztes",
                sublabel=sub,
                icon_name="reconnect",
                is_active=has_last
            )

        elif key_idx == 3:
            # Disconnect
            is_connected = bool(bt.connected_device)
            return r.render_button(
                label="Trennen",
                icon_name="cancel",
                border_color=COLOR_CANCEL if is_connected else COLOR_BT_OFF
            )

        elif key_idx == 4:
            # Forget device
            return r.render_button(
                label="Vergessen",
                sublabel="Entkoppeln",
                icon_name="trash"
            )

        # ---------------- Row 1 & 2: Discovered Devices (Keys 5..13) ----------------
        slot_idx = key_idx - 5
        if 0 <= slot_idx < len(self.device_slots):
            dev = self.device_slots[slot_idx]
            name = dev.get("name", "Audio")
            mac = dev.get("mac", "")
            is_this_connected = (bt.connected_device and bt.connected_device.get("mac") == mac)

            # Name abbreviation to fit key nicely
            short_name = (name[:9] + "…") if len(name) > 10 else name
            is_audio = dev.get("is_audio", False)

            if is_this_connected:
                return r.render_button(
                    label=short_name,
                    sublabel="Verbunden",
                    icon_name="speaker",
                    is_active=True,
                    highlight_color=COLOR_BT_OK
                )
            else:
                return r.render_button(
                    label=short_name,
                    sublabel="Audio" if is_audio else "Koppeln",
                    icon_name="speaker",
                    border_color=COLOR_BT_OK if is_audio else COLOR_BT_WAIT,
                    highlight_color=COLOR_BT_OK if is_audio else None
                )

        if key_idx == 14:
            # Empty / status slot
            curr = bt.connected_device.get("name", "Keins") if bt.connected_device else "Getrennt"
            short_curr = (curr[:7] + "…") if len(curr) > 8 else curr
            return r.render_button(label="Status", sublabel=short_curr, icon_name="bluetooth")

        # Empty slot
        return r.render_button(label="")

    async def on_press(self, key_idx):
        bt = self.bluetooth

        if key_idx == 0:
            # Back to main
            from botc_deck.pages.main import MainPage
            await self.app.set_page(MainPage(self.app))

        elif key_idx == 1:
            # Start Scan
            await self.app.refresh_key(1)
            # Run scan asynchronously
            asyncio.create_task(self._do_scan())

        elif key_idx == 2:
            # Reconnect Last
            if bt.last_mac:
                asyncio.create_task(self._do_connect(bt.last_mac, bt.last_name))

        elif key_idx == 3:
            # Disconnect
            await bt.disconnect()
            await self.app.refresh_page()

        elif key_idx == 4:
            # Forget
            await bt.forget_last_device()
            await self.app.refresh_page()

        elif 5 <= key_idx <= 13:
            slot_idx = key_idx - 5
            if slot_idx < len(self.device_slots):
                dev = self.device_slots[slot_idx]
                mac = dev.get("mac")
                name = dev.get("name")
                asyncio.create_task(self._do_connect(mac, name))

    async def _do_scan(self):
        await self.bluetooth.start_scan(duration=10)
        self._sync_device_slots()
        await self.app.refresh_page()

    async def _do_connect(self, mac, name):
        await self.app.refresh_page()
        success = await self.bluetooth.connect_device(mac, name)
        await self.app.refresh_page()
