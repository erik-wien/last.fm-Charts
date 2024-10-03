import sys
import os
import json
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
import pandas as pd
from collections import Counter
import calendar
import requests
import time
import pickle  # Zum Speichern des Caches
import datetime  # Für die Berechnung der Wochen in einem Jahr

# ---------------------------- Konfiguration und Konstante ----------------------------
DEBUG_MODE = True  # Setze auf True, um Debug-Ausgaben zu aktivieren

# Schriftarten definieren
FONT_FAMILY = "Ubuntu Mono"
FONT_SIZE_TEXT = 16
FONT_SIZE_LABEL = 20

# API-Parameter
BASE_URL = 'http://ws.audioscrobbler.com/2.0/'
API_KEY = None  # Wird in der Initialisierung gesetzt
current_user = None  # Aktueller Benutzer (wird gesetzt)

# ---------------------------- Cache und Benutzerkonfiguration ----------------------------
# Globale Variablen für den Daten-Cache und die Benutzer
data_cache = {}
users = []
last_chart_type = None

# ---------------------------- Globale Variablen für die GUI ----------------------------
newest_date = None
last_year = None
last_month = None
last_week = None


# Funktion zum Laden der Benutzer und API-Schlüssel aus keys.json
def load_users():
    global users
    try:
        with open('keys.json', 'r') as f:
            users_data = json.load(f)
            users = users_data
    except Exception as e:
        print(f"Fehler beim Laden der Benutzer aus keys.json: {e}")
        sys.exit(1)

# Benutzer laden
load_users()

# Überprüfen, ob Benutzer vorhanden sind
if not users:
    print("Keine Benutzer in keys.json gefunden.")
    sys.exit(1)

# Initialisierung von API_KEY und USER mit Standardwerten
API_KEY = users[0]['LASTFM_API_KEY']
USER = users[0]['LASTFM_USER']
BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Globale Variable für den aktuell ausgewählten Benutzer
current_user = USER

# Globale Variable für die letzte Auswahl (week, month, year)
last_chart_type = None

# Funktion zum Abrufen der Daten von der Last.fm API für einen bestimmten Zeitraum
def fetch_lastfm_data(from_timestamp, to_timestamp):
    all_tracks = []
    page = 1
    total_pages = 1  # Initialisierung mit 1, wird später aktualisiert

    # Update the chart_label to show "Daten werden von Last.fm geladen..."
    chart_label.config(text="Daten werden von Last.fm geladen...")
    chart_label.update_idletasks()

    while page <= total_pages:
        try:
            params = {
                'method': 'user.getrecenttracks',
                'user': current_user,
                'api_key': API_KEY,
                'format': 'json',
                'from': from_timestamp,
                'to': to_timestamp,
                'limit': 200,  # Maximale Anzahl pro Seite
                'page': page,
            }
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()  # HTTP-Fehler auslösen, falls vorhanden
            data = response.json()

            if 'error' in data:
                print(f"API-Fehler: {data['message']}")
                break

            recent_tracks = data.get('recenttracks', {}).get('track', [])
            total_pages = int(data.get('recenttracks', {}).get('@attr', {}).get('totalPages', 1))

            for track in recent_tracks:
                # Überspringe den aktuell gespielten Track (nowplaying)
                if '@attr' in track and track['@attr'].get('nowplaying') == 'true':
                    continue

                artist = track.get('artist', {}).get('#text', '').strip()
                album = track.get('album', {}).get('#text', '').strip()
                song_title = track.get('name', '').strip()
                date_uts = track.get('date', {}).get('uts', None)

                if date_uts is None:
                    continue  # Wenn kein Datum vorhanden ist, überspringe den Eintrag

                date_time = pd.to_datetime(int(date_uts), unit='s')

                all_tracks.append({
                    'artist': artist,
                    'album': album,
                    'song_title': song_title,
                    'date_time': date_time,
                })

            if DEBUG_MODE:
                print(f"Seite {page} von {total_pages} abgerufen für Benutzer {current_user}.")

            page += 1
            time.sleep(0.2)  # Kleine Pause, um die API nicht zu überlasten

        except requests.exceptions.RequestException as e:
            print(f"Netzwerkfehler: {e}")
            break
        except Exception as e:
            print(f"Fehler beim Abrufen der Daten: {e}")
            break

    return pd.DataFrame(all_tracks)

# Funktion zur Vorbereitung der Daten
def prepare_data(df):
    # Entferne potenzielle führende und nachfolgende Leerzeichen
    df['song_title'] = df['song_title'].str.strip()
    df['artist'] = df['artist'].str.strip()
    df['album'] = df['album'].str.strip()

    # Datumskomponenten hinzufügen
    iso_calendar = df['date_time'].dt.isocalendar()
    df['iso_year'] = iso_calendar.year
    df['iso_week'] = iso_calendar.week
    df['year'] = df['date_time'].dt.year
    df['month'] = df['date_time'].dt.month

    return df

