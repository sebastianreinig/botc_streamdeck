#!/bin/bash
set -e

# Blood on the Clocktower - Raspberry Pi Setup Script
# Run this directly on the Raspberry Pi: ./deploy/install.sh

echo "=========================================================="
echo "  BotC Stream Deck - Installation & System Setup"
echo "=========================================================="

if [ "$EUID" -eq 0 ]; then
    echo "Bitte NICHT als root/sudo ausführen! Führe das Skript als normaler Benutzer (z.B. botc) aus."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "--> 1. Systempakete aktualisieren und Abhängigkeiten installieren..."
sudo apt update
sudo apt install -y \
    python3-venv \
    python3-pip \
    python3-dev \
    libhidapi-libusb0 \
    libhidapi-dev \
    libmpv2 \
    mpv \
    pipewire \
    pipewire-pulse \
    wireplumber \
    libspa-0.2-bluetooth \
    bluez \
    bluetooth \
    rfkill \
    fonts-dejavu-core \
    libjpeg-dev \
    zlib1g-dev

# Versuche pico2wave (beste Offline-Sprachqualität), sonst Fallback auf espeak-ng
if sudo apt install -y libttspico-utils 2>/dev/null; then
    echo "Pico TTS erfolgreich installiert."
else
    echo "libttspico-utils nicht in Standard-Quellen; installiere espeak-ng als Fallback..."
    sudo apt install -y espeak-ng
fi

echo "--> 2. Benutzer-Berechtigungen für USB & Audio setzen..."
sudo usermod -a -G input,plugdev,audio,bluetooth "$USER"

echo "--> 2b. Passwordless Shutdown & Poweroff einrichten..."
echo "$USER ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/poweroff, /bin/systemctl poweroff, /bin/systemctl reboot" | sudo tee /etc/sudoers.d/botc-poweroff > /dev/null
sudo chmod 0440 /etc/sudoers.d/botc-poweroff

echo "--> 3. udev-Regeln für Elgato Stream Deck einrichten..."
sudo cp "$PROJECT_DIR/deploy/99-streamdeck.rules" /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "--> 4. Bluetooth konfigurieren (Auto-Power-On)..."
sudo sed -i 's/#AutoEnable=true/AutoEnable=true/g' /etc/bluetooth/main.conf 2>/dev/null || true
sudo systemctl enable --now bluetooth

echo "--> 4b. WirePlumber Headless-Bluetooth-Fix anwenden..."
sudo sed -i 's/if seat_state == "active" then/if seat_state == "active" or seat_state == "online" then/g' /usr/share/wireplumber/scripts/monitors/bluez.lua 2>/dev/null || true
sudo mkdir -p /etc/wireplumber/wireplumber.conf.d
sudo tee /etc/wireplumber/wireplumber.conf.d/bluetooth.conf > /dev/null << 'EOF'
wireplumber.profiles = {
  main = {
    hardware.bluetooth = required
    monitor.bluez.seat-monitoring = disabled
  }
}
EOF

echo "--> 5. Python Virtual Environment einrichten..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "--> 6. Tasten-Icons generieren..."
./venv/bin/python3 assets/generate_icons.py

echo "--> 7. Autostart via systemd (User-Service) einrichten..."
mkdir -p "$HOME/.config/systemd/user"
cp "$PROJECT_DIR/deploy/botc-deck.service" "$HOME/.config/systemd/user/botc-deck.service"

# Erlaube User-Dienste beim Booten ohne aktiven SSH/GUI-Login
loginctl enable-linger "$USER"

systemctl --user daemon-reload
systemctl --user enable botc-deck.service

echo "=========================================================="
echo "  Installation erfolgreich abgeschlossen!"
echo "=========================================================="
echo "Um den Dienst sofort zu starten:"
echo "  systemctl --user start botc-deck.service"
echo ""
echo "Um Live-Logs anzusehen:"
echo "  journalctl --user -u botc-deck -f"
echo ""
echo "Empfehlung: Starte den Pi jetzt einmal neu mit: sudo reboot"
