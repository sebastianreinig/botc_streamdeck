# Blood on the Clocktower – Stream Deck Controller 🕰️

<p align="center">
  <a href="README.md">🇬🇧 English Version</a> &bull; 
  <a href="README.de.md"><b>🇩🇪 Deutsche Version</b></a> &bull; 
  <a href="INSTALL.de.md">📖 Installationsanleitung (DE)</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" />
  <img src="https://img.shields.io/badge/Python-3.11+-brightgreen.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Platform-Raspberry%20Pi-red.svg" alt="Raspberry Pi" />
  <img src="https://img.shields.io/badge/Hardware-Stream%20Deck%20MK.2-blueviolet.svg" alt="Elgato Stream Deck MK.2" />
</p>

Ein autonomes Hardware-Steuerpult für den Spielleiter (Storyteller) von **Blood on the Clocktower**, betrieben auf einem **Raspberry Pi** mit einem **Elgato Stream Deck** (15 Tasten). 

Entwickelt für den screenlosen Standalone-Betrieb am Spieltisch – inklusive drahtloser Bluetooth-Audio-Ausgabe, Live-Countdowns auf den Tasten, nahtlosem Musik-Crossfade und Sprachrückmeldungen.

---

## Live-Eindrücke (Hardware im Einsatz)

<p align="center">
  <img src="screenshots/IMG_8370.jpeg" width="48%" alt="Hauptseite - Spielbetrieb" />
  <img src="screenshots/IMG_8371.jpeg" width="48%" alt="System-Menü - Einstellungen" />
</p>
<p align="center">
  <em>Links: Hauptseite während der Spielrunde &bull; Rechts: Geschütztes System-Menü</em>
</p>

<p align="center">
  <img src="screenshots/IMG_8372.jpeg" width="48%" alt="Bluetooth-Suchlauf auf dem Stream Deck" />
  <img src="screenshots/IMG_8373.jpeg" width="48%" alt="Gefundene Bluetooth-Geräte zum Koppeln" />
</p>
<p align="center">
  <em>Screenlose Bluetooth-Verwaltung: Geräte suchen (links) und per Knopfdruck koppeln (rechts).</em>
</p>

---

## Highlights

* 🎵 **Tag- & Nacht-Atmosphäre**: Sanfter Wechsel zwischen Tag- und Nachtmusik. Das System merkt sich für Tag und Nacht sekundengenau die Position und setzt die Musik beim Phasenwechsel nahtlos fort.
* 🩸 **Atmosphärisches Nacht-Theme (Grimoire-Rot)**: Beim Wechsel in die Nacht-Phase schalten alle Tastenbeschriftungen und Umrandungen automatisch auf blutroten Nachtsicht-Modus mit dezentem Weinrot-Rahmen um. Am Tag kehrt alles zu strahlendem Weiß zurück – perfekt für stimmungsvolle Runden im Halbdunkel.
* ⏱️ **Timer mit Live-Countdown**: 10, 8, 5 und 3 Minuten mit minütlicher/sekundlicher Restzeitanzeige (`MM:SS`) direkt auf der Taste. Farbwarnung bei `<30s` (Orange) und Alarm bei `<10s` (Rot).

* ⚡ **Quick-Adjust (+30s / -30s)**: Mitten in hitzigen Diskussionen mit einem Fingertipp spontan +30 Sekunden Nachspielzeit spendieren (oder lang drücken für +1 Minute).
* 🔔 **Glocke & Stopp-Automatik**: Timer-Ende, Timer-Abbruch oder Glocken-Taste stoppen die Musik und läuten `bell.mp3`. Danach bleibt es atmosphärisch still, bis die nächste Phase gestartet wird.
* 📶 **Headless Bluetooth (Ohne Monitor)**: Vollständige Gerätesuche und Kopplung direkt über das Stream Deck. Gefundene Boxen (z. B. Anker SoundCore, JBL) werden namentlich auf den Tasten angezeigt. Automatischer Reconnect beim Einschalten.
* 🔄 **Musik- & Audio-Reset**: Schneller Track-Reset auf `0:00` direkt per Long-Press auf die Tag-/Nacht-Taste oder im System-Menü.
* 🔊 **Deutsche Sprachausgabe (TTS)**: Angenehme Audio-Ansagen für Akkustand/Verbindung, Lautstärke, Timer-Status und IP-Adresse.
* 🌙 **Dimmbare Tastenbeleuchtung**: Helligkeitsstufen (100% / 50% / 15%) im geschützten Menü.
* 🛡️ **Sicherer Betrieb & SD-Schutz**: Geschütztes System-Menü gegen Fehlklicks im Spiel, 2-Klick-Sicherheits-Shutdown zum Schutz des Dateisystems.

---

## Tasten-Layout