# Funktion zum Laden der Daten für einen bestimmten Zeitraum
def load_data_for_period(period_type, year, month=None, week=None):
    global data_cache

    # Erzeuge einen eindeutigen Schlüssel für den Cache basierend auf dem Zeitraum und dem Benutzer
    if period_type == 'year':
        cache_key = f'{current_user}_year_{year}'
    elif period_type == 'month':
        cache_key = f'{current_user}_month_{year}_{month}'
    elif period_type == 'week':
        cache_key = f'{current_user}_week_{year}_{week}'
    else:
        print("Ungültiger Zeitraumtyp.")
        return pd.DataFrame()

    # Überprüfe, ob die Daten bereits im Cache sind
    if cache_key in data_cache:
        if DEBUG_MODE:
            print(f"Daten für {cache_key} aus dem Cache geladen.")
        return data_cache[cache_key]

    # Andernfalls Daten von der API abrufen
    if DEBUG_MODE:
        print(f"Daten für {cache_key} werden von der API abgerufen.")

    # Bestimme die Zeitstempel für den Zeitraum
    if period_type == 'year':
        from_timestamp = int(pd.Timestamp(year=year, month=1, day=1).timestamp())
        to_timestamp = int(pd.Timestamp(year=year + 1, month=1, day=1).timestamp()) - 1
    elif period_type == 'month':
        from_timestamp = int(pd.Timestamp(year=year, month=month, day=1).timestamp())
        if month == 12:
            to_timestamp = int(pd.Timestamp(year=year + 1, month=1, day=1).timestamp()) - 1
        else:
            to_timestamp = int(pd.Timestamp(year=year, month=month + 1, day=1).timestamp()) - 1
    elif period_type == 'week':
        # Wir nehmen an, dass die Woche beginnt am Montag
        from_date = pd.Timestamp.fromisocalendar(year, week, 1)
        to_date = from_date + pd.Timedelta(days=6, hours=23, minutes=59, seconds=59)
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())
    else:
        print("Ungültiger Zeitraumtyp.")
        return pd.DataFrame()

    # Daten abrufen
    df = fetch_lastfm_data(from_timestamp, to_timestamp)
    if df.empty:
        if DEBUG_MODE:
            print(f"Keine Daten für {cache_key} abgerufen.")
        return df

    df = prepare_data(df)

    # Daten im Cache speichern
    data_cache[cache_key] = df

    # Cache speichern
    save_cache()

    return df

# Funktion zum Speichern des Caches auf die Festplatte
def save_cache():
    try:
        with open('data_cache.pkl', 'wb') as f:
            pickle.dump(data_cache, f)
    except Exception as e:
        print(f"Fehler beim Speichern des Caches: {e}")

# Funktion zum Laden des Caches von der Festplatte
def load_cache():
    global data_cache
    if os.path.exists('data_cache.pkl'):
        try:
            with open('data_cache.pkl', 'rb') as f:
                data_cache = pickle.load(f)
            if DEBUG_MODE:
                print("Cache geladen.")
        except Exception as e:
            print(f"Fehler beim Laden des Caches: {e}")
            data_cache = {}
    else:
        data_cache = {}

# Funktion zum Löschen des Caches
def clear_cache():
    global data_cache
    data_cache = {}
    if os.path.exists('data_cache.pkl'):
        try:
            os.remove('data_cache.pkl')
            print("Cache erfolgreich gelöscht.")
        except Exception as e:
            print(f"Fehler beim Löschen des Caches: {e}")
    else:
        print("Kein Cache vorhanden.")
    # Aktualisiere die Anzeige
    chart_label.config(text="Charts")
    chart_text.delete('1.0', tk.END)

# Vor dem Start der Anwendung den Cache laden
load_cache()

# Funktion zur Berechnung der Wochencharts
def calculate_weekly_charts(df, year, week):
    try:
        week_data = df[(df['iso_year'] == year) & (df['iso_week'] == week)]

        if week_data.empty:
            if DEBUG_MODE:
                print(f"Keine Songs für Woche {week} im Jahr {year} gefunden.")
            return {}, pd.Series(dtype=int), pd.DataFrame()

        # Zähle die Vorkommen jeder song_title/artist-Kombination
        counts = week_data.groupby(['song_title', 'artist']).size()

        # Hole das erste Vorkommen jeder song_title/artist-Kombination, um das Album zu erhalten
        first_occurrences = week_data.drop_duplicates(subset=['song_title', 'artist'], keep='first')

        # Füge die Zählungen zum DataFrame hinzu
        top_songs_df = first_occurrences.set_index(['song_title', 'artist'])
        top_songs_df['play_count'] = counts

        # Sortiere nach Häufigkeit
        top_songs_df = top_songs_df.sort_values(by='play_count', ascending=False)

        # Begrenze auf die Top 20 Songs
        top_songs_df = top_songs_df.head(20)

        # Vergabe der Punkte (Platz 1 = 20 Punkte, Platz 2 = 19 usw.)
        points = {song: 20 - i for i, song in enumerate(top_songs_df.index)}

        # Füge die Punkte zum DataFrame hinzu
        top_songs_df['points'] = top_songs_df.index.map(points)

        # Rückgabe: Punkte, Wiedergabeanzahl und Top-Songs DataFrame
        return points, counts, top_songs_df

    except Exception as e:
        print(f"Fehler in calculate_weekly_charts: {e}")
        return {}, pd.Series(dtype=int), pd.DataFrame()

