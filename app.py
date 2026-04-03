from flask import Flask, jsonify, render_template
from countdown_service import get_countdown

app = Flask(__name__)

print("APP STARTET...")  # Debug


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/countdown/<mode>")
def api_countdown(mode):
    try:
        if mode not in ["contact", "exam"]:
            return jsonify({"error": "Ungültiger Modus"}), 400

        result = get_countdown(mode)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔥 GANZ WICHTIG (das hat bei dir gefehlt)
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)