### 1. Hauptseite (Während des Spiels)
```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  [0] Nacht   │   [1] Tag    │  [2] Pause   │  [3] Leiser  │  [4] Lauter  │
│  (Mond-Icon) │  (Sonne)     │  / Weiter    │    (-5%)     │    (+5%)     │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│  [5] 10 Min  │  [6] 8 Min   │  [7] 5 Min   │  [8] 3 Min   │  [9] Stop    │
│  (Live MM:SS)│  (Live MM:SS)│  (Live MM:SS)│  (Live MM:SS)│  (Glocke)    │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ [10] Glocke  │ [11] -30s    │ [12] +30s    │ [13] Status  │ [14] System  │
│ (Manuell)    │ (Timer -30s) │ (+1m Lang)   │  (Ansage)    │  (Menü)      │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

* **Long-Press auf `Tag`**: Setzt Tag-Position auf `0:00` zurück.
* **Long-Press auf `Nacht`**: Setzt Nacht-Position auf `0:00` zurück.
* **Long-Press auf `Stop`**: Setzt beide Tracks komplett auf `0:00` zurück.

### 2. System-Menü (Taste [14])
```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  [0] Zurück  │ [1] Bluetooth│  [2] Licht   │   [3] WLAN   │  [4] Sprache │
│  (Hauptseite)│ (Koppeln/Scan│ (100/50/15%) │  (Ein/Aus)   │ (Stumm/Aktiv)│
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ [5] Musik    │  [6] Audio   │ [7] IP-Adr.  │  [8] App Neu │ [9] Power Off│
│ (Reset 0:00) │  (Neustart)  │   (Ansage)   │  (Neustart)  │ (2x drücken) │
├──────────────┴──────────────┴──────────────┴──────────────┴──────────────┤
│                             [10-14] Frei                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Hardware-Anforderungen

1. **Raspberry Pi** (Empfohlen: Pi 3B+, 4B oder Pi Zero 2 W mit 64-bit Raspberry Pi OS Lite).
2. **Elgato Stream Deck** (15 Tasten, z. B. MK.2).
3. **Bluetooth-Lautsprecher** (z. B. Anker SoundCore 2, JBL Flip, etc.).
4. **Stromversorgung** (USB-Netzteil oder Powerbank für mobilen Einsatz am Spieletisch).

---

## Audio-Dateien (Wichtig!)

Aus rechtlichen Gründen werden in diesem Repository **keine urheberrechtlich geschützten Musik- oder Sounddateien mitgeliefert**.

Lege vor dem ersten Start drei Audiodateien im Ordner `music/` ab:
* `music/day.mp3`: Ruhige Hintergrundmusik für die Tag-Phase (wird automatisch geloopt).
* `music/night.mp3`: Düstere, spannende Hintergrundmusik für die Nacht-Phase (wird automatisch geloopt).
* `music/bell.mp3`: Kräftiger Glockenschlag oder Gong für Timer-Ablauf & Signal.

*(Weitere Details und Bezugsquellen für freie Musik findest du in [music/README.md](music/README.md)).*

---

## Installation & Einrichtung

Eine ausführliche Schritt-für-Schritt-Anleitung (von der SD-Karte bis zum Autostart) findest du in:  
👉 **[INSTALL.de.md](INSTALL.de.md)** *(English guide: [INSTALL.md](INSTALL.md))*

### Kurzüberblick:

1. **Repository klonen**:
   ```bash
   git clone https://github.com/sebastianreinig/botc_streamdeck.git
   cd botc_streamdeck
   ```
2. **Audio-Dateien einfügen**: Kopiere deine `day.mp3`, `night.mp3` und `bell.mp3` in den Ordner `music/`.
3. **Automatische Installation auf dem Pi**:
   ```bash
   ./deploy/install.sh
   ```
4. **Pi neu starten**:
   ```bash
   sudo reboot
   ```
Der Dienst `botc-deck.service` startet ab sofort automatisch im Hintergrund bei jedem Booten.

---

## Rechtliche Hinweise / Disclaimer

* **Inoffizielles Fan-Projekt**: Dieses Projekt ist ein unabhängiges, nicht-kommerzielles Fan-Tool und steht in **keinerlei** offizieller Verbindung zu Steven Medway oder *The Pandemonium Institute*.
* **Markenrecht**: *"Blood on the Clocktower"* ist eine eingetragene Marke von Steven Medway und *The Pandemonium Institute*. Alle Rechte an Spielkonzepten, Markennamen und offiziellen Inhalten verbleiben bei den jeweiligen Inhabern.
* **Open Source Lizenz**: Der Quellcode dieses Projekts steht unter der [MIT License](LICENSE).
* **Entwicklung mit KI-Unterstützung**: Dieses Projekt wurde mit Unterstützung von **Gemini 3.8 Flash** realisiert.

