#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Liste pour stocker les mesures reçues
received_data = []

@app.route("/", methods=["GET"])
def index():
    """
    Page d'accueil : affiche toutes les données reçues
    sous forme de tableau HTML.
    """
    # On prépare une liste "enumerated_data" (index, data)
    enumerated_data = list(enumerate(received_data))

    # Template minimal en HTML + Jinja2
    html_template = """
    <html>
    <head>
        <title>Visualisation des données Arduino</title>
        <style>
            table { border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ccc; padding: 8px 12px; }
        </style>
    </head>
    <body>
        <h1>Températures reçues</h1>
        <table>
            <tr>
                <th>Index</th>
                <th>Température</th>
                <th>Horodatage</th>
            </tr>
            {% for i, data in enumerated_data %}
            <tr>
                <td>{{ i }}</td>
                <td>{{ data.temperature }}</td>
                <td>{{ data.timestamp }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    # On injecte la liste 'enumerated_data' dans le template
    return render_template_string(html_template, enumerated_data=enumerated_data)


@app.route("/api/receiver", methods=["POST"])
def api_receiver():
    """
    Endpoint où l'Arduino envoie ses données en POST (JSON).
    On les insère dans 'received_data'.
    """
    # Récupération du JSON
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "No JSON received"}), 400

    # On s’attend à un champ "temperature" dans le JSON
    temperature = data.get("temperature")
    if temperature is None:
        return jsonify({"status": "error", "message": "No 'temperature' field found"}), 400

    # Ajout d'un horodatage
    timestamp = datetime.now().isoformat()

    # Stockage de la mesure dans la liste
    received_data.append({
        "temperature": temperature,
        "timestamp": timestamp
    })

    print(f"[DEBUG] Nouvelle donnée reçue : {temperature}°C à {timestamp}")

    # Réponse au client (Arduino)
    return jsonify({"status": "success", "message": "Data received"}), 200


if __name__ == "__main__":
    # Lancement du serveur Flask sur le port 5001
    # host='0.0.0.0' pour être accessible depuis le réseau local
    app.run(host='0.0.0.0', port=5001, debug=True)
