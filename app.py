"""
FILE: app.py

Main Flask backend for the Smart Parking Occupancy Analysis and
Prediction System.

Page routes (render HTML):
    /             -> Dashboard
    /parking      -> Parking Data Entry + table of records
    /analytics    -> Analytics (runs R script, shows charts + stats)
    /prediction   -> Prediction form
    /about        -> About page

API routes (return JSON):
    GET  /api/parking     -> list all parking records
    POST /api/parking     -> add a new parking record
    GET  /api/dashboard   -> current dashboard summary numbers
    GET  /api/analytics   -> chart data (occupancy by hour/day/area/event/weather)
    POST /api/predict     -> run R prediction script and return the result

How Flask talks to R:
    We use Python's built-in `subprocess` module to run R scripts as
    separate processes ("Rscript some_script.R arg1 arg2 ...").
    - For analysis, the R script writes its results to a JSON file
      (r_results/analysis_results.json) which Flask then reads.
    - For prediction, the R script PRINTS a JSON string to stdout,
      which Flask captures directly from the subprocess result.
    This is the simplest, most beginner-friendly way to connect
    Python and R without building a separate R web server.
"""

import os
import glob
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "parking.db")
R_RESULTS_PATH = os.path.join(BASE_DIR, "r_results", "analysis_results.json")

VALID_WEATHER = {"Normal", "Rainy", "Hot"}
VALID_EVENT = {"Yes", "No"}
VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def get_rscript_path():
    """Finds the Rscript executable from PATH or common Windows installation directories."""
    path = shutil.which("Rscript")
    if path:
        return path

    # Search common installation locations on Windows
    patterns = [
        r"C:\Program Files\R\R-*\bin\x64\Rscript.exe",
        r"C:\Program Files\R\R-*\bin\Rscript.exe",
        r"C:\Program Files (x86)\R\R-*\bin\x64\Rscript.exe",
        r"C:\Program Files (x86)\R\R-*\bin\Rscript.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\R\R-*\bin\Rscript.exe"),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            matches.sort(reverse=True)
            return matches[0]

    return "Rscript"


# ----------------------------------------------------------------------
# Database helpers
# ----------------------------------------------------------------------

def get_db_connection():
    """Opens a connection to the SQLite database with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def classify_status(occupancy_percentage):
    """Same LOW / MEDIUM / HIGH rule used everywhere in the app."""
    if occupancy_percentage <= 40:
        return "LOW"
    elif occupancy_percentage <= 70:
        return "MEDIUM"
    else:
        return "HIGH"


# ----------------------------------------------------------------------
# Page routes (render templates)
# ----------------------------------------------------------------------

@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/parking")
def parking_page():
    return render_template("parking.html")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@app.route("/prediction")
def prediction_page():
    return render_template("prediction.html")


@app.route("/about")
def about_page():
    return render_template("about.html")


# ----------------------------------------------------------------------
# API: Parking data (list + add)
# ----------------------------------------------------------------------

@app.route("/api/parking", methods=["GET"])
def api_get_parking():
    """Returns the most recent parking records as JSON (used by the table)."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM parking_data ORDER BY id DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/add-parking", methods=["POST"])
def api_add_parking():
    """Validates and inserts a new parking record."""
    data = request.get_json(silent=True) or {}

    errors = []
    date = str(data.get("date", "")).strip()
    day = str(data.get("day", "")).strip()
    time_ = str(data.get("time", "")).strip()
    weather = str(data.get("weather", "")).strip()
    event = str(data.get("event", "")).strip()
    parking_area = str(data.get("parking_area", "")).strip()

    # --- Validation ---
    if not date:
        errors.append("Date is required.")
    if day not in VALID_DAYS:
        errors.append("Day must be a valid day of the week.")
    if not time_:
        errors.append("Time is required.")
    if weather not in VALID_WEATHER:
        errors.append("Weather must be Normal, Rainy, or Hot.")
    if event not in VALID_EVENT:
        errors.append("Event must be Yes or No.")
    if not parking_area:
        errors.append("Parking area is required.")

    try:
        total_slots = int(data.get("total_slots"))
        occupied_slots = int(data.get("occupied_slots"))
        if total_slots <= 0:
            errors.append("Total slots must be a positive number.")
        if occupied_slots < 0:
            errors.append("Occupied slots cannot be negative.")
        if occupied_slots > total_slots:
            errors.append("Occupied slots cannot be greater than total slots.")
    except (TypeError, ValueError):
        errors.append("Total slots and occupied slots must be valid numbers.")
        total_slots = occupied_slots = None

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    occupancy_percentage = round((occupied_slots / total_slots) * 100, 1)

    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO parking_data
            (date, day, time, total_slots, occupied_slots, weather, event, parking_area, occupancy_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date, day, time_, total_slots, occupied_slots, weather, event, parking_area, occupancy_percentage))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        return jsonify({"success": False, "errors": [f"Database error: {e}"]}), 500

    return jsonify({
        "success": True,
        "occupancy_percentage": occupancy_percentage,
        "status": classify_status(occupancy_percentage)
    })