# Funktion zur Berechnung der Monatscharts
def calculate_monthly_charts(df, year, month):
    try:
        month_data = df[(df['year'] == year) & (df['month'] == month)]

        if month_data.empty:
            if DEBUG_MODE:
                print(f"Keine Songs für Monat {month} im Jahr {year} gefunden.")
            return {}, {}, pd.DataFrame()

        # Alle Wochen des Monats ermitteln
        weeks_in_month = month_data['iso_week'].unique()
        weekly_points = Counter()
        weekly_plays = Counter()

        # Berechnung der Wochencharts für jede Woche des Monats
        for week in weeks_in_month:
            points, plays, _ = calculate_weekly_charts(month_data, year, week)
            for song, points_count in points.items():
                weekly_points[song] += points_count
                weekly_plays[song] += plays.get(song, 0)

        if not weekly_points:
            if DEBUG_MODE:
                print(f"Keine Songs für Monat {month} im Jahr {year} gefunden.")
            return {}, {}, pd.DataFrame()

        # Erstelle DataFrame für die Songs
        chart_data = pd.DataFrame({
            'points': pd.Series(weekly_points),
            'play_count': pd.Series(weekly_plays),
        })

        # Setze die Indexnamen
        chart_data.index.names = ['song_title', 'artist']

        # Hole Song-Informationen
        first_occurrences = month_data.drop_duplicates(subset=['song_title', 'artist'], keep='first')
        song_info = first_occurrences.set_index(['song_title', 'artist'])
        song_info = song_info[['album']]

        # Zusammenführen mit Song-Informationen
        chart_data = chart_data.merge(song_info, left_index=True, right_index=True)

        # Sortiere nach Punkten und Wiedergabeanzahl
        chart_data = chart_data.sort_values(by=['points', 'play_count'], ascending=[False, False])

        # Begrenze auf die Top 30 Songs
        chart_data = chart_data.head(30)

        # Konvertiere Punkte und Wiedergabeanzahl zu Dictionaries
        points = chart_data['points'].to_dict()
        plays = chart_data['play_count'].to_dict()

        return points, plays, chart_data

    except Exception as e:
        print(f"Fehler in calculate_monthly_charts: {e}")
        return {}, {}, pd.DataFrame()

# Funktion zur Berechnung der Jahrescharts
def calculate_yearly_charts(df, year):
    try:
        year_data = df[df['year'] == year]

        if year_data.empty:
            if DEBUG_MODE:
                print(f"Keine Songs für Jahr {year} gefunden.")
            return {}, {}, pd.DataFrame()

        # Alle Monate des Jahres ermitteln
        months_in_year = year_data['month'].unique()
        monthly_points = Counter()
        monthly_plays = Counter()

        # Berechnung der Monatscharts für jeden Monat des Jahres
        for month in months_in_year:
            points, plays, _ = calculate_monthly_charts(year_data, year, month)
            for song, points_count in points.items():
                monthly_points[song] += points_count
                monthly_plays[song] += plays.get(song, 0)

        if not monthly_points:
            if DEBUG_MODE:
                print(f"Keine Songs für Jahr {year} gefunden.")
            return {}, {}, pd.DataFrame()

        # Erstelle DataFrame für die Songs
        chart_data = pd.DataFrame({
            'points': pd.Series(monthly_points),
            'play_count': pd.Series(monthly_plays),
        })

        # Setze die Indexnamen
        chart_data.index.names = ['song_title', 'artist']

        # Hole Song-Informationen
        first_occurrences = year_data.drop_duplicates(subset=['song_title', 'artist'], keep='first')
        song_info = first_occurrences.set_index(['song_title', 'artist'])
        song_info = song_info[['album']]

        # Zusammenführen mit Song-Informationen
        chart_data = chart_data.merge(song_info, left_index=True, right_index=True)

        # Sortiere nach Punkten und Wiedergabeanzahl
        chart_data = chart_data.sort_values(by=['points', 'play_count'], ascending=[False, False])

        # Begrenze auf die Top 50 Songs
        chart_data = chart_data.head(50)

        # Konvertiere Punkte und Wiedergabeanzahl zu Dictionaries
        points = chart_data['points'].to_dict()
        plays = chart_data['play_count'].to_dict()

        return points, plays, chart_data

    except Exception as e:
        print(f"Fehler in calculate_yearly_charts: {e}")
        return {}, {}, pd.DataFrame()

