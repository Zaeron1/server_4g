#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)
DATABASE = 'measurements.db'


def init_db():
    """
    Crée la table 'measurements' si elle n'existe pas déjà.
    """
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.before_first_request
def initialize_database():
    """
    Appelé par Flask avant la toute première requête,
    pour s'assurer que la base est prête.
    """
    init_db()

@app.route("/", methods=["GET"])
def index():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        # Récupération de toutes les mesures (ordre descendant)
        cur.execute("SELECT id, temperature, timestamp FROM measurements ORDER BY id DESC")
        rows = cur.fetchall()

    measurements = []
    for row in rows:
        measurements.append({
            'id': row[0],
            'temperature': row[1],
            'timestamp': row[2]
        })

    # Dernière mesure
    last_temp = measurements[0]['temperature'] if measurements else 0

    # Template avec gauge Google Charts
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <title>Mesures de Température</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h1 { color: #333; }
            #gauge_div {
                width: 400px; 
                height: 200px; 
                margin: 0 auto;
            }
            table {
                border-collapse: collapse; 
                margin-top: 30px; 
                width: 80%;
            }
            th, td { 
                border: 1px solid #ccc; 
                padding: 8px 12px; 
                text-align: center; 
            }
            th { background: #f0f0f0; }
        </style>
        <!-- Google Charts -->
        <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
        <script type="text/javascript">
          google.charts.load('current', {'packages':['gauge']});
          google.charts.setOnLoadCallback(drawGauge);

          function drawGauge() {
            var data = google.visualization.arrayToDataTable([
              ['Label', 'Value'],
              ['Temp °C', {{ last_temp }}]
            ]);

            var options = {
              min: 0, max: 50,
              yellowFrom: 25, yellowTo: 35,
              redFrom: 35, redTo: 50,
              greenFrom: 0, greenTo: 25,
              minorTicks: 5
            };

            var chart = new google.visualization.Gauge(document.getElementById('gauge_div'));
            chart.draw(data, options);
          }
        </script>
    </head>
    <body>
        <h1>Visualisation des Températures</h1>
        <div id="gauge_div"></div>

        <table>
            <tr>
                <th>ID</th>
                <th>Température (°C)</th>
                <th>Horodatage</th>
            </tr>
            {% for m in measurements %}
            <tr>
                <td>{{ m.id }}</td>
                <td>{{ m.temperature }}</td>
                <td>{{ m.timestamp }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, measurements=measurements, last_temp=last_temp)

@app.route("/api/receiver", methods=["POST"])
def api_receiver():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    temperature = data.get("temperature")
    if temperature is None:
        return jsonify({"status": "error", "message": "No 'temperature' field found"}), 400

    timestamp = datetime.now().isoformat()

    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO measurements (temperature, timestamp) VALUES (?, ?)",
                    (temperature, timestamp))
        conn.commit()

    print(f"[DEBUG] Nouvelle donnée reçue : {temperature} °C à {timestamp}")
    return jsonify({"status": "success", "message": "Data received"}), 200

if __name__ == "__main__":
    # En local, si vous lancez python app.py, on initialise la DB et on run
    app.run(host='0.0.0.0', port=500, debug=True)
