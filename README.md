


# Last.FM Charts

# Last.fm Charts Auswertung

Dieses Dokument bietet eine Anleitung zur Installation und Nutzung der Anwendung **"Last.fm Charts Auswertung"**. Die Anwendung ermöglicht es, persönliche Musikcharts basierend auf Ihren Last.fm-Daten zu erstellen und in einer grafischen Benutzeroberfläche anzuzeigen.

## Inhaltsverzeichnis

1. [Einführung](#einführung)
2. [Funktionen](#funktionen)
3. [Voraussetzungen](#voraussetzungen)
4. [Installation](#installation)
5. [Konfiguration](#konfiguration)
6. [Anwendung starten](#anwendung-starten)
7. [Bedienung](#bedienung)
8. [Häufig gestellte Fragen (FAQ)](#häufig-gestellte-fragen-faq)
9. [Lizenz](#lizenz)

## Einführung

Die **"Last.fm Charts Auswertung"** ist eine Python-Anwendung, die Daten von Last.fm abruft und daraus Wochen-, Monats- und Jahrescharts generiert. Die Ergebnisse werden in einer grafischen Oberfläche dargestellt, die es ermöglicht, durch verschiedene Zeiträume zu navigieren und die Charts für verschiedene Benutzer anzuzeigen.

## Funktionen

- **Wochencharts**: Anzeige der Top 20 Songs einer bestimmten Woche.
- **Monatscharts**: Anzeige der Top 30 Songs eines bestimmten Monats.
- **Jahrescharts**: Anzeige der Top 50 Songs eines bestimmten Jahres.
- **Benutzerauswahl**: Unterstützung für mehrere Last.fm-Benutzer.
- **Navigation**: Vor- und Zurückblättern zwischen den Zeiträumen.
- **Cache**: Zwischenspeicherung der abgerufenen Daten zur Verbesserung der Leistung.
- **Benutzerfreundliche GUI**: Einfache Bedienung durch eine grafische Benutzeroberfläche mit Eingabefeldern und Schaltflächen.

## Voraussetzungen

Stellen Sie sicher, dass die folgenden Voraussetzungen erfüllt sind:

- **Python 3.6 oder höher** ist installiert.
- Die folgenden Python-Bibliotheken sind installiert:
  - `tkinter` (normalerweise in der Standardbibliothek enthalten)
  - `pandas`
  - `requests`

## Installation

### 1. Python installieren

Falls Python noch nicht installiert ist, können Sie es von der offiziellen Website herunterladen und installieren:

[Python Download](https://www.python.org/downloads/)

### 2. Benötigte Bibliotheken installieren

Öffnen Sie ein Terminal oder eine Eingabeaufforderung und führen Sie die folgenden Befehle aus, um die erforderlichen Bibliotheken zu installieren:

```bash
pip install pandas requests
```

**Hinweis:** `tkinter` ist normalerweise in der Standardinstallation von Python enthalten. Falls nicht, installieren Sie es entsprechend Ihrer Betriebssystemumgebung.

- **Für Ubuntu/Debian**:

  ```bash
  sudo apt-get install python3-tk
  ```

- **Für macOS**:

  `tkinter` sollte bereits mit Python installiert sein. Falls nicht, installieren Sie Python über [Homebrew](https://brew.sh/):

  ```bash
  brew install python3
  ```

## Konfiguration

### 1. API-Schlüssel erstellen

Um die Last.fm API nutzen zu können, benötigen Sie einen API-Schlüssel:

1. Erstellen Sie ein Konto auf [Last.fm](https://www.last.fm/) (falls nicht bereits vorhanden).
2. Gehen Sie zu [Last.fm API-Anmeldung](https://www.last.fm/api/account/create) und erstellen Sie eine neue Anwendung.
3. Notieren Sie sich den bereitgestellten API-Schlüssel.

### 2. `keys.json` Datei erstellen

Erstellen Sie im selben Verzeichnis wie die Anwendung eine Datei namens `keys.json` mit folgendem Inhalt:

```json
[
  {
    "LASTFM_USER": "IhrBenutzername",
    "LASTFM_API_KEY": "IhrAPIKey"
  }
]
```

Ersetzen Sie `"IhrBenutzername"` durch Ihren Last.fm-Benutzernamen und `"IhrAPIKey"` durch Ihren API-Schlüssel.

**Unterstützung mehrerer Benutzer:**

Sie können mehrere Benutzer hinzufügen, indem Sie weitere Objekte zum Array hinzufügen:

```json
[
  {
    "LASTFM_USER": "Benutzer1",
    "LASTFM_API_KEY": "APIKey1"
  },
  {
    "LASTFM_USER": "Benutzer2",
    "LASTFM_API_KEY": "APIKey2"
  }
]
```

### 3. Schriftarten (optional)

Die Anwendung verwendet standardmäßig die Schriftart **"Ubuntu Mono"**. Stellen Sie sicher, dass diese Schriftart auf Ihrem System installiert ist, oder ändern Sie die Schriftart im Code in eine auf Ihrem System verfügbare Schriftart.

- **Schriftart ändern:**

  Öffnen Sie die Anwendungscode-Datei (`lastfm_charts.py`) in einem Texteditor und suchen Sie nach:

  ```python
  FONT_FAMILY = "Ubuntu Mono"
  ```

  Ersetzen Sie `"Ubuntu Mono"` durch den Namen der Schriftart, die Sie verwenden möchten.

### 4. last.fm API

Die App verwendet die last.fm API mit Stand vom 22. 09.2024.




## Anwendung starten

1. Speichern Sie den Anwendungscode in einer Datei, z.B. `lastfm_charts.py`.
2. Stellen Sie sicher, dass sich die Datei `keys.json` im selben Verzeichnis befindet.
3. Öffnen Sie ein Terminal oder eine Eingabeaufforderung und navigieren Sie in das Verzeichnis der Anwendung.
4. Starten Sie die Anwendung mit dem folgenden Befehl:

```bash
python lastfm_charts.py
```

## Bedienung

Nach dem Start der Anwendung erscheint ein Fenster mit folgenden Elementen:

- **Benutzerauswahl**: Wählen Sie den Last.fm-Benutzer aus, für den die Charts angezeigt werden sollen.
- **Eingabefelder**: Jahr, Monat und Woche können eingegeben werden.
  - **Enter-Taste**: Durch Drücken der Enter-Taste in einem der Eingabefelder wird die entsprechende Chartansicht geladen.
- **Schaltflächen**:
  - **Jahrescharts**: Zeigt die Jahrescharts für das eingegebene Jahr an.
  - **Monatscharts**: Zeigt die Monatscharts für das eingegebene Jahr und den Monat an.
  - **Wochencharts**: Zeigt die Wochencharts für das eingegebene Jahr und die Woche an.
  - **Zurück / Weiter**: Ermöglichen das Navigieren zum vorherigen oder nächsten Zeitraum basierend auf der zuletzt angezeigten Chartansicht.
  - **Reset**: Setzt die Eingabefelder auf die aktuellen Werte zurück.
  - **Cache löschen**: Löscht den zwischengespeicherten Daten-Cache.
- **Charts-Anzeige**: Die Ergebnisse werden in einer scrollbaren Liste angezeigt.

### Hinweise zur Bedienung

- **Synchronisierung der Eingabefelder**: Beim Anzeigen der Charts werden die Eingabefelder für Jahr, Monat und Woche entsprechend aktualisiert.
- **Limitierung der Ergebnisse**:
  - Wochencharts: Top 20 Songs
  - Monatscharts: Top 30 Songs
  - Jahrescharts: Top 50 Songs
- **Statusmeldungen**: Während des Ladens der Daten und der Berechnungen werden Statusmeldungen in der Überschrift angezeigt.

## Häufig gestellte Fragen (FAQ)

### Warum erhalte ich eine Fehlermeldung beim Starten der Anwendung?

- **Fehlende Bibliotheken**: Stellen Sie sicher, dass alle erforderlichen Bibliotheken (`pandas`, `requests`, `tkinter`) installiert sind.
- **Fehlende `keys.json` Datei**: Die Anwendung benötigt die `keys.json` Datei mit Ihren Last.fm-Benutzernamen und API-Schlüsseln.

### Die Charts werden nicht angezeigt oder sind leer.

- **Keine Daten vorhanden**: Überprüfen Sie, ob für den ausgewählten Zeitraum Daten auf Ihrem Last.fm-Konto vorhanden sind.
- **Falsche Eingaben**: Stellen Sie sicher, dass die Eingaben für Jahr, Monat und Woche gültige Zahlen sind.

### Wie kann ich die Schriftart oder Schriftgröße ändern?

- Öffnen Sie die Anwendungscode-Datei (`lastfm_charts.py`) in einem Texteditor.
- Suchen Sie nach den Zeilen:

  ```python
  FONT_FAMILY = "Ubuntu Mono"
  FONT_SIZE_LISTBOX = 16
  FONT_SIZE_LABEL = 20
  ```

- Passen Sie die Werte nach Ihren Wünschen an.
- Speichern Sie die Datei und starten Sie die Anwendung neu.

### Wie kann ich den Cache löschen?

- Klicken Sie in der Anwendung auf die Schaltfläche **"Cache löschen"**. Dies entfernt den zwischengespeicherten Daten-Cache und erzwingt beim nächsten Abruf das Laden der neuesten Daten von Last.fm.

### Kann ich die Anwendung mit mehreren Benutzern verwenden?

- Ja, Sie können mehrere Benutzer in der `keys.json` Datei hinzufügen. Verwenden Sie dazu das im Abschnitt [Konfiguration](#konfiguration) beschriebene Format.

## Lizenz

Diese Anwendung ist unter der **MIT-Lizenz** lizenziert. Sie können den Quellcode frei verwenden, modifizieren und verbreiten.

---

**Hinweis:** Stellen Sie sicher, dass Sie die Last.fm API-Richtlinien einhalten und Ihre API-Schlüssel sicher aufbewahren. Teilen Sie Ihre API-Schlüssel nicht öffentlich.

---

Bei weiteren Fragen oder Problemen wenden Sie sich bitte an den Entwickler oder konsultieren Sie die [Last.fm API-Dokumentation](https://www.last.fm/api).