# Funktion zum Abrufen des neuesten Datums (für die Initialisierung)
def get_latest_date():
    try:
        # Abrufen des aktuellsten Tracks
        params = {
            'method': 'user.getrecenttracks',
            'user': current_user,
            'api_key': API_KEY,
            'format': 'json',
            'limit': 1,
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        recent_tracks = data.get('recenttracks', {}).get('track', [])
        if not recent_tracks:
            print("Keine aktuellen Daten verfügbar.")
            sys.exit(1)

        track = recent_tracks[0]
        date_uts = track.get('date', {}).get('uts', None)
        if date_uts is None:
            print("Keine Datumseinträge gefunden.")
            sys.exit(1)

        date_time = pd.to_datetime(int(date_uts), unit='s')
        return date_time

    except Exception as e:
        print(f"Fehler beim Abrufen des neuesten Datums: {e}")
        sys.exit(1)

# Funktion zur Aktualisierung des aktuell ausgewählten Benutzers
def update_current_user(event):
    global current_user, API_KEY
    selected_user = user_combo.get()
    for user in users:
        if user['LASTFM_USER'] == selected_user:
            current_user = user['LASTFM_USER']
            API_KEY = user['LASTFM_API_KEY']
            break
    print(f"Aktueller Benutzer: {current_user}")
    initialize()

# Funktion zur Formatierung von Werten
def format_value(value):
    if pd.isna(value):
        return ''
    else:
        return f"{int(value)}"

# Funktion zur Berechnung der Anzahl der Wochen in einem Jahr
def get_weeks_in_year(year):
    last_week = datetime.date(year, 12, 28).isocalendar()[1]
    return last_week

# Initialisierung der GUI mit den neuesten Daten
newest_date = None
def initialize():
    global newest_date, last_year, last_month, last_week
    newest_date = get_latest_date()
    last_year = newest_date.year
    last_month = newest_date.month
    last_week = newest_date.isocalendar().week
    reset_input()

# Funktion zur Anzeige der aktuellen Eingabefelder
def reset_input():
    year_entry.delete(0, tk.END)
    year_entry.insert(0, last_year)  # Trage das letzte Jahr ein
    month_entry.delete(0, tk.END)
    month_entry.insert(0, last_month)  # Trage das letzte Monat ein
    week_entry.delete(0, tk.END)
    week_entry.insert(0, last_week)  # Trage die letzte Woche ein

# Funktion zur Formatierung der Dauer
def format_duration(duration_ms):
    try:
        duration_ms = int(duration_ms)
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        return f"{minutes}:{seconds:02d}"
    except ValueError:
        return "Unbekannt"

# GUI erstellen
# ---------------------------------------------
root = tk.Tk()
root.title("Last.fm Charts Auswertung")

# Layout-Konfiguration
root.grid_columnconfigure(5, weight=20)

root.grid_rowconfigure(0, weight=2)  # Bildschirmrand
root.grid_rowconfigure(13, weight=1)  # Listenüberschrift 
root.grid_rowconfigure(14, weight=20)  # Liste
root.grid_rowconfigure(15, weight=1)  # Bildschirmrand

# Schriftarten definieren
text_font = tkFont.Font(family=FONT_FAMILY, size=FONT_SIZE_TEXT)
label_font = (FONT_FAMILY, FONT_SIZE_LABEL, "bold")  # Schriftart für Labels

# Stil für Labels erstellen
style = ttk.Style()
style.configure("ChartLabel.TLabel", font=label_font)

# Chart Label erstellen und platzieren
chart_label = ttk.Label(root, text="Last.FM Charts", style="ChartLabel.TLabel")
chart_label.grid(row=1, column=1, columnspan=5, sticky="w", pady=(10, 5), padx=(10,5))

# Benutzer-Auswahl
ttk.Label(root, text="Benutzer:").grid(row=2, column=1, sticky="e", padx=(10,0))
user_combo = ttk.Combobox(root, values=[user['LASTFM_USER'] for user in users])
user_combo.current(0)  # Standardmäßig den ersten Benutzer auswählen
user_combo.grid(row=2, column=2, sticky="w")
user_combo.bind("<<ComboboxSelected>>", update_current_user)

# Jahr, Monat und Woche Eingabefelder
ttk.Label(root, text="Jahr:").grid(row=3, column=1, sticky="e", padx=(10,0))
year_entry = ttk.Entry(root)
year_entry.grid(row=3, column=2, sticky="w")

ttk.Label(root, text="Monat:").grid(row=4, column=1, sticky="e", padx=(10,0))
month_entry = ttk.Entry(root)
month_entry.grid(row=4, column=2, sticky="w")

ttk.Label(root, text="Woche:").grid(row=5, column=1, sticky="e", padx=(10,0))
week_entry = ttk.Entry(root)
week_entry.grid(row=5, column=2, sticky="w")

# Funktionen, die bei Drücken der Enter-Taste aufgerufen werden
def on_year_entry(event):
    try:
        year = int(year_entry.get())
        display_yearly_charts(year)
    except ValueError:
        chart_label.config(text="Bitte geben Sie eine gültige Zahl für das Jahr ein.")

def on_month_entry(event):
    try:
        year = int(year_entry.get())
        month = int(month_entry.get())
        display_monthly_charts(year, month)
    except ValueError:
        chart_label.config(text="Bitte geben Sie gültige Zahlen für Jahr und Monat ein.")

def on_week_entry(event):
    try:
        year = int(year_entry.get())
        week = int(week_entry.get())
        display_weekly_charts(year, week)
    except ValueError:
        chart_label.config(text="Bitte geben Sie gültige Zahlen für Jahr und Woche ein.")

# Bindings für die Enter-Taste
year_entry.bind('<Return>', on_year_entry)
month_entry.bind('<Return>', on_month_entry)
week_entry.bind('<Return>', on_week_entry)

# Funktionen für "Zurück" und "Weiter"
def go_back():
    try:
        if last_chart_type == 'week':
            week = int(week_entry.get())
            year = int(year_entry.get())
            week -= 1
            if week < 1:
                year -= 1
                week = get_weeks_in_year(year)
            week_entry.delete(0, tk.END)
            week_entry.insert(0, week)
            year_entry.delete(0, tk.END)
            year_entry.insert(0, year)
            # Aktualisiere den Monat basierend auf der neuen Woche
            first_day_of_week = datetime.date.fromisocalendar(year, week, 1)
            month = first_day_of_week.month
            month_entry.delete(0, tk.END)
            month_entry.insert(0, month)
            display_weekly_charts(year, week)
        elif last_chart_type == 'month':
            month = int(month_entry.get())
            year = int(year_entry.get())
            month -= 1
            if month < 1:
                month = 12
                year -= 1
            month_entry.delete(0, tk.END)
            month_entry.insert(0, month)
            year_entry.delete(0, tk.END)
            year_entry.insert(0, year)
            # Setze die Woche auf die erste Woche des Monats
            first_day_of_month = datetime.date(year, month, 1)
            week = first_day_of_month.isocalendar()[1]
            week_entry.delete(0, tk.END)
            week_entry.insert(0, week)
            display_monthly_charts(year, month)
        elif last_chart_type == 'year':
            year = int(year_entry.get())
            year -= 1
            year_entry.delete(0, tk.END)
            year_entry.insert(0, year)
            display_yearly_charts(year)
        else:
            print("Keine vorherige Auswahl vorhanden.")
    except Exception as e:
        print(f"Fehler in go_back: {e}")

def go_forward():
    try:
        if last_chart_type == 'week':
            week = int(week_entry.get())
            year = int(year_entry.get())
            week += 1
            max_week = get_weeks_in_year(year)
            if week > max_week:
                week = 1
                year += 1
            week_entry.delete(0, tk.END)
            week_entry.insert(0, week)
            year_entry.delete(0, tk.END)
            year_entry.insert(0, year)
            # Aktualisiere den Monat basierend auf der neuen Woche
            first_day_of_week = datetime.date.fromisocalendar(year, week, 1)
            month = first_day_of_week.month
            month_entry.delete(0, tk.END)
            month_entry.insert(0, month)
            display_weekly_charts(year, week)
        elif last_chart_type == 'month':
            month = int(month_entry.get())
            year = int(year_entry.get())
            month += 1
            if month > 12:
                month = 1
                year += 1
            month_entry.delete(0, tk.END)
            month_entry.insert(0, month)
            year_entry.delete(0, tk.END)
            year_entry.insert(0, year)
            # Setze die Woche auf die erste Woche des Monats
            first_day_of_month = datetime.date(year, month, 1)
            week = first_day_of_month.isocalendar()[1]
            week_entry.delete(0, tk.END)
            week_entry.insert(0, week)
            display_monthly_charts(year, month)
        elif last_chart_type == 'year':
            year = int(year_entry.get())
            year += 1
            year_entry.delete(0, tk.END)
            year_entry.insert(0, year)
            display_yearly_charts(year)
        else:
            print("Keine vorherige Auswahl vorhanden.")
    except Exception as e:
        print(f"Fehler in go_forward: {e}")

# Buttons für die Charts
ttk.Button(root, text="Jahrescharts", command=lambda: display_yearly_charts(int(year_entry.get()))).grid(row=4, column=3, columnspan=2, sticky="ew")
ttk.Button(root, text="Monatscharts", command=lambda: display_monthly_charts(int(year_entry.get()), int(month_entry.get()))).grid(row=5, column=3, columnspan=2, sticky="ew")
ttk.Button(root, text="Wochencharts", command=lambda: display_weekly_charts(int(year_entry.get()), int(week_entry.get()))).grid(row=6, column=3, columnspan=2, sticky="ew")

# Schaltflächen für "Zurück" und "Weiter"
ttk.Button(root, text="Zurück", command=go_back).grid(row=7, column=3, sticky="ew")
ttk.Button(root, text="Weiter", command=go_forward).grid(row=7, column=4, sticky="ew")

# Trennline
separator = ttk.Separator(root, orient='horizontal')
separator.grid(row=9, column=3, columnspan=2, sticky="ew", pady=10)

# Buttons Formular auf Default Wert zurück setzen und Cache löschen
ttk.Button(root, text="Reset", command=reset_input).grid(row=10, column=3, sticky="ew")
ttk.Button(root, text="Cache löschen", command=clear_cache).grid(row=10, column=4, sticky="ew")

# Label zur Anzeige der Charts
chart_label = ttk.Label(root, text="Wählen Sie eine Auswertung", anchor="center", style="ChartLabel.TLabel")
chart_label.grid(row=13, column=0, columnspan=6, sticky="ew", pady=(10, 5), padx=(10,10))

# Erstelle einen Frame für das Text-Widget und den Scrollbar
text_frame = tk.Frame(root)
text_frame.grid(row=15, column=0, columnspan=6, padx=(10,10))

# Erstelle das Text-Widget
chart_text = tk.Text(text_frame, width=125, height=35, font=(FONT_FAMILY, FONT_SIZE_TEXT))
chart_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Erstelle den Scrollbar und verbinde ihn mit dem Text-Widget
scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chart_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=chart_text.yview)

