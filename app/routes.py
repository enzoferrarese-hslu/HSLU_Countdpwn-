from flask import Flask, jsonify, render_template, request

from app.database.db import init_db
from app.scraper.common import TECHNIK_ARCHITEKTUR
from app.services.countdown_service import get_countdown, get_current_semester

app = Flask(__name__, template_folder="templates", static_folder="static")

try:
    init_db()
except Exception as error:
    app.logger.warning("Datenbank konnte beim Start nicht initialisiert werden: %s", error)


@app.route("/")
def home():
    department_name = request.args.get("department", TECHNIK_ARCHITEKTUR)

    try:
        semester = get_current_semester(department_name)
    except Exception as error:
        app.logger.warning("Semester konnte nicht geladen werden: %s", error)
        semester = None

    return render_template("index.html", semester=semester)


@app.route("/countdown/<mode>")
def countdown_page(mode):
    department_name = request.args.get("department", TECHNIK_ARCHITEKTUR)

    if mode not in ["contact", "exam"]:
        return "Ungültiger Modus", 400
    return render_template("countdown.html", mode=mode, department_name=department_name)


@app.route("/api/countdown/<mode>")
def api_countdown(mode):
    department_name = request.args.get("department", TECHNIK_ARCHITEKTUR)

    try:
        if mode not in ["contact", "exam"]:
            return jsonify({"error": "Ungültiger Modus"}), 400

        result = get_countdown(mode, department_name)
        return jsonify(result)

    except Exception as error:
        return jsonify({"error": str(error)}), 500
