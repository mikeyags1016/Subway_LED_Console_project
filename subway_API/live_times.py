#!/usr/bin/env python3
import os
import sqlite3
from nyct_gtfs import NYCTFeed

# Optional: ensure your API key is set
# assert "MTA_API_KEY" in os.environ, "Set MTA_API_KEY first!"

# --- Define all lines manually (no shuttles) ---
feed_to_lines = {
    "ACE": ["A", "C", "E"],
    "BDFM": ["B", "D", "F", "M"],
    "NQRW": ["N", "Q", "R", "W"],
    "JZ": ["J", "Z"],
    "L": ["L"],
    "G": ["G"],
    "1234567": ["1", "2", "3", "4", "5", "6", "7"]
}

# Flatten feed groups into a single list of lines
lines = [line for lines_group in feed_to_lines.values() for line in lines_group]
print(f"🚇 Tracking {len(lines)} NYC subway lines (no shuttles): {', '.join(lines)}")

# --- Database setup ---
db_path = "subway.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS live_edges (
    line TEXT,
    from_stop TEXT,
    to_stop TEXT,
    travel_time_seconds INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- Process all lines ---
for line in lines:
    print(f"\n🔄 Fetching line {line} ...")
    try:
        feed = NYCTFeed(line)
    except Exception as e:
        print(f"⚠️ Failed to fetch {line} feed: {e}")
        continue

    last_seen = {}
    for trip in feed.trips:
        trip_id = trip.trip_id
        for stu in trip.stop_time_updates:
            if not stu.arrival:
                continue

            stop_id = stu.stop_id
            arrival = stu.arrival.timestamp()

            if trip_id in last_seen:
                prev_stop, prev_arrival = last_seen[trip_id]
                if prev_stop != stop_id and arrival > prev_arrival:
                    travel_time = int(arrival - prev_arrival)
                    print(f"[{line}] {prev_stop} → {stop_id}: {travel_time}s")
                    cur.execute("""
                    INSERT INTO live_edges (line, from_stop, to_stop, travel_time_seconds)
                    VALUES (?, ?, ?, ?)
                    """, (line, prev_stop, stop_id, travel_time))

            last_seen[trip_id] = (stop_id, arrival)
    conn.commit()

conn.close()
print("\n✅ Snapshot complete for all NYC lines (no shuttles). Data saved to subway.db")