# Funktion zur Anzeige der Wochencharts
def display_weekly_charts(year, week):
    global last_chart_type
    last_chart_type = 'week'

    try:
        # Eingabevalidierung
        if week < 1 or week > 53:
            print(f"Ungültige Woche: {week}. Woche muss zwischen 1 und 53 sein.")
            return

        if year < 2000 or year > newest_date.year:
            print(f"Ungültiges Jahr: {year}.")
            return

        # Statusmeldung: Daten werden geladen
        chart_label.config(text="Daten werden von Last.fm geladen...")
        chart_label.update_idletasks()

        # Daten für den Zeitraum laden
        df = load_data_for_period('week', year, week=week)

        # Statusmeldung: Berechnungen werden durchgeführt
        chart_label.config(text="Führe Berechnungen durch...")
        chart_label.update_idletasks()

        if df.empty:
            chart_label.config(text=f"Keine Daten für Woche {week}, {year}")
            chart_text.delete('1.0', tk.END)
            return

        # Berechne die Wochencharts
        points, plays, results = calculate_weekly_charts(df, year, week)

        if results.empty:
            chart_label.config(text=f"Keine Daten für Woche {week}, {year}")
            chart_text.delete('1.0', tk.END)
            return

        # Setze die Überschrift
        chart_label.config(text=f"Wochencharts - Woche {week}, {year} - {current_user}")

        # Lösche die alte Chartanzeige
        chart_text.delete('1.0', tk.END)

        # Füge die Top-Songs mit Punkten, Wiedergabeanzahl und Platzierung hinzu
        for idx, ((song_title, artist), row) in enumerate(results.iterrows(), start=1):
            album = row['album'] if 'album' in row else ''
            play_count = format_value(row['play_count'])
            point = format_value(row['points'])

            album = album if pd.notna(album) else ''

            # Text für den Song
            song_text = f"{idx:>2}. {play_count:>2}× {point:>2} Pkt: {song_title} - {artist} ({album}) "

            # Einfügen des Textes in das Text-Widget
            chart_text.insert(tk.END, song_text)

            # Füge den Link hinzu
            start_index = chart_text.index(tk.INSERT)
            chart_text.insert(tk.END, "Info\n")  # Einheitlicher Link-Text
            end_index = chart_text.index(tk.INSERT)
            tag_name = f"info_link_{idx}"
            chart_text.tag_add(tag_name, start_index, end_index)
            chart_text.tag_bind(tag_name, "<Button-1>", lambda e, artist=artist, song_title=song_title: show_song_info(artist, song_title))
            chart_text.tag_config(tag_name, underline=True)  # Kein spezieller Farbton

        # Aktualisiere das Monatseingabefeld basierend auf der Woche
        first_day_of_week = datetime.date.fromisocalendar(year, week, 1)
        month = first_day_of_week.month
        month_entry.delete(0, tk.END)
        month_entry.insert(0, month)

    except ValueError:
        print("Bitte geben Sie gültige Zahlen für Jahr und Woche ein.")
    except Exception as e:
        print(f"Fehler in display_weekly_charts: {e}")

