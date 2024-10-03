import tkinter as tk
from tkinter import ttk
import requests
import pandas as pd
import calendar
import time
from datetime import datetime
from collections import Counter

# API-Key und URL für Last.fm
API_KEY = "12a4e15b6f7a4d6543e53a43b89804e7"
USER = "athefu"
BASE_URL = f"http://ws.audioscrobbler.com/2.0/"

# Funktion, um Daten von der Last.fm API zu laden
def fetch_lastfm_data(limit=50, page=1, from_ts=None, to_ts=None):
    try:
        params = {
            "method": "user.getrecenttracks",
            "user": USER,
            "api_key": API_KEY,
            "format": "json",
            "limit": limit,
            "page": page
        }
        
        if from_ts:
            params['from'] = from_ts
        if to_ts:
            params['to'] = to_ts
        
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Fehler beim Abrufen der Daten von Last.fm: {response.status_code}")
            return None
    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")
        return None

# Funktion, um die Daten in ein DataFrame zu konvertieren
def convert_to_dataframe(data):
    track_list = data['recenttracks']['track']
    
    rows = []
    for track in track_list:
        artist = track['artist']['#text']
        song_title = track['name']
        album = track['album']['#text']
        date_time = track['date']['#text'] if 'date' in track else "aktuell"  # Falls der Track aktuell gespielt wird, gibt es kein Datum
        rows.append([artist, album, song_title, date_time])
    
    # DataFrame erstellen
    df = pd.DataFrame(rows, columns=['artist', 'album', 'song_title', 'date_time'])
    # Konvertiere die Datumsspalte in datetime, falls möglich
    df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
    return df

# Funktion, um einen UNIX-Zeitstempel zu berechnen
def get_unix_timestamp(year, month=None, day=None, week=None):
    if week:
        d = f'{year}-W{week}-1'
        dt = datetime.strptime(d, "%Y-W%W-%w")
    else:
        dt = datetime(year, month if month else 1, day if day else 1)
    return int(time.mktime(dt.timetuple()))

# Funktion, um Daten iterativ zu laden, bis der gewünschte Zeitraum abgedeckt ist
def load_data_until(df, year=None, month=None, week=None):
    page = 1
    limit = 200  # Maximale Anzahl pro Seite
    from_ts, to_ts = None, None
    
    # Wenn Jahr, Monat oder Woche angegeben, setze den Zeitraum
    if year:
        if month:
            from_ts = get_unix_timestamp(year, month)
            to_ts = get_unix_timestamp(year, month + 1) - 1 if month < 12 else get_unix_timestamp(year + 1)
        elif week:
            from_ts = get_unix_timestamp(year, week=week)
            to_ts = get_unix_timestamp(year, week=week + 1) - 1
        else:
            from_ts = get_unix_timestamp(year)
            to_ts = get_unix_timestamp(year + 1) - 1
    
    while True:
        data = fetch_lastfm_data(limit=limit, page=page, from_ts=from_ts, to_ts=to_ts)
        if data:
            temp_df = convert_to_dataframe(data)
            if temp_df.empty:
                print("Keine weiteren Daten gefunden.")
                break
            
            # Debugging: Seitennummer, ältestes und jüngstes Datum ausgeben
            oldest_date = temp_df['date_time'].min()
            newest_date = temp_df['date_time'].max()
            print(f"Seite {page}: Jüngstes Datum: {newest_date}, Ältestes Datum: {oldest_date}")
            
            # Check, ob die ältesten Daten außerhalb des Zeitraums liegen
            if pd.isnull(oldest_date) or (oldest_date.year < year) or (month and oldest_date.month < month) or (week and oldest_date.isocalendar().week < week):
                print("Daten außerhalb des gesuchten Zeitraums. Beende das Laden.")
                break

            # Füge die neuen Daten zum Gesamt-DataFrame hinzu
            df = pd.concat([df, temp_df], ignore_index=True)

            # Prüfe, ob die Anzahl der Einträge kleiner ist als das Limit, dann sind alle Daten geladen
            if len(temp_df) < limit:
                print("Alle Daten für den Zeitraum geladen.")
                break

            # Erhöhe die Seitenzahl für die nächste Abfrage
            page += 1
        else:
            break

    return df

# Initialisiere globale Variablen
df = pd.DataFrame(columns=['artist', 'album', 'song_title', 'date_time'])
oldest_date = None
newest_date = None
last_year = None
last_month = None
last_week = None

# Funktion, um die Daten zu laden und die globalen Variablen zu setzen
def initialize_data(year=None, month=None, week=None):
    global df, oldest_date, newest_date, last_year, last_month, last_week
    df = pd.DataFrame(columns=['artist', 'album', 'song_title', 'date_time'])  # DataFrame zurücksetzen
    
    # Lade die Daten iterativ, bis der Zeitraum abgedeckt ist
    df = load_data_until(df, year=year, month=month, week=week)
    
    if not df.empty:
        # Das älteste und das neueste Datum aus den Daten ermitteln
        oldest_date = df['date_time'].min()
        newest_date = df['date_time'].max()

        # Jahr, Monat und Woche der letzten Einträge bestimmen
        last_year = newest_date.year
        last_month = newest_date.month
        last_week = newest_date.isocalendar().week
        print(f"Initialisiert {oldest_date} - {newest_date}")