# ----------------------------------------------------------------------
# API: Dashboard summary
# ----------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Returns the latest record's numbers plus a few quick overall stats."""
    conn = get_db_connection()
    latest = conn.execute(
        "SELECT * FROM parking_data ORDER BY id DESC LIMIT 1"
    ).fetchone()

    overall = conn.execute(
        "SELECT AVG(occupancy_percentage) as avg_occ, COUNT(*) as total_records FROM parking_data"
    ).fetchone()
    conn.close()

    if latest is None:
        return jsonify({
            "has_data": False,
            "message": "No parking data yet. Add a record on the Parking Data page."
        })

    latest_dict = dict(latest)
    latest_dict["status"] = classify_status(latest_dict["occupancy_percentage"])
    latest_dict["available_slots"] = latest_dict["total_slots"] - latest_dict["occupied_slots"]

    return jsonify({
        "has_data": True,
        "latest": latest_dict,
        "average_occupancy": round(overall["avg_occ"], 1) if overall["avg_occ"] is not None else 0,
        "total_records": overall["total_records"]
    })


# ----------------------------------------------------------------------
# API: Analytics chart data (fast, computed directly with SQL)
# ----------------------------------------------------------------------

@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """Returns aggregated data for the Chart.js charts on the Analytics page."""
    conn = get_db_connection()

    by_hour = conn.execute("""
        SELECT substr(time, 1, 2) as hour, ROUND(AVG(occupancy_percentage), 1) as avg_occ
        FROM parking_data GROUP BY hour ORDER BY hour
    """).fetchall()

    by_day = conn.execute("""
        SELECT day, ROUND(AVG(occupancy_percentage), 1) as avg_occ
        FROM parking_data GROUP BY day
    """).fetchall()

    by_area = conn.execute("""
        SELECT parking_area, ROUND(AVG(occupancy_percentage), 1) as avg_occ
        FROM parking_data GROUP BY parking_area
    """).fetchall()

    by_event = conn.execute("""
        SELECT event, ROUND(AVG(occupancy_percentage), 1) as avg_occ
        FROM parking_data GROUP BY event
    """).fetchall()

    by_weather = conn.execute("""
        SELECT weather, ROUND(AVG(occupancy_percentage), 1) as avg_occ
        FROM parking_data GROUP BY weather
    """).fetchall()

    available_over_time = conn.execute("""
        SELECT date, ROUND(AVG(total_slots - occupied_slots), 1) as avg_available
        FROM parking_data GROUP BY date ORDER BY date
    """).fetchall()

    conn.close()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day_sorted = sorted([dict(r) for r in by_day], key=lambda r: day_order.index(r["day"]) if r["day"] in day_order else 99)

    return jsonify({
        "by_hour": [dict(r) for r in by_hour],
        "by_day": by_day_sorted,
        "by_area": [dict(r) for r in by_area],
        "by_event": [dict(r) for r in by_event],
        "by_weather": [dict(r) for r in by_weather],
        "available_over_time": [dict(r) for r in available_over_time],
    })


# ----------------------------------------------------------------------
# API: Run the R analysis script (statistics + peak hours + charts)
# ----------------------------------------------------------------------

@app.route("/api/run-r-analysis", methods=["POST"])
def api_run_r_analysis():
    """
    Calls R/data_analysis.R using subprocess. That script reads the
    database, computes statistics/peak hours, generates PNG charts
    into static/images/, and writes r_results/analysis_results.json.
    We then read that JSON file and return it to the browser.
    """
    try:
        rscript_cmd = get_rscript_path()
        result = subprocess.run(
            [rscript_cmd, "R/data_analysis.R"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "error": "R (Rscript) was not found. Please install R and make sure it is on your PATH."
        }), 500
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "R analysis script timed out."}), 500

    if result.returncode != 0:
        return jsonify({
            "success": False,
            "error": "R script failed.",
            "details": result.stderr
        }), 500

    if not os.path.exists(R_RESULTS_PATH):
        return jsonify({"success": False, "error": "R script did not produce a results file."}), 500

    with open(R_RESULTS_PATH) as f:
        r_results = json.load(f)

    return jsonify({"success": True, "results": r_results})


# ----------------------------------------------------------------------
# API: Prediction (calls R/prediction.R)
# ----------------------------------------------------------------------

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}

    day = str(data.get("day", "")).strip()
    time_ = str(data.get("time", "")).strip()
    weather = str(data.get("weather", "")).strip()
    event = str(data.get("event", "")).strip()
    parking_area = str(data.get("parking_area", "")).strip()

    errors = []
    if day not in VALID_DAYS:
        errors.append("Please choose a valid day.")
    if not time_:
        errors.append("Please choose a time.")
    if weather not in VALID_WEATHER:
        errors.append("Please choose a valid weather condition.")
    if event not in VALID_EVENT:
        errors.append("Please specify Yes or No for event.")
    if not parking_area:
        errors.append("Please choose a parking area.")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        rscript_cmd = get_rscript_path()
        result = subprocess.run(
            [rscript_cmd, "R/prediction.R", day, time_, weather, event, parking_area],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "errors": ["R (Rscript) was not found. Please install R and make sure it is on your PATH."]
        }), 500
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "errors": ["Prediction script timed out."]}), 500

    if result.returncode != 0:
        return jsonify({
            "success": False,
            "errors": ["Prediction failed in R script."],
            "details": result.stderr
        }), 500

    try:
        prediction = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "errors": ["Could not read prediction result from R."],
            "details": result.stdout
        }), 500

    return jsonify({"success": True, "prediction": prediction})


# ----------------------------------------------------------------------
# Error handlers
# ----------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run 'python database/init_db.py' first.")
    app.run(debug=True, port=5000)