# Funktion zum Anzeigen von Song-Informationen
def show_song_info(artist, song_title):
    try:
        # Neues Fenster erstellen
        info_window = tk.Toplevel(root)
        info_window.title(f"Info: {song_title} - {artist}")

        # Statusmeldung anzeigen
        info_label = tk.Label(info_window, text="Lade Song-Informationen...")
        info_label.pack()

        # API-Aufruf für track.getInfo mit artist und song_title
        params = {
            'method': 'track.getInfo',
            'api_key': API_KEY,
            'format': 'json',
            'artist': artist,
            'track': song_title,
        }

        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            info_label.config(text=f"Fehler: {data['message']}")
            return

        track_info = data.get('track', {})

        # Informationen extrahieren
        listeners = track_info.get('listeners', 'N/A')
        playcount = track_info.get('playcount', 'N/A')
        duration_ms = track_info.get('duration', '0')  # Dauer in Millisekunden
        duration_formatted = format_duration(duration_ms)
        album_info = track_info.get('album', {})
        album_title = album_info.get('title', 'N/A')
        tags = track_info.get('toptags', {}).get('tag', [])
        tags_list = [tag.get('name') for tag in tags]
        tags_str = ', '.join(tags_list) if tags_list else 'Keine'

        # Wiki-Informationen (optional)
        wiki = track_info.get('wiki', {})
        summary = wiki.get('summary', 'Keine Zusammenfassung verfügbar.')

        # Anzeige der Informationen
        info_text = f"""
Titel: {song_title}
Künstler: {artist}
Album: {album_title}
Dauer: {duration_formatted} ({duration_ms} ms)
Hörer: {listeners}
Wiedergaben: {playcount}
Tags: {tags_str}
Zusammenfassung:
{summary}
"""

        # Überprüfen, welche Chart-Art zuletzt angezeigt wurde, um den entsprechenden Zeitraum abzurufen
        if last_chart_type == 'week':
            period = f"Woche {last_week}, {last_year}"
            cache_key = f'{current_user}_week_{last_year}_{last_week}'
        elif last_chart_type == 'month':
            period = f"Monat {last_month}, {last_year}"
            cache_key = f'{current_user}_month_{last_year}_{last_month}'
        elif last_chart_type == 'year':
            period = f"Jahr {last_year}"
            cache_key = f'{current_user}_year_{last_year}'
        else:
            period = "Unbekannter Zeitraum"
            cache_key = None

        # Liste der Song-Einträge im aktuellen Zeitraum
        if cache_key and cache_key in data_cache:
            current_df = data_cache[cache_key]
            # Filtere nach dem angeklickten Song
            song_entries = current_df[
                (current_df['song_title'] == song_title) &
                (current_df['artist'] == artist)
            ]

            if not song_entries.empty:
                entries_text = "\nListe der Einträge in diesem Zeitraum:\n"
                entries_text += f"{'Timestamp':<20} {'Song Titel':<30} {'Künstler':<25} {'Album':<30}\n"
                entries_text += "-" * 105 + "\n"
                for _, row in song_entries.iterrows():
                    timestamp = row['date_time'].strftime("%Y-%m-%d %H:%M:%S")
                    song = row['song_title']
                    artist_name = row['artist']
                    album = row['album']
                    entries_text += f"{timestamp:<20} {song:<30} {artist_name:<25} {album:<30}\n"
            else:
                entries_text = "\nKeine weiteren Einträge für diesen Song in diesem Zeitraum."
        else:
            entries_text = "\nKeine Einträge verfügbar."

        # Vollständiger Informationstext
        full_info_text = info_text + entries_text

        # Aktualisiere das Label
        info_label.config(text=full_info_text, justify=tk.LEFT)
        info_label.pack_forget()  # Entferne das Label, da wir ein Text-Widget verwenden
        chart_text = tk.Text(text_frame, width=150, height=50, font=(FONT_FAMILY, FONT_SIZE_TEXT))

        # Scrollbares Text-Widget für die Anzeige der Informationen
        info_text_widget = tk.Text(info_window, width=110, height=40, font=(FONT_FAMILY, FONT_SIZE_TEXT), wrap=tk.WORD)
        info_text_widget.insert(tk.END, full_info_text)
        info_text_widget.config(state=tk.DISABLED)
        info_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar = tk.Scrollbar(info_window, command=info_text_widget.yview)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        info_text_widget.config(yscrollcommand=info_scrollbar.set)

    except Exception as e:
        print(f"Fehler in show_song_info: {e}")
        info_label.config(text="Fehler beim Laden der Song-Informationen.")