# Funktion zur wöchentlichen Top-20-Songs-Auswertung
def calculate_weekly_charts(df, year, week):
    try:
        df['week'] = df['date_time'].dt.isocalendar().week
        df['year'] = df['date_time'].dt.year
        week_data = df[(df['year'] == year) & (df['week'] == week)]

        # Zähle die Häufigkeit jedes Songs (basierend auf song_title, artist und album)
        top_songs = week_data.groupby(['song_title', 'artist', 'album']).size().nlargest(20)

        if top_songs.empty:
            print(f"Keine Songs für Woche {week} im Jahr {year} gefunden.")

        # Punkte für Wochencharts (Platz 1 = 20 Punkte, Platz 2 = 19 usw.)
        points = {song: 20 - i for i, song in enumerate(top_songs.index)}

        # Erstelle einen DataFrame der Top-Songs
        top_songs_df = week_data.drop_duplicates(subset=['song_title', 'artist', 'album'])
        top_songs_df = top_songs_df.set_index(['song_title', 'artist', 'album']).loc[top_songs.index]

        # Rückgabe: Punkte, Anzahl der Wiedergaben und die Top-Songs
        return points, top_songs, top_songs_df

    except Exception as e:
        print(f"Fehler in calculate_weekly_charts: {e}")
        return {}, pd.Series(), pd.DataFrame()

# Funktion zur monatlichen Top-30-Songs-Auswertung
def calculate_monthly_charts(df, year, month):
    try:
        df['month'] = df['date_time'].dt.month
        df['year'] = df['date_time'].dt.year
        month_data = df[(df['year'] == year) & (df['month'] == month)]

        # Zuerst alle Wochen des Monats ermitteln
        weeks_in_month = month_data['date_time'].dt.isocalendar().week.unique()
        weekly_points = Counter()
        weekly_plays = Counter()

        # Berechnung der Wochencharts für jede Woche des Monats
        for week in weeks_in_month:
            points, plays, _ = calculate_weekly_charts(df, year, week)
            for song, points_count in points.items():
                weekly_points[song] += points_count
                weekly_plays[song] += plays[song]

        # Top 30 Songs für den Monat
        top_songs = sorted(weekly_points.items(), key=lambda x: (-x[1], -weekly_plays[x[0]]))[:30]
        top_songs_list = [song for song, _ in top_songs]

        # Setze den Index auf ['song_title', 'artist', 'album']
        valid_songs = month_data[['song_title', 'artist', 'album']].drop_duplicates()
        valid_songs = valid_songs.set_index(['song_title', 'artist', 'album'])

        # Filtere die Liste der Songs, die im Index vorhanden sind
        top_songs_list = [song for song in top_songs_list if song in valid_songs.index]

        return dict(top_songs), dict(weekly_plays), valid_songs.loc[top_songs_list]

    except Exception as e:
        print(f"Fehler in calculate_monthly_charts: {e}")
        return {}, {}, pd.DataFrame()

# Funktion zur jährlichen Top-50-Songs-Auswertung
def calculate_yearly_charts(df, year):
    try:
        df['year'] = df['date_time'].dt.year
        year_data = df[df['year'] == year]

        # Zuerst alle Monate des Jahres ermitteln
        months_in_year = year_data['date_time'].dt.month.unique()
        monthly_points = Counter()
        monthly_plays = Counter()

        # Berechnung der Monatscharts für jeden Monat des Jahres
        for month in months_in_year:
            points, plays, _ = calculate_monthly_charts(df, year, month)
            for song, points_count in points.items():
                monthly_points[song] += points_count
                monthly_plays[song] += plays[song]

        # Top 50 Songs für das Jahr
        top_songs = sorted(monthly_points.items(), key=lambda x: (-x[1], -monthly_plays[x[0]]))[:50]
        top_songs_list = [song for song, _ in top_songs]

        # Setze den Index auf ['song_title', 'artist', 'album']
        valid_songs = year_data[['song_title', 'artist', 'album']].drop_duplicates()
        valid_songs = valid_songs.set_index(['song_title', 'artist', 'album'])

        # Filtere die Liste der Songs, die im Index vorhanden sind
        top_songs_list = [song for song in top_songs_list if song in valid_songs.index]

        return dict(top_songs), dict(monthly_plays), valid_songs.loc[top_songs_list]

    except Exception as e:
        print(f"Fehler in calculate_yearly_charts: {e}")
        return {}, {}, pd.DataFrame()

# GUI erstellen
root = tk.Tk()
root.title("Last.fm Charts Auswertung")

