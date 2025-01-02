import requests
import xml.etree.ElementTree as ET
from flask import Flask, Response

app = Flask(__name__)

# URL do istniejącego feedu RSS YouTube
YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLf8XERBV_Iuv4-YfCd7ucWbe44usUikJ6"

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
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

# Dodaj informacje o kanale
ET.SubElement(channel, "title").text = root.find("./atom:title", namespaces).text
ET.SubElement(channel, "link").text = root.find("./atom:link", namespaces).attrib["href"]
ET.SubElement(channel, "description").text = "Poprawiony RSS z YouTube playlist"

# Dodaj każdy wpis z XML jako element RSS
for entry in root.findall("./atom:entry", namespaces):
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = entry.find("./atom:title", namespaces).text
    ET.SubElement(item, "link").text = entry.find("./atom:link", namespaces).attrib["href"]
    ET.SubElement(item, "description").text = entry.find("./media:group/media:description", namespaces).text
    ET.SubElement(item, "pubDate").text = entry.find("./atom:published", namespaces).text

# Zapisz do pliku
tree = ET.ElementTree(rss)
tree.write("corrected_youtube_rss.xml", encoding="utf-8", xml_declaration=True)

print("Poprawiony RSS został zapisany w pliku 'corrected_youtube_rss.xml'")


@app.route("/favicon.ico")
def favicon():
    return "", 204  # Pusta odpowiedź, brak zawartości

# Domyślna ścieżka, np. strona informacyjna
@app.route("/")
def home():
    return "To jest serwer RSS. Użyj ścieżki /rss, aby uzyskać kanał RSS."

# Endpoint dla RSS
@app.route("/rss")
def serve_rss():
    try:
        with open("corrected_youtube_rss.xml", "r", encoding="utf-8") as file:
            rss_content = file.read()
        return Response(rss_content, mimetype='application/rss+xml')
    except FileNotFoundError:
        return "RSS file not found. Generate the RSS file first.", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