# Funktion zur Anzeige der Monatscharts
def display_monthly_charts(year, month):
    global last_chart_type
    last_chart_type = 'month'

    try:
        # Eingabevalidierung
        if month < 1 or month > 12:
            print(f"Ungültiger Monat: {month}. Monat muss zwischen 1 und 12 sein.")
            return

        if year < 2000 or year > newest_date.year:
            print(f"Ungültiges Jahr: {year}.")
            return

        # Statusmeldung: Daten werden geladen
        chart_label.config(text="Daten werden von Last.fm geladen...")
        chart_label.update_idletasks()

        # Daten für den Zeitraum laden
        df = load_data_for_period('month', year, month=month)

        # Statusmeldung: Berechnungen werden durchgeführt
        chart_label.config(text="Führe Berechnungen durch...")
        chart_label.update_idletasks()

        if df.empty:
            chart_label.config(text=f"Keine Daten für Monat {month}, {year}")
            chart_text.delete('1.0', tk.END)
            return

        # Berechne die Monatscharts
        points, plays, results = calculate_monthly_charts(df, year, month)

        if results.empty:
            chart_label.config(text=f"Keine Daten für Monat {month}, {year}")
            chart_text.delete('1.0', tk.END)
            return

        # Hole den Monatsnamen
        month_name = calendar.month_name[month]

        # Setze die Überschrift
        chart_label.config(text=f"Monatscharts - {month_name} {year} - {current_user}")

        # Lösche die alte Chartanzeige
        chart_text.delete('1.0', tk.END)

        # Füge die Top-Songs hinzu
        for idx, ((song_title, artist), row) in enumerate(results.iterrows(), start=1):
            album = row['album'] if 'album' in row else ''
            play_count = format_value(row['play_count'])
            point = format_value(row['points'])

            album = album if pd.notna(album) else ''

            # Text für den Song
            song_text = f"{idx:>2}. {play_count:>2}× {point:>2} Pkt: {song_title} - {artist} ({album}) "
            # Einfügen des Textes in das Text-Widget
            chart_text.insert(tk.END, song_text)

            # Füge den Link hinzu
            start_index = chart_text.index(tk.INSERT)
            chart_text.insert(tk.END, "Info\n")  # Einheitlicher Link-Text
            end_index = chart_text.index(tk.INSERT)
            tag_name = f"info_link_{idx}"
            chart_text.tag_add(tag_name, start_index, end_index)
            chart_text.tag_bind(tag_name, "<Button-1>", lambda e, artist=artist, song_title=song_title: show_song_info(artist, song_title))
            chart_text.tag_config(tag_name, underline=True)  # Kein spezieller Farbton

        # Setze das Wocheneingabefeld auf die erste Woche des Monats
        first_day_of_month = datetime.date(year, month, 1)
        week = first_day_of_month.isocalendar()[1]
        week_entry.delete(0, tk.END)
        week_entry.insert(0, week)

    except ValueError:
        print("Bitte geben Sie gültige Zahlen für Jahr und Monat ein.")
    except Exception as e:
        print(f"Fehler in display_monthly_charts: {e}")

