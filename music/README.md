# Audio-Dateien / Audio Files

Dieses Verzeichnis enthält die Audiodateien für den Blood on the Clocktower Stream Deck Controller.

> **Wichtiger rechtlicher Hinweis / Legal Note:**  
> Aus Urheberrechtsgründen werden in diesem Repository **keine** urheberrechtlich geschützten Musik- oder Sounddateien mitgeliefert.  
> *Due to copyright laws, this repository does NOT bundle copyrighted audio or music tracks.*

---

## Benötigte Dateien / Required Files

Platziere deine eigenen Audiodateien direkt in diesem Ordner (`music/`):

| Dateiname | Format | Funktion | Beschreibung |
|---|---|---|---|
| `day.mp3` | MP3 / WAV | Tag-Phase | Ruhige, stimmungsvolle Hintergrundmusik für Tag-Diskussionen (wird automatisch endlos geloopt). |
| `night.mp3` | MP3 / WAV | Nacht-Phase | Düstere, geheimnisvolle Hintergrundmusik für die Nacht (wird automatisch endlos geloopt). |
| `bell.mp3` | MP3 / WAV | Glocke / Signal | Kräftiger Glockenschlag, Gong oder Chime (wird bei Ablauf von Timern oder manuellem Glocken-Klick gespielt). |

---

## Woher bekomme ich passende Musik? / Sourcing Audio

Für private Spielrunden kannst du lizenzfreie oder CC0-Musik nutzen, zum Beispiel von:
* **[Incompetech (Kevin MacLeod)](https://incompetech.com/)**: Viele atmosphärische Mystery- & Fantasy-Tracks (CC-BY).
* **[Pixabay Music](https://pixabay.com/music/)**: Große Auswahl an lizenzfreien Ambient- und Dark-Fantasy-Tracks.
* **[Freesound.org](https://freesound.org/)**: Hunderte historische Kirchenglocken, Chimes und Gongs (CC0 / gemeinfrei).
* **Eigene Soundtracks**: Gekaufte Soundtracks oder offizielle BotC-Atmosphäre-Tracks für die private Nutzung.

---

## Pfade & Konfiguration

Standardmäßig sucht die Anwendung in `config.yaml` nach:
```yaml
paths:
  day_track: "music/day.mp3"
  night_track: "music/night.mp3"
  bell_sound: "music/bell.mp3"
```
Die Dateinamen können bei Bedarf in `config.yaml` angepasst werden.
