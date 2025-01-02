# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
from flask import Flask, Response

app = Flask(__name__)


@app.route("/favicon.ico")
def favicon():
    return "", 204  # Pusta odpowiedź, brak zawartości

# Domyślna ścieżka, np. strona informacyjna
@app.route("/rss")
def home():
    return "To jest serwer RSS. Użyj ścieżki /rss, aby uzyskać kanał RSS."

# Endpoint dla RSS
@app.route("/")
def serve_rss():
    try:
        with open("corrected_youtube_rss.xml", "r", encoding="utf-8") as file:
            rss_content = file.read()
        return Response(rss_content, mimetype='application/rss+xml')
    except FileNotFoundError:
        return "RSS file not found. Generate the RSS file first.", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
