#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Configuration de la connexion PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("La variable d'environnement DATABASE_URL n'est pas définie.")

def get_db_connection():
    """
    Établit une connexion à la base de données PostgreSQL.
    """
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """
    Crée la table 'measurements' si elle n'existe pas déjà.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id SERIAL PRIMARY KEY,
            temperature REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Initialisation de la base de données au démarrage de l'application
init_db()

@app.route("/", methods=["GET"])
def index():
    """
    Page d'accueil : affiche la dernière mesure sous forme de gauge
    et la liste de toutes les mesures sous forme de tableau.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    # Récupération de toutes les mesures (ordre descendant)
    cur.execute("SELECT id, temperature, timestamp FROM measurements ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    measurements = []
    for row in rows:
        measurements.append({
            'id': row[0],
            'temperature': row[1],
            'timestamp': row[2].strftime("%Y-%m-%d %H:%M:%S")
        })

    # Dernière mesure
    last_temp = measurements[0]['temperature'] if measurements else 0

    # Template avec gauge Plotly
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
                background-color: #f9f9f9;
            }
            h1 { color: #333; text-align: center; }
            #gauge_div {
                width: 450px; 
                height: 350px; 
                margin: 0 auto;
            }
            table {
                border-collapse: collapse; 
                margin: 30px auto; 
                width: 90%;
                background-color: #fff;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 12px 15px; 
                text-align: center; 
            }
            th { 
                background-color: #4CAF50; 
                color: white; 
            }
            tr:nth-child(even) {background-color: #f2f2f2;}
        </style>
        <!-- Plotly.js -->
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script type="text/javascript">
          var gaugeChart;

          function drawGauge(value) {
            var data = [
              {
                type: "indicator",
                mode: "gauge+number",
                value: value,
                title: { text: "Température (°C)", font: { size: 24 } },
                gauge: {
                  axis: { range: [0, 50], tickwidth: 1, tickcolor: "darkblue" },
                  bar: { color: "darkblue" },
                  bgcolor: "white",
                  borderwidth: 2,
                  bordercolor: "gray",
                  steps: [
                    { range: [0, 25], color: "green" },
                    { range: [25, 35], color: "yellow" },
                    { range: [35, 50], color: "red" }
                  ],
                }
              }
            ];

            var layout = {
              width: 450,
              height: 350,
              margin: { t: 25, r: 25, l: 25, b: 25 },
              paper_bgcolor: "white",
              font: { color: "darkblue", family: "Arial" }
            };

            if (!gaugeChart) {
              gaugeChart = Plotly.newPlot('gauge_div', data, layout);
            } else {
              Plotly.update('gauge_div', { value: [value] }, layout);
            }
          }

          function updateTable(measurements) {
            var tableBody = document.getElementById("measurements-body");
            tableBody.innerHTML = ""; // Efface le contenu actuel

            measurements.forEach(function(measure) {
                var row = document.createElement("tr");

                var cellId = document.createElement("td");
                cellId.textContent = measure.id;
                row.appendChild(cellId);

                var cellTemp = document.createElement("td");
                cellTemp.textContent = measure.temperature;
                row.appendChild(cellTemp);

                var cellTime = document.createElement("td");
                cellTime.textContent = measure.timestamp;
                row.appendChild(cellTime);

                tableBody.appendChild(row);
            });
          }

          function fetchData() {
            fetch('/api/data')
              .then(response => response.json())
              .then(data => {
                  if (data.status === "success") {
                      var measurements = data.measurements;
                      if (measurements.length > 0) {
                          var last_temp = measurements[0].temperature;
                          drawGauge(last_temp);
                          updateTable(measurements);
                      }
                  } else {
                      console.error("Erreur lors de la récupération des données :", data.message);
                  }
              })
              .catch(error => {
                  console.error("Erreur lors de la requête fetch :", error);
              });
          }

          // Charger les données initiales au chargement de la page
          document.addEventListener("DOMContentLoaded", function() {
              fetchData();
              // Mettre à jour toutes les 5 secondes (5000 millisecondes)
              setInterval(fetchData, 5000);
          });
        </script>
    </head>
    <body>
        <h1>Visualisation des Températures</h1>
        <div id="gauge_div"></div>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Température (°C)</th>
                    <th>Horodatage</th>
                </tr>
            </thead>
            <tbody id="measurements-body">
                {% for m in measurements %}
                <tr>
                    <td>{{ m.id }}</td>
                    <td>{{ m.temperature }}</td>
                    <td>{{ m.timestamp }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, measurements=measurements, last_temp=last_temp)

@app.route("/api/data", methods=["GET"])
def get_data():
    """
    Endpoint qui renvoie toutes les mesures de température au format JSON.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, temperature, timestamp FROM measurements ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    measurements = []
    for row in rows:
        measurements.append({
            'id': row[0],
            'temperature': row[1],
            'timestamp': row[2].strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify({"status": "success", "measurements": measurements}), 200

@app.route("/api/receiver", methods=["POST"])
def api_receiver():
    """
    Endpoint où l'Arduino envoie ses données en POST (JSON).
    On insère dans la base PostgreSQL.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    temperature = data.get("temperature")
    if temperature is None:
        return jsonify({"status": "error", "message": "No 'temperature' field found"}), 400

    try:
        temperature = float(temperature)
    except ValueError:
        return jsonify({"status": "error", "message": "'temperature' must be a number"}), 400

    timestamp = datetime.now()

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO measurements (temperature, timestamp) VALUES (%s, %s)",
                    (temperature, timestamp))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'insertion dans la base de données : {e}")
        return jsonify({"status": "error", "message": "Database insertion failed"}), 500

    print(f"[DEBUG] Nouvelle donnée reçue : {temperature} °C à {timestamp}")
    return jsonify({"status": "success", "message": "Data received"}), 200

if __name__ == "__main__":
    # En local, si vous lancez python server_4g.py, on initialise la DB et on run
    app.run(host='0.0.0.0', port=5000, debug=True)
