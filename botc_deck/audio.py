import asyncio
import os
import shutil
import subprocess
import time

try:
    import mpv
    HAS_PYTHON_MPV = True
except (ImportError, OSError):
    HAS_PYTHON_MPV = False

class AudioEngine:
    def __init__(self, config, state):
        self.config = config
        self.state = state
        self.fade_duration = float(config.get("audio", "fade_duration", default=1.5))
        self.volume_step = int(config.get("audio", "volume_step", default=5))
        self.day_file = config.resolve_path(config.get("paths", "day_track"))
        self.night_file = config.resolve_path(config.get("paths", "night_track"))
        self.bell_file = config.resolve_path(config.get("paths", "bell_sound"))

        self.current_track = None  # "day", "night"
        self.is_playing = False
        self.is_paused = False
        self._fade_task = None

        # mpv instances
        self.player_music = None
        self.player_bell = None
        self.player_tts = None
        self._init_players()

    def _init_players(self):
        if HAS_PYTHON_MPV:
            try:
                self.player_music = mpv.MPV(
                    ytdl=False,
                    video=False,
                    keep_open=False,
                    idle=True,
                    ao="pipewire,pulse,alsa",
                    audio_device="auto"
                )
                self.player_music.volume = self.state.volume
                self.player_music.loop_file = "inf"

                self.player_bell = mpv.MPV(
                    ytdl=False,
                    video=False,
                    keep_open=False,
                    idle=True,
                    ao="pipewire,pulse,alsa",
                    audio_device="auto"
                )
                self.player_bell.volume = self.state.volume

                self.player_tts = mpv.MPV(
                    ytdl=False,
                    video=False,
                    keep_open=False,
                    idle=True,
                    ao="pipewire,pulse,alsa",
                    audio_device="auto"
                )
                self.player_tts.volume = self.state.volume
                print("[Audio] Initialized python-mpv audio engine successfully.")
                return
            except Exception as e:
                print(f"[Audio] python-mpv init failed ({e}), falling back to CLI mpv subprocess.")

        # Subprocess fallback if python-mpv is not available
        self.player_music = None

    async def play_track(self, track_type):
        """
        Switch to track_type ("day" or "night").
        Performs smooth transition and resumes from stored position.
        """
        if self._fade_task and not self._fade_task.done():
            self._fade_task.cancel()

        target_file = self.day_file if track_type == "day" else self.night_file
        if not os.path.exists(target_file):
            print(f"[Audio] File not found: {target_file}")
            return

        # If already playing this track
        if self.current_track == track_type:
            if self.is_playing and not self.is_paused:
                print(f"[Audio] Already playing {track_type}.")
                return
            elif self.player_music and self.is_paused:
                print(f"[Audio] Resuming paused {track_type}...")
                try:
                    self.player_music.pause = False
                except Exception as e:
                    print(f"[Audio] Error unpausing: {e}")
                self.is_playing = True
                self.is_paused = False
                return

        self._fade_task = asyncio.create_task(self._transition_to(track_type, target_file))
        await self._fade_task

    async def _transition_to(self, track_type, target_file):
        # 1. Save position and pause old track if active
        if self.is_playing and not self.is_paused and self.player_music:
            self._save_current_position()
            try:
                self.player_music.pause = True
            except Exception:
                pass

        # 2. Switch track
        self.current_track = track_type
        self.state.active_mode = track_type
        resume_pos = self.state.day_position if track_type == "day" else self.state.night_position

        print(f"[Audio] Starting {track_type} ({os.path.basename(target_file)}) at pos {resume_pos:.1f}s, vol {self.state.volume}%")

        if self.player_music:
            try:
                start_sec = f"{resume_pos:.2f}" if resume_pos > 0 else "0"
                self.player_music.loadfile(target_file, mode="replace", start=start_sec)
                self.player_music.pause = False
                self.player_music.volume = self.state.volume
                self.player_music.loop_file = "inf"
                self.is_playing = True
                self.is_paused = False
            except Exception as e:
                print(f"[Audio] Error starting playback: {e}")
        else:
            # Subprocess fallback
            self.is_playing = True
            self.is_paused = False
            self._save_current_position()

    def _save_current_position(self):
        if not self.player_music:
            return
        try:
            pos = self.player_music.time_pos
            if pos is not None and pos > 0:
                if self.current_track == "day":
                    self.state.day_position = float(pos)
                elif self.current_track == "night":
                    self.state.night_position = float(pos)
                self.state.save()
        except Exception:
            pass

    async def toggle_play_pause(self):
        if not self.is_playing and self.is_paused:
            # Resume current track
            mode = self.current_track or self.state.active_mode or "day"
            await self.play_track(mode)
            return

        if not self.is_playing:
            mode = self.state.active_mode or "day"
            await self.play_track(mode)
            return

        if self.player_music:
            if self.is_paused:
                try:
                    self.player_music.pause = False
                except Exception:
                    pass
                self.is_paused = False
                print(f"[Audio] Resumed {self.current_track}.")
            else:
                self._save_current_position()
                try:
                    self.player_music.pause = True
                except Exception:
                    pass
                self.is_paused = True
                print(f"[Audio] Paused {self.current_track}.")

    async def stop(self):
        """
        Stops music and preserves position for resume.
        """
        if self._fade_task and not self._fade_task.done():
            self._fade_task.cancel()

        if self.is_playing or not self.is_paused:
            self._save_current_position()
            if self.player_music:
                try:
                    self.player_music.pause = True
                except Exception:
                    pass
            self.is_playing = False
            self.is_paused = True
            print(f"[Audio] Stopped {self.current_track}.")

    async def play_bell(self):
        """
        Plays bell.mp3 immediately.
        Per requirement: Stops the running music, plays the bell, then remains silent.
        """
        await self.stop()
        if not os.path.exists(self.bell_file):
            print(f"[Audio] Bell file not found: {self.bell_file}")
            return

        print("[Audio] Playing bell sound...")
        if self.player_bell:
            try:
                self.player_bell.volume = self.state.volume
                self.player_bell.play(self.bell_file)
            except Exception as e:
                print(f"[Audio] Bell playback error: {e}")
        else:
            if shutil.which("mpv"):
                subprocess.Popen(["mpv", "--no-video", f"--volume={self.state.volume}", self.bell_file])

    async def play_audio_file(self, file_path):
        """Play a one-shot audio file (e.g. for TTS speech announcements)."""
        if not os.path.exists(file_path):
            return
        if self.player_tts:
            try:
                self.player_tts.volume = min(100, self.state.volume + 10)
                self.player_tts.play(file_path)
            except Exception as e:
                print(f"[Audio] One-shot playback error: {e}")
        elif shutil.which("mpv"):
            subprocess.Popen(["mpv", "--no-video", f"--volume={self.state.volume}", file_path])

    def change_volume(self, delta):
        new_vol = max(0, min(100, self.state.volume + delta))
        self.state.volume = new_vol
        self.state.save()
        if self.player_music and not self.is_paused:
            try:
                self.player_music.volume = new_vol
            except Exception:
                pass
        if self.player_bell:
            try:
                self.player_bell.volume = new_vol
            except Exception:
                pass
        if self.player_tts:
            try:
                self.player_tts.volume = new_vol
            except Exception:
                pass
        print(f"[Audio] Master Volume set to {new_vol}%")
        return new_vol

    async def reset_positions(self, track_type=None):
        """Reset saved playback positions to 0:00. If track_type is None, resets both."""
        if track_type == "day":
            self.state.day_position = 0.0
            print("[Audio] Day position reset to 0:00.")
        elif track_type == "night":
            self.state.night_position = 0.0
            print("[Audio] Night position reset to 0:00.")
        else:
            self.state.day_position = 0.0
            self.state.night_position = 0.0
            print("[Audio] Both Day & Night positions reset to 0:00.")
        self.state.save()

        # If the reset track is currently playing, reload it immediately from 0:00
        if self.is_playing and (track_type is None or self.current_track == track_type):
            target_file = self.day_file if self.current_track == "day" else self.night_file
            if self.player_music:
                try:
                    self.player_music.loadfile(target_file, mode="replace", start="0")
                    self.player_music.pause = False
                    self.player_music.volume = self.state.volume
                except Exception as e:
                    print(f"[Audio] Error reloading after reset: {e}")

    def reinit_audio(self):
        """Re-initializes all mpv players in case of audio glitches or device switches."""
        print("[Audio] Re-initializing audio engine players...")
        if self.player_music:
            try:
                self.player_music.terminate()
            except Exception:
                pass
        if self.player_bell:
            try:
                self.player_bell.terminate()
            except Exception:
                pass
        if self.player_tts:
            try:
                self.player_tts.terminate()
            except Exception:
                pass
        self._init_players()
