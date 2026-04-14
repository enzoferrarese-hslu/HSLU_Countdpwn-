import os

from flask import Flask, jsonify, render_template
from countdown_service import get_countdown, get_current_semester

app = Flask(__name__)


@app.route("/")
def home():
    semester = get_current_semester()
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
