"""
FILE: database/init_db.py

Creates the SQLite database (database/parking.db) with the
'parking_data' table, and loads the sample dataset
(data/parking_data.csv) into it so the app has data to show
the first time it runs.

Run this once before starting the Flask app:
    python database/init_db.py
"""

import sqlite3
import csv
import os

# Paths are relative to the project root, not this file,
# so this script should be run from the project root folder.
DB_PATH = os.path.join("database", "parking.db")
CSV_PATH = os.path.join("data", "parking_data.csv")


def create_table(conn):
    """Create the parking_data table if it does not already exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS parking_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            occupied_slots INTEGER NOT NULL,
            weather TEXT NOT NULL,
            event TEXT NOT NULL,
            parking_area TEXT NOT NULL,
            occupancy_percentage REAL NOT NULL
        )
    """)
    conn.commit()


def load_sample_data(conn):
    """Load the sample CSV into the table, but only if the table is empty.
    This way, re-running init_db.py does not create duplicate rows."""
    cursor = conn.execute("SELECT COUNT(*) FROM parking_data")
    count = cursor.fetchone()[0]

    if count > 0:
        print(f"Table already has {count} rows. Skipping sample data load.")
        return

    if not os.path.exists(CSV_PATH):
        print(f"No sample CSV found at {CSV_PATH}. Skipping.")
        return

    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["date"], row["day"], row["time"],
                int(row["total_slots"]), int(row["occupied_slots"]),
                row["weather"], row["event"], row["parking_area"],
                float(row["occupancy_percentage"])
            )
            for row in reader
        ]

    conn.executemany("""
        INSERT INTO parking_data
        (date, day, time, total_slots, occupied_slots, weather, event, parking_area, occupancy_percentage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    print(f"Loaded {len(rows)} sample rows into parking_data.")


def main():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)
    load_sample_data(conn)
    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    main()