# Jahr, Monat und Woche Eingabefelder
ttk.Label(root, text="Jahr:").grid(row=0, column=0)
year_entry = ttk.Entry(root)
year_entry.grid(row=0, column=1)

ttk.Label(root, text="Monat:").grid(row=1, column=0)
month_entry = ttk.Entry(root)
month_entry.grid(row=1, column=1)

ttk.Label(root, text="Woche:").grid(row=2, column=0)
week_entry = ttk.Entry(root)
week_entry.grid(row=2, column=1)

# Buttons für die Charts
ttk.Button(root, text="Jahrescharts", command=lambda: display_yearly_charts()).grid(row=0, column=2)
ttk.Button(root, text="Monatscharts", command=lambda: display_monthly_charts()).grid(row=1, column=2)
ttk.Button(root, text="Wochencharts", command=lambda: display_weekly_charts()).grid(row=2, column=2)
ttk.Button(root, text="Reset", command=lambda: reset_input()).grid(row=3, column=2)

# Funktion zum Zurücksetzen der Eingabefelder
def reset_input():
    year_entry.delete(0, tk.END)
    year_entry.insert(0, last_year)  # Trage das letzte Jahr ein
    month_entry.delete(0, tk.END)
    month_entry.insert(0, last_month)  # Trage das letzte Monat ein
    week_entry.delete(0, tk.END)
    week_entry.insert(0, last_week)  # Trage die letzte Woche ein

# Funktion, die durch das Drücken der Enter-Taste ausgelöst wird
def bind_search_functions():
    year_entry.bind("<Return>", lambda event: display_yearly_charts())
    month_entry.bind("<Return>", lambda event: display_monthly_charts())
    week_entry.bind("<Return>", lambda event: display_weekly_charts())

# Binde die Enter-Taste an die Suchfunktionen
bind_search_functions()

# Label und Listbox zur Anzeige der Charts
chart_label = ttk.Label(root, text="Charts")
chart_label.grid(row=4, column=0, columnspan=3)

chart_listbox = tk.Listbox(root, width=100, height=40)
chart_listbox.grid(row=5, column=0, columnspan=3)

# Funktion zur Anzeige der Wochencharts
def display_weekly_charts():
    try:
        year = int(year_entry.get())
        week = int(week_entry.get())

        # Berechne die Wochencharts
        points, plays, results = calculate_weekly_charts(df, year, week)

        # Setze die Überschrift
        chart_label.config(text=f"Wochencharts - Woche {week}, {year}")

        # Lösche die alte Chartanzeige
        chart_listbox.delete(0, tk.END)

        # Füge die Top 20 Songs mit Anzahl der Wiedergaben (×) und Platzierung hinzu
        for i, ((song_title, artist, album), row) in enumerate(results.iterrows(), start=1):
            chart_listbox.insert(tk.END, f"{i:2}. {plays[(song_title, artist, album)]:2}× {song_title} - {artist} ({album})")

    except Exception as e:
        print(f"Fehler in display_weekly_charts: {e}")

# Funktion zur Anzeige der Monatscharts
def display_monthly_charts():
    try:
        year = int(year_entry.get())
        month = int(month_entry.get())

        # Berechne die Monatscharts
        points, plays, results = calculate_monthly_charts(df, year, month)

        # Hole den Monatsnamen aus der Zahl
        month_name = calendar.month_name[month]

        # Setze die Überschrift auf den Monatsnamen
        chart_label.config(text=f"Monatscharts - {month_name} {year}")

        # Lösche die alte Chartanzeige
        chart_listbox.delete(0, tk.END)

        # Füge die Top 30 Songs mit Punkten, Wiedergaben und Platzierung hinzu
        for i, ((song_title, artist, album), row) in enumerate(results.iterrows(), start=1):
            chart_listbox.insert(tk.END, f"{i:2}. {plays[(song_title, artist, album)]:2} × {points[(song_title, artist, album)]:2}: {song_title} - {artist} ({album})")

    except Exception as e:
        print(f"Fehler in display_monthly_charts: {e}")

# Funktion zur Anzeige der Jahrescharts
def display_yearly_charts():
    try:
        year = int(year_entry.get())

        # Berechne die Jahrescharts
        points, plays, results = calculate_yearly_charts(df, year)

        # Setze die Überschrift
        chart_label.config(text=f"Jahrescharts - {year}")

        # Lösche die alte Chartanzeige
        chart_listbox.delete(0, tk.END)

        # Füge die Top 50 Songs mit Punkten, Wiedergaben und Platzierung hinzu
        for i, ((song_title, artist, album), row) in enumerate(results.iterrows(), start=1):
            chart_listbox.insert(tk.END, f"{i:2}. {plays[(song_title, artist, album)]:3} × {points[(song_title, artist, album)]:3}: {song_title} - {artist} ({album})")

    except Exception as e:
        print(f"Fehler in display_yearly_charts: {e}")

# Starte die GUI
root.mainloop()