# Funktion zur Anzeige der Jahrescharts
def display_yearly_charts(year):
    global last_chart_type
    last_chart_type = 'year'

    try:
        # Eingabevalidierung
        if year < 2000 or year > newest_date.year:
            print(f"Ungültiges Jahr: {year}.")
            return

        # Statusmeldung: Daten werden geladen
        chart_label.config(text="Daten werden von Last.fm geladen...")
        chart_label.update_idletasks()

        # Daten für den Zeitraum laden
        df = load_data_for_period('year', year)

        # Statusmeldung: Berechnungen werden durchgeführt
        chart_label.config(text="Führe Berechnungen durch...")
        chart_label.update_idletasks()

        if df.empty:
            chart_label.config(text=f"Keine Daten für Jahr {year}")
            chart_text.delete('1.0', tk.END)
            return

        # Berechne die Jahrescharts
        points, plays, results = calculate_yearly_charts(df, year)

        if results.empty:
            chart_label.config(text=f"Keine Daten für Jahr {year}")
            chart_text.delete('1.0', tk.END)
            return

        # Setze die Überschrift
        chart_label.config(text=f"Jahrescharts - {year} - {current_user}")

        # Lösche die alte Chartanzeige
        chart_text.delete('1.0', tk.END)

        # Füge die Top-Songs hinzu
        for idx, ((song_title, artist), row) in enumerate(results.iterrows(), start=1):
            album = row['album'] if 'album' in row else ''
            play_count = format_value(row['play_count'])
            point = format_value(row['points'])

            album = album if pd.notna(album) else ''

            # Text für den Song
            song_text = f"{idx:>2}. {play_count:>3}× {point:>3} Pkt: {song_title} - {artist} ({album}) "

            # Einfügen des Textes in das Text-Widget
            chart_text.insert(tk.END, song_text)

            # Füge den Link hinzu
            start_index = chart_text.index(tk.INSERT)
            chart_text.insert(tk.END, "Info\n")  # Einheitlicher Link-Text
            end_index = chart_text.index(tk.INSERT)
            tag_name = f"info_link_{idx}"
            chart_text.tag_add(tag_name, start_index, end_index)
            chart_text.tag_bind(tag_name, "<Button-1>", lambda e, artist=artist, song_title=song_title: show_song_info(artist, song_title))
            chart_text.tag_config(tag_name, underline=True)  # Kein spezieller Farbton

    except ValueError:
        print("Bitte geben Sie eine gültige Zahl für das Jahr ein.")
    except Exception as e:
        print(f"Fehler in display_yearly_charts: {e}")

# Starte die GUI
initialize()
root.mainloop()
