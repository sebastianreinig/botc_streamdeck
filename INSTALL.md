# Installation & User Guide: BotC Stream Deck

<p align="center">
  <b>English Installation Guide</b> &bull; 
  <a href="INSTALL.de.md">🇩🇪 Deutsche Anleitung</a> &bull; 
  <a href="README.md">📖 README (EN)</a> &bull; 
  <a href="README.de.md">README (DE)</a>
</p>

This guide explains how to build a dedicated, screenless hardware audio console for **Blood on the Clocktower** Storytellers using a **Raspberry Pi 3** and an **Elgato Stream Deck MK.2**.

---

## Table of Contents
1. [Required Hardware](#1-required-hardware)
2. [Step 1: Prepare MicroSD Card on Mac / PC](#2-step-1-prepare-microsd-card-on-mac--pc)
3. [Step 2: First Contact via SSH](#3-step-2-first-contact-via-ssh)
4. [Step 3: Copy Project Files & Music to the Pi](#4-step-3-copy-project-files--music-to-the-pi)
5. [Step 4: Automated Installation on the Pi](#5-step-4-automated-installation-on-the-pi)
6. [Step 5: Pair Bluetooth Speaker (Without a Screen!)](#6-step-5-pair-bluetooth-speaker-without-a-screen)
7. [Tabletop Controls & Gameplay Guide](#7-tabletop-controls--gameplay-guide)
8. [Fixing Bluetooth Audio Stutter on Raspberry Pi 3](#8-fixing-bluetooth-audio-stutter-on-raspberry-pi-3)
9. [Troubleshooting & Logs](#9-troubleshooting--logs)

---

## 1. Required Hardware

- **Raspberry Pi 3** (Model B or B+), Pi 4, or Pi Zero 2 W
- **MicroSD Card** (16 GB minimum, Class 10 or A1/A2 recommended)
- **Power Supply**: Minimum **5V / 2.5A** (Important: The Stream Deck draws its power directly from the Raspberry Pi's USB port. An underpowered charger will cause reboots or Bluetooth disconnects).
- **Elgato Stream Deck MK.2** (connected via USB to the Pi)
- **Bluetooth Speaker / Stereo System** (e.g., Anker SoundCore 2, JBL Flip)
- **Mac or PC** for the initial setup

---

## 2. Step 1: Prepare MicroSD Card on Mac / PC

1. Download and install the free **Raspberry Pi Imager**:
   - On macOS with Homebrew:
     ```bash
     brew install --cask raspberry-pi-imager
     ```
   - Or download directly from [raspberrypi.com/software](https://www.raspberrypi.com/software/)
2. Insert your MicroSD card into your computer.
3. Open **Raspberry Pi Imager**:
   - **Device**: Select `Raspberry Pi 3` (or your model).
   - **OS**: `Raspberry Pi OS (other)` ➔ `Raspberry Pi OS Lite (64-bit)` *(no desktop GUI needed)*.
   - **Storage**: Choose your MicroSD card.
4. Click **Next**. When asked *“Would you like to apply OS customization settings?”*, click **Edit Settings**:
   - **General tab**:
     - Hostname: `botc`
     - Username: `botc`
     - Password: Set a secure password.
     - Wireless LAN: Enter your Wi-Fi SSID and password, country: your country code (e.g. `DE`, `US`, `GB`).
     - Timezone: Set your local timezone (e.g. `Europe/Berlin`).
   - **Services tab**:
     - Check **Enable SSH** ➔ choose *Use password authentication* (or add your SSH public key).
5. Click **Save** and start writing.
6. Once finished, eject the card, insert it into the Raspberry Pi, connect the Stream Deck via USB, and plug in the power supply. Allow about 90 seconds on first boot.

---

## 3. Step 2: First Contact via SSH

Open your terminal and connect to the Pi:

```bash
ssh botc@botc.local
```
*(If prompted to verify the host key, type `yes` and enter your password).*

Once you see `botc@botc:~ $`, your Pi is connected and ready!

---

## 4. Step 3: Copy Project Files & Music to the Pi

Open a **new local terminal window on your Mac / PC** (not in the SSH session) and synchronize the project directory to the Pi:

```bash
cd ~/Documents/botc_streamdeck
rsync -avz --progress ./ botc@botc.local:~/botc_streamdeck/
```

*Note: Depending on the size of your `night.mp3`, `day.mp3`, and `bell.mp3` files, transfer may take 1–3 minutes over Wi-Fi.*

---

## 5. Step 4: Automated Installation on the Pi

Switch back to your **SSH terminal** on the Pi and run the automated setup script:

```bash
cd ~/botc_streamdeck
./deploy/install.sh
```

The installer takes care of:
1. Audio and Bluetooth stack (PipeWire, WirePlumber, BlueZ, MPV, Pico TTS).
2. USB permissions (`udev` rules) for non-root Stream Deck access.
3. Dedicated Python virtual environment (`venv`) with all required packages.
4. Background `systemd` user service that boots automatically on startup.

Once the script completes, perform a clean reboot:
```bash
sudo reboot
```

After ~25 seconds, your Stream Deck will light up with the custom BotC interface!

---

## 6. Step 5: Pair Bluetooth Speaker (Without a Screen!)

You never need an external monitor or keyboard. Pairing is performed **entirely from the Stream Deck keys**:

<p align="center">
  <img src="screenshots/IMG_8372.jpeg" width="48%" alt="Bluetooth Scanning on Stream Deck" />
  <img src="screenshots/IMG_8373.jpeg" width="48%" alt="Discovered Bluetooth Audio Devices" />
</p>

1. Turn on your Bluetooth speaker and put it in **Pairing Mode** (typically hold the Bluetooth button for 3 seconds until it beeps or flashes).
2. On the Stream Deck, tap **⚙️ System** (key [14]), then tap **📶 Bluetooth** (key [1]).
3. Press **🔍 Suchen / Scan** at the top.
   - The key switches to *„Scannt… / Scanning“* and scans for 10 seconds for visible Bluetooth audio devices.
4. When scanning finishes, discovered device names appear on the keys (rows 2 and 3).
5. **Tap the key displaying your speaker's name.**
   - The Pi automatically pairs, trusts, and connects to the speaker.
   - When connected, the key lights up **green** (*„Verbunden / Connected“*) and a voice confirmation plays over your speaker: *„Bluetooth verbunden mit [Speaker Name]“*.
6. Tap **← Zurück / Back** (top left) to return to the main gameplay screen.

### Automatic Reconnection (Autostart)
- The Pi saves your speaker's MAC address in `state.json`.
- On every subsequent boot, the Pi **automatically reconnects** to your speaker.
- If you powered on the speaker after the Pi: tap **Bluetooth ➔ Letztes / Last** to instantly reconnect.

---

## 7. Tabletop Controls & Gameplay Guide

<p align="center">
  <img src="screenshots/IMG_8370.jpeg" width="48%" alt="Stream Deck Main Controller Page" />
  <img src="screenshots/IMG_8371.jpeg" width="48%" alt="Stream Deck System Menu Page" />
</p>

### Main Page Key Map

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  [0] Night   │   [1] Day    │  [2] Pause   │  [3] Vol -   │  [4] Vol +   │
│  (Moon Icon) │  (Sun Icon)  │   / Resume   │    (-5%)     │    (+5%)     │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│  [5] 10 Min  │  [6] 8 Min   │  [7] 5 Min   │  [8] 3 Min   │  [9] Stop    │
│  (Live MM:SS)│  (Live MM:SS)│  (Live MM:SS)│  (Live MM:SS)│  (Bell toll) │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ [10] Bell    │ [11] -30s    │ [12] +30s    │ [13] Status  │ [14] System  │
│ (Manual toll)│ (Timer -30s) │ (+1m long)   │ (TTS Announce│   (Menu)     │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

- **🌙 Night**: Starts `night.mp3` or resumes from saved night position. *(Long press: resets night track to 0:00)*.
- **☀️ Day**: Starts `day.mp3` or resumes from saved day position. *(Long press: resets day track to 0:00)*.
- **⏯ Pause / Resume**: Temporarily freezes or unpauses music playback.
- **🔉 / 🔊 Volume**: Adjusts master volume by ±5% (current level briefly flashes on the key).
- **⏱ Timers (10 / 8 / 5 / 3 Min)**:
  - Starts the discussion countdown.
  - The active key displays live seconds remaining (`MM:SS`).
  - Below 30 seconds: turns cautionary orange.
  - Below 10 seconds: flashes urgent red.
  - At zero: **music cuts immediately** and the **Town Bell (`bell.mp3`) tolls**, calling players back to the circle. Atmospheric silence follows.
- **✖ Stop / Bell**: Stops active timer, cuts music, and tolls the bell. *(Long press: resets both day and night tracks to 0:00)*.
- **🔔 Bell**: Manually tolls the bell on demand and stops background music.
- **⏱ -30s**: Subtracts 30 seconds from active timer *(Long press: -1 min)*.
- **⏱ +30s**: Adds 30 seconds to active timer *(Long press: +1 min)*.
- **ℹ️ Status**: Speaks connection status, volume percentage, and timer status over the speaker.
- **⚙️ System**: Opens the protected settings and hardware menu.

### System Page Key Map

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  [0] Back    │ [1] Bluetooth│ [2] Light    │  [3] Wi-Fi   │  [4] Voice   │
│  (Main page) │ (Pair/Scan)  │ (100/50/15%) │   (On/Off)   │  (Mute/Unm.) │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ [5] Music    │  [6] Audio   │ [7] IP Addr  │  [8] App Rst │ [9] Power Off│
│ (Reset 0:00) │  (Restart)   │ (TTS Speak)  │  (Restart)   │ (Tap 2x)     │
├──────────────┴──────────────┴──────────────┴──────────────┴──────────────┤
│                             [10-14] Unused                               │
└──────────────────────────────────────────────────────────────────────────┘
```

- **← Back**: Returns to the main page.
- **📶 Bluetooth**: Displays status and opens device scan/pairing.
- **🔆 Light**: Cycles key backlighting (100% ➔ 50% ➔ 15%) for dark game rooms.
- **📶 Wi-Fi (On / Off)**: Disables Wi-Fi with 1 tap to eliminate 2.4 GHz interference with Bluetooth.
- **🔊 Voice**: Toggles TTS voice announcements on or off.
- **🔄 Music (Reset 0:00)**: Resets both day and night tracks to zero.
- **🛠️ Audio (Restart)**: Re-initializes MPV player engine and Bluetooth audio sink.
- **ℹ️ IP Address**: Speaks the current local IP address aloud.
- **🔁 App Restart**: Restarts the controller Python process.
- **⏻ Power Off (Tap 2x)**: Instantly blanks Stream Deck displays and executes a safe system shutdown.

---

## 8. Fixing Bluetooth Audio Stutter on Raspberry Pi 3

### Why does Bluetooth sometimes stutter on Pi 3?
The Raspberry Pi 3 uses a single shared combo chip for both 2.4 GHz Wi-Fi and Bluetooth. When Wi-Fi transmits traffic simultaneously, packet contention can cause micro-dropouts in audio streaming.

### Solution A: Disable Wi-Fi via Stream Deck (Zero extra hardware)
Since your music files reside locally on the MicroSD card, no internet connection is required during game sessions:
1. Tap **⚙️ System** on the Stream Deck.
2. Tap **📶 Wi-Fi**.
3. Wi-Fi turns off immediately (key turns red, voice confirms: *„WLAN deaktiviert“*).
4. Bluetooth now gets 100% dedicated radio bandwidth, running smoothly without dropouts.
5. Tap it again anytime to re-enable Wi-Fi when you want to update software.

### Solution B: Dedicated USB Bluetooth Dongle (Recommended for full Wi-Fi concurrency)
If you prefer keeping Wi-Fi active while streaming:
- **No code changes are needed in this project!**
- **Disable the onboard chip so Linux routes audio to the USB dongle:**
  1. Open boot config via SSH:
     ```bash
     sudo nano /boot/firmware/config.txt
     ```
     *(Or `/boot/config.txt` on older Raspberry Pi OS releases).*
  2. Add this line at the bottom:
     ```ini
     dtoverlay=disable-bt
     ```
  3. Save (`Ctrl + O`, `Enter`) and exit (`Ctrl + X`).
  4. Disable internal UART service and reboot:
     ```bash
     sudo systemctl disable hciuart
     sudo reboot
     ```
- The USB adapter will automatically become primary adapter `hci0`, and all Stream Deck controls will operate through it seamlessly.

---

## 9. Troubleshooting & Logs

### Check service status
```bash
systemctl --user status botc-deck
```

### View real-time logs
```bash
journalctl --user -u botc-deck -f
```

### Restart application service
```bash
systemctl --user restart botc-deck
```

### Stream Deck not detected
- Run `lsusb` and verify that an Elgato device is listed.
- Reload `udev` rules:
  ```bash
  sudo udevadm control --reload-rules && sudo udevadm trigger
  ```
- Check power supply: If the red power LED on the Pi blinks, your power supply is experiencing undervoltage. Use an official 5V / 2.5A or 3A supply.
