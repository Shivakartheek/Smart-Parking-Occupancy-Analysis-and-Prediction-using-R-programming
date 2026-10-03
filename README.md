# Smart Parking Occupancy Analysis and Prediction System Using R

A beginner-friendly full-stack college project (Flask + R + SQLite) that
monitors parking occupancy in real time and predicts future occupancy
using a statistical model.

---

## 1. Problem Statement

Drivers waste time searching for available parking spaces, while parking
managers have no clear view of peak occupancy periods. This system
analyzes parking data, displays current parking status on a dashboard,
identifies peak hours, and predicts future occupancy.

## 2. Objectives

- Track real-time parking occupancy (total / occupied / available slots)
- Classify occupancy into LOW / MEDIUM / HIGH status
- Visualize occupancy patterns by hour, day, area, weather, and events
- Automatically detect peak hours and busiest days
- Predict future occupancy for a given day/time/weather/event/area using
  a linear regression model built in R
- Store all data in a simple, portable SQLite database

## 3. Features

| Module | Description |
|---|---|
| Dashboard | Live cards for total/occupied/available slots, occupancy %, and LOW/MEDIUM/HIGH status, plus a recent trend chart |
| Parking Data Entry | A validated form to add new parking records, and a table of recent records |
| Analytics | Interactive Chart.js charts (by hour, day, area, event, weather, availability over time) + real R-generated statistical charts |
| Peak Hour Detection | Peak hour, lowest hour, busiest day, average & max occupancy — computed in R |
| Prediction | Form-based prediction of future occupancy using a linear regression model trained in R |

## 4. Technologies Used

- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript, Chart.js
- **Backend:** Python 3, Flask
- **Data Analysis / ML:** R (dplyr, ggplot2, jsonlite, DBI/RSQLite, `lm()` linear regression)
- **Database:** SQLite

## 5. System Architecture

```
Browser (HTML/CSS/JS, Chart.js)
        │  fetch() calls
        ▼
Flask backend (app.py) ───SQL───► SQLite (database/parking.db)
        │
        │  subprocess.run(["Rscript", ...])
        ▼
R scripts (R/data_analysis.R, R/prediction.R)
        │
        ├─ read/write ──► SQLite (same database)
        ├─ write ───────► r_results/analysis_results.json (stats)
        ├─ write ───────► static/images/*.png (charts)
        └─ print JSON to stdout ──► Flask captures it (prediction result)
```

Flask never re-implements the statistics itself — it calls the R scripts
as separate processes using Python's built-in `subprocess` module, which
is the simplest way to connect Python and R for a college project (no
extra R web server needed).

## 6. Project Structure

```
smart-parking/
├── app.py                     Flask backend (pages + REST API)
├── requirements.txt
├── README.md
├── database/
│   ├── init_db.py             Creates the DB and loads sample data
│   └── parking.db             SQLite database (created after setup)
├── data/
│   └── parking_data.csv       220-row realistic sample dataset
├── R/
│   ├── preprocessing.R        Shared load/clean/classify helpers
│   ├── data_analysis.R        Stats, peak hours, calls visualization.R
│   ├── prediction.R           Trains lm() model, predicts occupancy
│   └── visualization.R        ggplot2 chart generation
├── r_results/
│   └── analysis_results.json  Latest R analysis output (auto-generated)
├── models/                    (reserved for saved model artifacts)
├── templates/
│   ├── base.html               Shared layout + navbar
│   ├── index.html               Dashboard
│   ├── parking.html            Data entry + table
│   ├── analytics.html          Charts
│   ├── prediction.html         Prediction form
│   └── about.html              About page
└── static/
    ├── css/style.css
    ├── js/script.js
    └── images/                 R-generated PNG charts (auto-generated)
```

## 7. Database Design

Table `parking_data`:

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| date | TEXT | dd-mm-yyyy |
| day | TEXT | Monday…Sunday |
| time | TEXT | HH:MM (24-hour) |
| total_slots | INTEGER | Capacity of the area |
| occupied_slots | INTEGER | Must be ≤ total_slots |
| weather | TEXT | Normal / Rainy / Hot |
| event | TEXT | Yes / No |
| parking_area | TEXT | e.g. Block A |
| occupancy_percentage | REAL | Auto-computed: occupied/total × 100 |

`database/init_db.py` creates this table and loads `data/parking_data.csv`
into it the first time you run it.

## 8. Installation (Windows)

### Step 1 — Install Python dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Install R

1. Download R from https://cran.r-project.org/bin/windows/base/ and install it.
2. Make sure `Rscript` is on your PATH (the R installer usually asks about this,
   or you can add `C:\Program Files\R\R-4.x.x\bin` to PATH manually).
3. Open the R console (or RStudio) and install the required packages:

```r
install.packages(c("dplyr", "ggplot2", "jsonlite", "DBI", "RSQLite"))
```

(macOS/Linux users: install R with `brew install r` or your package
manager, e.g. on Ubuntu: `sudo apt install r-base r-cran-dplyr
r-cran-ggplot2 r-cran-jsonlite r-cran-rsqlite r-cran-dbi`.)

### Step 3 — Set up the database

```bash
python database/init_db.py
```

This creates `database/parking.db` and loads the 220-row sample dataset.

### Step 4 — Run the app

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

## 9. How to Run the R Scripts

You normally don't need to run these manually — Flask calls them for you
(when you open the Analytics page and click "Run R Statistical Analysis",
and whenever you submit the Prediction form). But you can also run them
directly from the project root folder to see their output:

```bash
Rscript R/data_analysis.R
Rscript R/prediction.R "Monday" "11:00" "Normal" "Yes" "Block A"
```

## 10. Testing Instructions

