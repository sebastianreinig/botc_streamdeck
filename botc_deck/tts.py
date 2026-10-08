import asyncio
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess

class TTSEngine:
    def __init__(self, config, audio_engine):
        self.config = config
        self.audio = audio_engine
        self.enabled = bool(config.get("system", "tts_enabled", default=True))
        self.cache_dir = Path(config.resolve_path(config.get("paths", "tts_cache_dir", default="cache_tts")))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._has_pico = shutil.which("pico2wave") is not None
        self._has_espeak = shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None
        self._is_mac = platform.system() == "Darwin"

    def _get_cache_path(self, text):
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        return self.cache_dir / f"tts_{h}.wav"

    async def speak(self, text):
        """Generate and play spoken German text."""
        if not self.enabled:
            return

        cache_path = self._get_cache_path(text)
        if not cache_path.exists():
            await self._render_tts(text, cache_path)

        if cache_path.exists():
            await self.audio.play_audio_file(str(cache_path))

    async def _render_tts(self, text, out_wav):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._render_tts_sync, text, out_wav)

    def _render_tts_sync(self, text, out_wav):
        tmp_file = str(out_wav) + ".tmp.wav"
        try:
            if self._has_pico:
                # Pico TTS on Debian/Raspberry Pi (SVOX Pico, natural sounding)
                subprocess.run(
                    ["pico2wave", "-l", "de-DE", "-w", tmp_file, text],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if os.path.exists(tmp_file):
                    os.replace(tmp_file, out_wav)
                    return
            elif self._is_mac:
                # macOS 'say' command with Anna (German) or default
                aiff_file = str(out_wav) + ".aiff"
                subprocess.run(
                    ["say", "-v", "Anna", "-o", aiff_file, text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # Convert AIFF to WAV if ffmpeg/sox or afconvert exists
                if shutil.which("afconvert"):
                    subprocess.run(
                        ["afconvert", "-f", "WAVE", "-d", "LEI16", aiff_file, str(out_wav)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                if os.path.exists(aiff_file):
                    os.remove(aiff_file)
                return
            elif self._has_espeak:
                espeak_bin = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
                subprocess.run(
                    [espeak_bin, "-v", "de", "-w", str(out_wav), text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            print(f"[TTS] Error rendering speech '{text}': {e}")
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass
