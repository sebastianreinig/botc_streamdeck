#!/bin/bash
# Disables WiFi on Raspberry Pi 3 to prevent 2.4 GHz interference with Bluetooth A2DP audio
echo "Disabling WiFi on Raspberry Pi..."

if command -v rfkill &> /dev/null; then
    sudo rfkill block wifi
fi

if command -v nmcli &> /dev/null; then
    sudo nmcli radio wifi off
fi

echo "WiFi disabled. Bluetooth now has maximum antenna bandwidth."
