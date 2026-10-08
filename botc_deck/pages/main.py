import asyncio
import time
from botc_deck.pages.base import BasePage
from botc_deck.render import (
    COLOR_NIGHT, COLOR_DAY, COLOR_BELL, COLOR_CANCEL,
    COLOR_BT_OK, COLOR_BT_WAIT, COLOR_BT_OFF, COLOR_TEXT_PRIMARY
)

class MainPage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.vol_display_until = 0
        self.vol_display_val = None
        self.system_prompt_until = 0

    async def get_image(self, key_idx):
        r = self.renderer
        now = time.monotonic()

        # ---------------- Row 0: Music & Master Controls ----------------
        if key_idx == 0:
            # Night
            is_active = self.audio.current_track == "night" and self.audio.is_playing and not self.audio.is_paused
            return r.render_button(
                label="Nacht",
                icon_name="moon",
                is_active=is_active,
                highlight_color=COLOR_NIGHT
            )

        elif key_idx == 1:
            # Day
            is_active = self.audio.current_track == "day" and self.audio.is_playing and not self.audio.is_paused
            return r.render_button(
                label="Tag",
                icon_name="sun",
                is_active=is_active,
                highlight_color=COLOR_DAY
            )

        elif key_idx == 2:
            # Play / Pause
            is_paused = self.audio.is_paused or not self.audio.is_playing
            lbl = "Weiter" if is_paused else "Pause"
            return r.render_button(
                label=lbl,
                icon_name="play_pause",
                is_active=not is_paused
            )

        elif key_idx == 3:
            # Volume Down
            sub = f"{self.audio.state.volume}%" if now < self.vol_display_until else "-5%"
            return r.render_button(
                label="Leiser",
                sublabel=sub,
                icon_name="vol_down"
            )

        elif key_idx == 4:
            # Volume Up
            sub = f"{self.audio.state.volume}%" if now < self.vol_display_until else "+5%"
            return r.render_button(
                label="Lauter",
                sublabel=sub,
                icon_name="vol_up"
            )

        # ---------------- Row 1: Timers & Cancel ----------------
        timer_indices = {5: 10, 6: 8, 7: 5, 8: 3}
        if key_idx in timer_indices:
            mins = timer_indices[key_idx]
            is_this_timer = (self.timers.is_running and self.timers.active_minutes == mins)
            rem_str = self.timers.get_remaining_str() if is_this_timer else ""
            rem_sec = self.timers.remaining_seconds if is_this_timer else 999

            is_warning = (rem_sec <= 30)
            is_alert = (rem_sec <= 10)
            return r.render_timer_button(
                label=f"{mins} Min",
                remaining_str=rem_str,
                is_active=is_this_timer,
                is_warning=is_warning,
                is_alert=is_alert
            )

        elif key_idx == 9:
            # Timer Stop / Abbrechen
            return r.render_button(
                label="Stop",
                sublabel="Glocke",
                icon_name="cancel",
                border_color=COLOR_CANCEL
            )

        # ---------------- Row 2: Bell, -30s, +30s, Status, System ----------------
        elif key_idx == 10:
            # Bell
            return r.render_button(
                label="Glocke",
                icon_name="bell",
                border_color=COLOR_BELL,
                highlight_color=COLOR_BELL
            )

        elif key_idx == 11:
            # Timer Quick Adjust: -30s
            is_timer_running = self.timers.is_running
            return r.render_button(
                label="-30s",
                sublabel="Timer" if is_timer_running else "",
                icon_name="timer",
                border_color=COLOR_CANCEL if is_timer_running else None
            )

        elif key_idx == 12:
            # Timer Quick Adjust: +30s (Long press: +1 Min)
            is_timer_running = self.timers.is_running
            return r.render_button(
                label="+30s",
                sublabel="+1m Lang" if is_timer_running else "Start",
                icon_name="timer",
                border_color=COLOR_BT_OK if is_timer_running else None
            )

        elif key_idx == 13:
            # Status / Info
            return r.render_button(
                label="Status",
                sublabel="Ansage",
                icon_name="status"
            )

        elif key_idx == 14:
            # System Page
            return r.render_button(
                label="System",
                sublabel="Menü",
                icon_name="power"
            )

        return r.render_button(label="")

    async def on_press(self, key_idx):
        if key_idx == 0:
            # Night
            await self.audio.play_track("night")
            await self.app.refresh_key(0)
            await self.app.refresh_key(1)
            await self.app.refresh_key(2)

        elif key_idx == 1:
            # Day
            await self.audio.play_track("day")
            await self.app.refresh_key(0)
            await self.app.refresh_key(1)
            await self.app.refresh_key(2)

        elif key_idx == 2:
            # Play / Pause
            await self.audio.toggle_play_pause()
            await self.app.refresh_key(0)
            await self.app.refresh_key(1)
            await self.app.refresh_key(2)

        elif key_idx == 3:
            # Volume Down
            new_v = self.audio.change_volume(-self.audio.volume_step)
            self.vol_display_until = time.monotonic() + 2.0
            self.vol_display_val = new_v
            await self.app.refresh_key(3)
            await self.app.refresh_key(4)

        elif key_idx == 4:
            # Volume Up
            new_v = self.audio.change_volume(+self.audio.volume_step)
            self.vol_display_until = time.monotonic() + 2.0
            self.vol_display_val = new_v
            await self.app.refresh_key(3)
            await self.app.refresh_key(4)

        elif key_idx == 5:
            # 10 min
            self.timers.start_timer(10)
            await self.app.refresh_page()

        elif key_idx == 6:
            # 8 min
            self.timers.start_timer(8)
            await self.app.refresh_page()

        elif key_idx == 7:
            # 5 min
            self.timers.start_timer(5)
            await self.app.refresh_page()

        elif key_idx == 8:
            # 3 min
            self.timers.start_timer(3)
            await self.app.refresh_page()

        elif key_idx == 9:
            # Cancel Timer (triggers bell + stops music)
            await self.timers.cancel_timer(trigger_bell=True)
            await self.app.refresh_page()

        elif key_idx == 10:
            # Manual Bell (stops music + plays bell)
            await self.audio.play_bell()
            await self.app.refresh_key(0)
            await self.app.refresh_key(1)
            await self.app.refresh_key(2)

        elif key_idx == 11:
            # Quick adjust -30s
            if self.timers.is_running:
                self.timers.adjust_time(-30)
                await self.app.refresh_page()

        elif key_idx == 12:
            # Quick adjust +30s (or start 30s quick timer)
            self.timers.adjust_time(+30)
            await self.app.refresh_page()

        elif key_idx == 13:
            # Voice Status announcement
            await self._announce_status()

        elif key_idx == 14:
            # Go directly to System Page
            from botc_deck.pages.system import SystemPage
            await self.app.set_page(SystemPage(self.app))

    async def on_long_press(self, key_idx):
        if key_idx == 0:
            # Long press on Night -> Reset night position to 0:00
            print("[Main] Long press: Resetting Night to 0:00")
            await self.audio.reset_positions("night")
            if self.tts:
                await self.tts.speak("Nacht auf Anfang.")
            await self.app.refresh_key(0)

        elif key_idx == 1:
            # Long press on Day -> Reset day position to 0:00
            print("[Main] Long press: Resetting Day to 0:00")
            await self.audio.reset_positions("day")
            if self.tts:
                await self.tts.speak("Tag auf Anfang.")
            await self.app.refresh_key(1)

        elif key_idx == 9:
            # Long press on Stop button -> Full music reset
            print("[Main] Long press: Resetting both tracks to 0:00")
            await self.audio.reset_positions()
            if self.tts:
                await self.tts.speak("Musik auf Anfang gesetzt.")
            await self.app.refresh_key(0)
            await self.app.refresh_key(1)

        elif key_idx == 11:
            # Long press -30s button -> -1 Min
            if self.timers.is_running:
                self.timers.adjust_time(-60)
                await self.app.refresh_page()

        elif key_idx == 12:
            # Long press +30s button -> +1 Min
            self.timers.adjust_time(+60)
            await self.app.refresh_page()

        elif key_idx == 14:
            # Long press on System button -> Go to System Page
            from botc_deck.pages.system import SystemPage
            await self.app.set_page(SystemPage(self.app))

    async def _announce_status(self):
        bt = self.bluetooth
        if bt.connected_device:
            bt_text = f"Bluetooth verbunden mit {bt.connected_device.get('name', 'Gerät')}."
        else:
            bt_text = "Bluetooth nicht verbunden."

        vol_text = f"Lautstärke {self.state.volume} Prozent."

        if self.timers.is_running:
            rem_m = (self.timers.remaining_seconds + 59) // 60
            timer_text = f"Timer aktiv, noch {rem_m} Minuten."
        else:
            timer_text = "Kein Timer aktiv."

        status_msg = f"{bt_text} {vol_text} {timer_text}"
        print(f"[Status] {status_msg}")
        if self.tts:
            await self.tts.speak(status_msg)
