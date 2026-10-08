import asyncio
import time

class TimerManager:
    def __init__(self, audio_engine, on_tick=None):
        self.audio = audio_engine
        self.on_tick = on_tick  # async callback(remaining_seconds, total_seconds, timer_idx)

        self.running_task = None
        self.active_minutes = None
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.is_running = False
        self._end_time = 0

    def start_timer(self, minutes):
        """Start or replace a timer."""
        if self.running_task and not self.running_task.done():
            self.running_task.cancel()

        self.active_minutes = minutes
        self.total_seconds = int(minutes * 60)
        self.remaining_seconds = self.total_seconds
        self.is_running = True
        self._end_time = time.monotonic() + self.remaining_seconds

        self.running_task = asyncio.create_task(self._run_loop())
        print(f"[Timer] Started {minutes} minute timer ({self.total_seconds}s)")

    def adjust_time(self, delta_seconds):
        """Add or subtract seconds from the running timer (e.g. +30s, +60s, -30s)."""
        if not self.is_running:
            if delta_seconds > 0:
                self.start_timer(delta_seconds / 60)
            return self.remaining_seconds

        self._end_time += delta_seconds
        new_rem = max(1, int(round(self._end_time - time.monotonic())))
        self.remaining_seconds = new_rem
        if self.remaining_seconds > self.total_seconds:
            self.total_seconds = self.remaining_seconds
        print(f"[Timer] Adjusted timer by {delta_seconds:+d}s -> {self.remaining_seconds}s remaining.")
        return self.remaining_seconds

    async def cancel_timer(self, trigger_bell=True):
        """Cancel current timer. Triggers bell sound as specified."""
        if not self.is_running:
            return

        print("[Timer] Timer cancelled.")
        if self.running_task and not self.running_task.done():
            self.running_task.cancel()

        self.is_running = False
        self.active_minutes = None
        self.remaining_seconds = 0
        self._end_time = 0

        if self.on_tick:
            try:
                await self.on_tick(0, 0, None)
            except Exception:
                pass

        if trigger_bell:
            await self.audio.play_bell()

    async def _run_loop(self):
        try:
            while self._end_time > time.monotonic():
                self.remaining_seconds = max(0, int(round(self._end_time - time.monotonic())))
                if self.on_tick:
                    try:
                        await self.on_tick(self.remaining_seconds, self.total_seconds, self.active_minutes)
                    except Exception as e:
                        print(f"[Timer] on_tick error: {e}")

                await asyncio.sleep(1.0)

            # Timer finished!
            print(f"[Timer] Timer finished! Triggering bell.")
            self.remaining_seconds = 0
            self.is_running = False
            self.active_minutes = None
            self._end_time = 0
            if self.on_tick:
                try:
                    await self.on_tick(0, 0, None)
                except Exception:
                    pass

            await self.audio.play_bell()

        except asyncio.CancelledError:
            pass

    def get_remaining_str(self):
        if not self.is_running or self.remaining_seconds <= 0:
            return ""
        m = self.remaining_seconds // 60
        s = self.remaining_seconds % 60
        return f"{m:02d}:{s:02d}"

