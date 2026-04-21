from flask import Flask, jsonify, render_template

from app.database.db import init_db
from app.services.countdown_service import get_countdown, get_current_semester

app = Flask(__name__, template_folder="templates", static_folder="static")

try:
    init_db()
except Exception as error:
    app.logger.warning("Datenbank konnte beim Start nicht initialisiert werden: %s", error)


@app.route("/")
def home():
    try:
        semester = get_current_semester()
    except Exception as error:
        app.logger.warning("Semester konnte nicht geladen werden: %s", error)
        semester = None

    return render_template("index.html", semester=semester)


@app.route("/countdown/<mode>")
def countdown_page(mode):
    if mode not in ["contact", "exam"]:
        return "Ungültiger Modus", 400
    return render_template("countdown.html", mode=mode)


@app.route("/api/countdown/<mode>")
def api_countdown(mode):
    try:
        if mode not in ["contact", "exam"]:
            return jsonify({"error": "Ungültiger Modus"}), 400

        result = get_countdown(mode)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