1. Start the app and open the Dashboard — confirm it shows the latest
   record's stats and a trend chart.
2. Go to **Parking Data**, submit a record with `occupied_slots` greater
   than `total_slots` — confirm you get a friendly validation error.
3. Submit a valid record — confirm it appears at the top of the table
   and the dashboard updates.
4. Go to **Analytics**, click "Run R Statistical Analysis" — confirm the
   peak hour / busiest day / average / max occupancy cards populate and
   four new chart images appear.
5. Go to **Prediction**, fill the form with a day/time/weather/event/area
   and submit — confirm you get a predicted occupancy %, available slots,
   and a status badge.
6. Stop the R installation (rename `Rscript` temporarily) and confirm the
   Analytics/Prediction pages show a friendly error instead of crashing.

## 11. Sample Output

```
Dashboard:
  Total Slots: 100   Occupied: 72   Available: 28   Occupancy: 72%   Status: MEDIUM

Analytics (R):
  Peak Hour: 11:00   Busiest Day: Monday   Avg Occupancy: 45.2%   Max: 98%

Prediction (Monday, 11:00, Normal, Event=Yes, Block A):
  Predicted Occupancy: 73.2%   Available: 27   Status: HIGH
```

## 12. Future Enhancements

- Add user authentication for administrators
- Support multiple facilities/buildings in one deployment
- Real-time sensor integration (IoT slot sensors) instead of manual entry
- Export analytics reports as PDF
- More advanced models (Random Forest, time-series forecasting) in R

## 13. Conclusion

This project demonstrates a complete, working full-stack pipeline: a
Flask web app backed by SQLite for storage, with genuine statistical
analysis and machine learning prediction performed in R and connected to
the backend through `subprocess`. It is intentionally kept simple and
well-commented so a 2nd-year student can confidently explain every part
of it.

---

## 14. Viva Questions and Answers

**Q1. Why did you use SQLite instead of MySQL/PostgreSQL?**
SQLite is serverless and file-based — no separate database server needs
to be installed or configured, which keeps the project simple and
portable for a college demo.

**Q2. Why use R for the analysis instead of doing everything in Python?**
The project brief specifically required R for statistical analysis and
prediction. R's `dplyr` and `ggplot2` make data summarization and
visualization concise, and `lm()` provides a simple, well-understood
regression model. Python/Flask stays focused on serving the web app.

**Q3. How does Flask communicate with R?**
Using Python's built-in `subprocess` module, Flask runs the R scripts as
separate processes (like typing `Rscript script.R` in a terminal). For
analysis, the R script writes its results to a JSON file that Flask
reads back. For prediction, the R script prints a JSON string to
"stdout" (its output stream) which Flask captures directly.

**Q4. What machine learning algorithm did you use for prediction, and why?**
Multiple Linear Regression (`lm()` in R). It's simple to train, fast, and
easy to explain: it estimates occupancy as a weighted combination of
hour, day, weather, event, and parking area — enough to model a
beginner-friendly project without over-engineering.

**Q5. How is occupancy percentage calculated?**
`occupancy_percentage = (occupied_slots / total_slots) × 100`, rounded to
1 decimal place, calculated identically in the Flask backend, the R
scripts, and re-validated on each database read.

**Q6. How do you classify LOW / MEDIUM / HIGH status?**
0–40% is LOW, 41–70% is MEDIUM, 71–100% is HIGH. This rule is applied
consistently in both the Flask backend and the R scripts.

**Q7. What happens if a user enters occupied slots greater than total slots?**
The Flask `/api/add-parking` endpoint validates this before touching the
database and returns a clear error message instead of saving bad data.

**Q8. What if the prediction form is given a parking area that doesn't
exist in the historical data?**
The R model checks whether the input's category (day/weather/event/area)
was seen during training. If not, it safely falls back to the overall
average occupancy instead of crashing or producing a nonsensical value.

**Q9. How were peak hours identified?**
`R/data_analysis.R` groups all records by hour, calculates the average
occupancy per hour with `dplyr`, and picks the hour with the highest
(and lowest) average.

**Q10. Is this a real working system or just a UI mockup?**
It's fully functional: the form saves real records to SQLite, the
dashboard and analytics read real data from the database, the R scripts
perform genuine statistical computation and train a real regression
model each time they run, and the charts are generated from live data
— not hardcoded.

**Q11. How would you scale this for a real deployment?**
Swap SQLite for PostgreSQL/MySQL, add authentication, run Flask behind a
production WSGI server (e.g. Gunicorn) with Nginx, and consider caching
R analysis results instead of recomputing them on every click.

**Q12. What does `subprocess.run()` do in `app.py`?**
It launches an external program (here, `Rscript`) as a new process,
waits for it to finish, and captures its output (stdout/stderr) and
return code so Flask can react to success or failure.

---

## 15. Project Presentation Points

1. **Problem & motivation** — wasted time searching for parking, no
   visibility into peak periods for managers.
2. **Architecture diagram** — browser ↔ Flask ↔ SQLite, with Flask
   calling R via subprocess for analysis and prediction.
3. **Live demo flow:** Dashboard → add a record on Parking Data → watch
   Dashboard update → Analytics (run R analysis, show charts) →
   Prediction (submit a scenario, show predicted occupancy).
4. **Highlight the R integration** — open `R/data_analysis.R` and
   `R/prediction.R` briefly to show real statistical code, not just a
   Python simulation.
5. **Data validation** — demo submitting an invalid record (occupied >
   total) to show error handling.
6. **Design choices** — why SQLite, why linear regression, why
   subprocess instead of a full R web API (simplicity for a student
   project).
7. **Future scope** — IoT sensors, multi-facility support, better models.
