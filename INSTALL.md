# Installations- und Bedienungsanleitung: BotC Stream Deck

Dieses Projekt verwandelt einen **Raspberry Pi 3** und ein **Elgato Stream Deck MK.2** in eine eigenständige, bildschirmlose Steuerkonsole für **Blood on the Clocktower** Spielleiter.

---

## Inhaltsverzeichnis
1. [Benötigte Hardware](#1-benötigte-hardware)
2. [Schritt 1: SD-Karte am Mac vorbereiten](#2-schritt-1-sd-karte-am-mac-vorbereiten)
3. [Schritt 2: Erstkontakt per SSH vom Mac](#3-schritt-2-erstkontakt-per-ssh-vom-mac)
4. [Schritt 3: Projektdateien & Musik auf den Pi übertragen](#4-schritt-3-projektdateien--musik-auf-den-pi-übertragen)
5. [Schritt 4: Automatische Installation auf dem Pi](#5-schritt-4-automatische-installation-auf-dem-pi)
6. [Schritt 5: Bluetooth-Stereoanlage koppeln (ohne Bildschirm!)](#6-schritt-5-bluetooth-stereoanlage-koppeln-ohne-bildschirm)
7. [Bedienung am Spielabend](#7-bedienung-am-spielabend)
8. [Tipps gegen Bluetooth-Ruckler (Pi 3 Besonderheit)](#8-tipps-gegen-bluetooth-ruckler-pi-3-besonderheit)
9. [Fehlerbehebung & Logs](#9-fehlerbehebung--logs)

---

## 1. Benötigte Hardware

- **Raspberry Pi 3** (Modell B oder B+)
- **MicroSD-Karte** (mindestens 16 GB, Class 10 oder A1/A2 empfohlen)
- **Netzteil für den Pi**: Min. **5V / 2.5A** (Wichtig: Das Stream Deck bezieht seinen Strom komplett über den USB-Port des Pi. Ein schwaches Handy-Netzteil führt zu Neustarts oder Verbindungsabbrüchen).
- **Elgato Stream Deck MK.2** (per USB am Pi angeschlossen)
- **Bluetooth-Lautsprecher / Stereoanlage**
- **Dein Mac** für die Ersteinrichtung

---

## 2. Schritt 1: SD-Karte am Mac vorbereiten

1. Lade dir auf dem Mac den kostenlosen **Raspberry Pi Imager** herunter:
   ```bash
   brew install --cask raspberry-pi-imager
   ```
   *(Oder direkt von [raspberrypi.com/software](https://www.raspberrypi.com/software/))*
2. Stecke die MicroSD-Karte in deinen Mac.
3. Öffne den **Raspberry Pi Imager**:
   - **Gerät**: `Raspberry Pi 3`
   - **Betriebssystem**: `Raspberry Pi OS (other)` ➔ `Raspberry Pi OS Lite (64-bit)` *(keine Desktop-GUI nötig)*
   - **Speichermedium**: Deine SD-Karte auswählen
4. Klicke auf **Weiter**. Bei der Frage *„Möchten Sie die OS-Anpassung anwenden?“* klicke auf **Einstellungen bearbeiten**:
   - **Reiter Allgemein**:
     - Hostname: `botc`
     - Benutzername: `botc`
     - Passwort festlegen (z. B. ein sicheres Passwort notieren)
     - WLAN einrichten: Dein Heim-WLAN (SSID + Passwort) eintragen, Land: `DE`
     - Zeitzone: `Europe/Berlin`
   - **Reiter Dienste**:
     - **SSH aktivieren** anhaken ➔ *Passwortauthentifizierung verwenden* (oder deinen SSH-Schlüssel anhaken).
5. Klicke auf **Speichern** und starte den Schreibvorgang.
6. Nach Abschluss SD-Karte auswerfen, in den Raspberry Pi stecken und das Netzteil anschließen. Warte ca. 90 Sekunden beim ersten Start.

---

## 3. Schritt 2: Erstkontakt per SSH vom Mac

Öffne das Terminal auf deinem Mac und verbinde dich mit dem Pi:

```bash
ssh botc@botc.local
```
*(Falls du nach dem Host-Key gefragt wirst, mit `yes` bestätigen und dein festgelegtes Passwort eingeben).*

Wenn du die Eingabeaufforderung `botc@botc:~ $` siehst, läuft dein Pi einwandfrei!

---

## 4. Schritt 3: Projektdateien & Musik auf den Pi übertragen

Öffne ein **neues Terminal-Fenster auf deinem Mac** (nicht im SSH-Fenster, sondern lokal) und synchronisiere diesen Projektordner direkt auf den Pi:

```bash
cd ~/Documents/botc_streamdeck
rsync -avz --progress ./ botc@botc.local:~/botc_streamdeck/
```

*Hinweis: Da die drei MP3-Dateien (`night.mp3`, `day.mp3`, `bell.mp3`) zusammen ca. 390 MB groß sind, dauert die Übertragung je nach WLAN-Geschwindigkeit 1 bis 3 Minuten.*

---

## 5. Schritt 4: Automatische Installation auf dem Pi

Wechsle wieder in das **SSH-Terminal** auf dem Pi und führe das vorbereitete Installationsskript aus:

```bash
cd ~/botc_streamdeck
./deploy/install.sh
```

Das Skript erledigt vollautomatisch:
1. Installation aller Audio- und Bluetooth-Dienste (PipeWire, WirePlumber, BlueZ, MPV, Pico TTS).
2. Vergabe der USB-Rechte (`udev`), damit das Stream Deck ohne Root-Rechte läuft.
3. Erstellung des isolierten Python-Environments (`venv`) und Installation aller Bibliotheken.
4. Einrichtung des `systemd`-Autostarts (startet bei jedem Boot automatisch im Hintergrund).

Nach Abschluss starte den Pi einmal sauber neu:
```bash
sudo reboot
```

Nach ca. 25 Sekunden leuchtet das Stream Deck auf und zeigt die Benutzeroberfläche!

---

## 6. Schritt 5: Bluetooth-Stereoanlage koppeln (ohne Bildschirm!)

Du benötigst weder Monitor noch Tastatur. Die Bluetooth-Kopplung erfolgt **direkt über das Stream Deck**:

1. Schalte deine Bluetooth-Stereoanlage / Box ein und aktiviere den **Pairing-Modus** (meist BT-Taste an der Box 3 Sekunden gedrückt halten, bis sie blinkt/ein Ton ertönt).
2. Drücke auf dem Stream Deck die Taste **📶 Bluetooth** (Reihe 3, Taste 2).
3. Drücke oben auf **🔍 Suchen**.
   - Die Taste wechselt zu *„Scannt…“* und sucht 10 Sekunden nach sichtbaren Bluetooth-Audiogeräten.
4. Nach dem Suchlauf erscheinen die Namen der gefundenen Geräte auf den Tasten (Reihe 2 und 3).
5. **Tippe die Taste mit dem Namen deiner Stereoanlage an.**
   - Der Pi koppelt, vertraut und verbindet sich automatisch mit der Anlage.
   - Sobald die Verbindung steht, leuchtet die Taste **grün** auf (*„Verbunden“*) und über den Lautsprecher ertönt die deutsche Sprachansage: *„Bluetooth verbunden mit [Name]“*.
6. Drücke oben links auf **← Zurück**, um zur Hauptseite zurückzukehren.

### Automatisches Wiederverbinden (Autostart)
- Der Pi speichert die Adresse deiner Anlage in `state.json`.
- Bei jedem zukünftigen Einschalten verbindet sich der Pi **vollautomatisch** mit dieser Anlage.
- Falls die Anlage erst nach dem Pi eingeschaltet wurde: Ein Druck auf **Bluetooth ➔ Letztes** stellt die Verbindung sofort wieder her.

---

## 7. Bedienung am Spielabend

### Tastenbelegung (Hauptseite)

```
[  🌙 Nacht  ] [   ☀️ Tag   ] [ ⏯ Pause/Go ] [ 🔉 Leiser  ] [ 🔊 Lauter  ]
[  ⏱ 10 Min  ] [  ⏱ 8 Min   ] [  ⏱ 5 Min   ] [  ⏱ 3 Min   ] [ ✖ Stop/Glocke]
[  🔔 Glocke ] [  ⏱ -30s   ] [  ⏱ +30s   ] [  ℹ️ Status  ] [  ⚙️ System   ]
```

- **🌙 Nacht**: Startet `night.mp3` bzw. setzt an der gemerkten Position fort. *(Lange drücken: Setzt Nacht auf 0:00 zurück).*
- **☀️ Tag**: Startet `day.mp3` bzw. setzt an der gemerkten Position fort. *(Lange drücken: Setzt Tag auf 0:00 zurück).*
- **⏯ Pause / Weiter**: Pausiert die laufende Musik bzw. setzt sie fort.
- **🔉 / 🔊 Lautstärke**: Ändert die Master-Lautstärke in 5%-Schritten (der aktuelle Prozentwert wird kurz auf der Taste eingeblendet).
- **⏱ Timer (10 / 8 / 5 / 3 Min)**:
  - Startet den Countdown.
  - Die gedrückte Taste zeigt **sekundengenau die Restzeit** (z. B. `07:42`).
  - Unter 30 Sekunden: Taste wechselt zu Warn-Orange.
  - Unter 10 Sekunden: Taste blinkt Alarm-Rot.
  - Bei Ablauf: **Die Musik stoppt sofort** und die **Glocke (`bell.mp3`) ertönt**, um die Stadt zum Kreis zu rufen. Danach bleibt es still.
- **✖ Stop / Glocke**: Bricht den laufenden Timer vorzeitig ab, stoppt die Musik und schlägt die Glocke. *(Lange drücken: Setzt beide Musik-Tracks auf 0:00 zurück).*
- **🔔 Glocke**: Schlägt die Glocke sofort manuell und stoppt laufende Musik.
- **⏱ -30s**: Zieht 30 Sekunden vom laufenden Timer ab *(Lange drücken: -1 Min)*.
- **⏱ +30s**: Verlängert den laufenden Timer um 30 Sekunden *(Lange drücken: +1 Min)*.
- **ℹ️ Status**: Sprachansage über die Lautsprecher (Verbindung, Lautstärke, Timer-Status).
- **⚙️ System**: Öffnet das geschützte System-Menü.

### Systemseite (Sicherheit, Hardware & Wartung)
```
[  ← Zurück  ] [ 📶 Bluetooth] [  🔆 Licht   ] [  📶 WLAN    ] [  🔊 Sprache ]
[  🔄 Musik  ] [  🛠️ Audio   ] [  ℹ️ IP-Adr.  ] [  🔁 App Neu ] [  ⏻ Power Off]
```
- **← Zurück**: Kehrt zur Hauptseite zurück.
- **📶 Bluetooth**: Zeigt Status & öffnet das Kopplungsmenü (geschützt vor Fehlbedienung).
- **🔆 Licht**: Schaltet die Tastenhelligkeit um (100% ➔ 50% ➔ 15% für atmosphärisch abgedunkelte Nachtrunden).
- **📶 WLAN (An / Aus)**: Schaltet das WLAN per Knopfdruck ab (für ungestörten Bluetooth-Betrieb vor Ort) oder wieder ein.
- **🔊 Sprache**: Schaltet Sprachansagen stumm oder wieder ein.
- **🔄 Musik (Reset 0:00)**: Setzt Tag- und Nachtmusik sofort auf Sekunde 0 zurück.
- **🛠️ Audio (Neustart)**: Startet das Audio-Subsystem (MPV-Engine) frisch neu und bindet Bluetooth neu an.
- **ℹ️ IP-Adresse**: Sagt die aktuelle IP-Adresse per Sprache an.
- **🔁 App Neu**: Startet die Steuerungs-App neu.
- **⏻ Power Off (2× drücken)**: Dunkelt das Stream Deck sofort ab und fährt den Pi sauber herunter.

---

## 8. Tipps gegen Bluetooth-Ruckler & USB-Dongle Einrichtung

### Warum ruckelt Bluetooth beim Pi 3 manchmal?
Der Raspberry Pi 3 nutzt **einen einzigen Chip für 2.4 GHz WLAN und Bluetooth**. Wenn der Pi gleichzeitig Daten über WLAN funkt, teilen sich beide Funktionen dieselbe Frequenz – das kann zu Tonaussetzern bei Bluetooth führen.

### Lösung A: WLAN per Stream Deck ausschalten (Keine Extra-Hardware nötig)
Da alle MP3s lokal auf der SD-Karte liegen, brauchst du vor Ort kein Internet:
1. Halte auf dem Stream Deck die Taste **⏻ System** 1,5 Sekunden lang gedrückt.
2. Drücke auf die Taste **📶 WLAN**.
3. Das WLAN schaltet sich sofort ab (Taste leuchtet rot, Ansage: *„WLAN deaktiviert“*).
4. Bluetooth hat nun 100% der internen Funkbandbreite und läuft glasklar und stabil.
5. Zuhause kannst du dieselbe Taste einfach erneut drücken, um das WLAN für Updates wieder einzuschalten!

### Lösung B: USB-Bluetooth-Stick nutzen (Ideal, wenn WLAN an bleiben soll)
Möchtest du einen externen USB-Bluetooth-Stick verwenden (z. B. für noch höhere Reichweite oder paralleles WLAN):
- **Am Code / Python-Skript muss gar nichts geändert werden!**
- **Wichtig am Pi:** Der Pi 3 hat bereits einen internen Bluetooth-Chip (`hci0`). Damit Linux den neuen USB-Stick als Hauptadapter verwendet und der interne Chip nicht stört, schaltet man den internen Chip einfach ab:
  1. Öffne die Boot-Konfiguration per SSH:
     ```bash
     sudo nano /boot/firmware/config.txt
     ```
     *(Bei älterem Raspberry Pi OS: `/boot/config.txt`)*
  2. Füge ganz unten folgende Zeile hinzu:
     ```ini
     dtoverlay=disable-bt
     ```
  3. Speichern mit `Strg + O`, `Enter` und Beenden mit `Strg + X`.
  4. Deaktiviere den Dienst für den alten internen Chip und starte neu:
     ```bash
     sudo systemctl disable hciuart
     sudo reboot
     ```
- **Ergebnis:** Der USB-Stick wird automatisch als primärer Bluetooth-Adapter (`hci0`) geladen. Unser Skript, PipeWire und BlueZ steuern ihn direkt ohne jede Anpassung an.

---

## 9. Fehlerbehebung & Logs

### Dienststatus prüfen
```bash
systemctl --user status botc-deck
```

### Live-Logs mitlesen
```bash
journalctl --user -u botc-deck -f
```

### Dienst neu starten
```bash
systemctl --user restart botc-deck
```

### Stream Deck wird nicht erkannt
- Prüfe mit `lsusb`, ob ein Gerät von `Elgato` aufgeführt ist.
- Stelle sicher, dass die udev-Regel aktiv ist:
  ```bash
  sudo udevadm control --reload-rules && sudo udevadm trigger
  ```
- Prüfe das Netzteil: Wenn das rote Power-LED am Pi blinkt, hat der Pi Unterspannung. Nutze ein offizielles Raspberry Pi 5V / 2.5A Netzteil.
