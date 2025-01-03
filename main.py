# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
from flask import Flask, Response, send_from_directory
import os
import time
from threading import Thread
from email.utils import format_datetime
from datetime import datetime

app = Flask(__name__)

RSS_FILE = "corrected_youtube_rss.xml"
ONE_DAY_IN_SECONDS = 24 * 60 * 60
# URL do istniejącego feedu RSS YouTube
YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLf8XERBV_Iuv4-YfCd7ucWbe44usUikJ6"

def is_file_stale(file_path, max_age_in_seconds):
    """Sprawdź, czy plik jest starszy niż maksymalny wiek."""
    if not os.path.exists(file_path):
        return True
    file_age = time.time() - os.path.getmtime(file_path)
    return file_age > max_age_in_seconds

def gen_pod():
    """Generowanie nowego pliku RSS."""
    try:
        # Zdefiniuj przestrzenie nazw
        namespaces = {
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/',
            'atom': 'http://www.w3.org/2005/Atom'
        }

        # Pobierz dane z YouTube RSS
        response = requests.get(YOUTUBE_RSS_URL)
        response.raise_for_status()
        youtube_rss = response.content

        # Parsuj oryginalny RSS
        root = ET.fromstring(youtube_rss)

        # Utwórz nowy RSS 2.0
        rss = ET.Element("rss", version="2.0", xmlns="http://www.youtube.com/xml/schemas/2015")
        channel = ET.SubElement(rss, "channel")

        # Dodaj informacje o kanale
        title = root.find("./atom:title", namespaces).text
        link = root.find("./atom:link", namespaces).attrib["href"]
        description = "RSS z YouTube playlist"

        ET.SubElement(channel, "title").text = title
        ET.SubElement(channel, "link").text = "https://awsbpodcast.onrender.com/rss"
        ET.SubElement(channel, "description").text = description

        # Dodaj element <atom:link> poprawnie deklarując przestrzeń nazw
        atom_link = ET.SubElement(
            channel,
            "{http://www.w3.org/2005/Atom}link",
            attrib={"rel": "self", "href": "https://awsbpodcast.onrender.com/rss"}
        )

        # Dodaj każdy wpis z XML jako element RSS
        for entry in root.findall("./atom:entry", namespaces):
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = entry.find("./atom:title", namespaces).text
            ET.SubElement(item, "link").text = entry.find("./atom:link", namespaces).attrib["href"]
            ET.SubElement(item, "description").text = entry.find("./media:group/media:description", namespaces).text
            
            # Konwersja daty na RFC-822
            published = entry.find("./atom:published", namespaces).text
            pub_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S%z")
            ET.SubElement(item, "pubDate").text = format_datetime(pub_date)

            # Dodaj unikalny identyfikator (guid)
            video_id = entry.find("./yt:videoId", namespaces).text
            guid = f"https://www.youtube.com/watch?v={video_id}"
            ET.SubElement(item, "guid").text = guid

        # Zapisz do pliku
        tree = ET.ElementTree(rss)
        tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)

    except Exception as e:
        print(f"Error while generating RSS: {e}")


#    print("Poprawiony RSS został zapisany w pliku 'corrected_youtube_rss.xml'")

def refresh_rss_in_background():
    """Uruchom odświeżanie RSS w tle."""
    thread = Thread(target=gen_pod)
    thread.start()

@app.route("/favicon.ico")
def favicon():
    """Serwowanie favicon.ico z katalogu głównego."""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "favicon.ico", mimetype="image/x-icon")

@app.route("/reset", methods=["POST", "GET"])
def reset_rss():
    """Resetowanie pliku RSS - usunięcie i wygenerowanie nowego."""
    try:
        # Usuń istniejący plik, jeśli istnieje
        if os.path.exists(RSS_FILE):
            os.remove(RSS_FILE)
            print(f"Plik {RSS_FILE} został usunięty.")

        # Wygeneruj nowy plik RSS
        gen_pod()
        return "Plik RSS został zresetowany i wygenerowany na nowo.", 200
    except Exception as e:
        print(f"Błąd podczas resetowania pliku RSS: {e}")
        return f"Błąd podczas resetowania pliku RSS: {e}", 500


# Domyślna ścieżka, np. strona informacyjna
@app.route("/rss")
def home():
    return "To jest serwer RSS. Użyj ścieżki /rss, aby uzyskać kanał RSS."

# Endpoint dla RSS
@app.route("/")
def serve_rss():
    gen_pod()
    try:
        with open("corrected_youtube_rss.xml", "r", encoding="utf-8") as file:
            rss_content = file.read()
        return Response(rss_content, mimetype='application/rss+xml')
    except FileNotFoundError:
        return "RSS file not found. Generate the RSS file first.", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

