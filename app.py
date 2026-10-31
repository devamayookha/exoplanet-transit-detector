import json
from pathlib import Path

from flask import Flask, abort, jsonify, render_template


app = Flask(__name__)

RESULTS_DIR = Path(__file__).resolve().parent / "data" / "results"
STAR_FILES = {
    "kepler8": "kepler8.json",
    "kepler6": "kepler6.json",
    "control": "control.json",
}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/star/<name>")
def get_star(name):
    filename = STAR_FILES.get(name)
    if filename is None:
        abort(404)

    with (RESULTS_DIR / filename).open(encoding="utf-8") as result_file:
        return jsonify(json.load(result_file))


if __name__ == "__main__":
    app.run()
