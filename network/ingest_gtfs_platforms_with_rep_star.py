#!/usr/bin/env python3
import csv, sys, os, sqlite3
from collections import defaultdict

def parse_time_to_seconds(t):
    if not t or t.strip()=="":
        return None
    parts = t.strip().split(":")
    if len(parts)!=3: return None
    try:
        h,m,s = int(parts[0]), int(parts[1]), int(parts[2])
        return h*3600 + m*60 + s
    except:
        return None

def create_schema(con):
    cur = con.cursor()
    # Speed tweaks (safe for one-shot ETL)
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=OFF;")
    cur.execute("PRAGMA temp_store=MEMORY;")
    # Nodes = platforms only
    cur.execute("""
    CREATE TABLE IF NOT EXISTS node (
      stop_id    TEXT PRIMARY KEY,
      stop_name  TEXT NOT NULL,
      stop_lat   REAL,
      stop_lon   REAL,
      is_rep     INTEGER NOT NULL DEFAULT 0  -- 0/1
    );
    """)
    # Edges = directed (run + zero-transfer)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS edge (
      src_stop_id  TEXT NOT NULL REFERENCES node(stop_id) ON DELETE CASCADE,
      dst_stop_id  TEXT NOT NULL REFERENCES node(stop_id) ON DELETE CASCADE,
      weight_s     INTEGER NOT NULL CHECK (weight_s >= 0),
      edge_type    TEXT NOT NULL CHECK (edge_type IN ('run','intra_station0','station_link')),
      PRIMARY KEY (src_stop_id, dst_stop_id)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS node_name_idx ON node(stop_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS edge_src_idx  ON edge(src_stop_id, dst_stop_id);")
    # one rep (is_rep=1) per stop_name
    cur.execute("""
      CREATE UNIQUE INDEX IF NOT EXISTS one_rep_per_name
      ON node(stop_name) WHERE is_rep=1;
    """)
    con.commit()

def load_platforms(stops_path):
    nodes = {}                 # stop_id -> (name, lat, lon)
    by_name = defaultdict(list)# stop_name -> [stop_id...]
    with open(stops_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            lt = (row.get("location_type") or "0").strip()
            if lt == "1":
                continue  # skip station/parent rows; we’re platform-only
            sid = (row.get("stop_id") or "").strip()
            if not sid: continue
            name = (row.get("stop_name") or "").strip()
            lat  = row.get("stop_lat"); lon = row.get("stop_lon")
            latf = float(lat) if lat not in (None,"") else None
            lonf = float(lon) if lon not in (None,"") else None
            nodes[sid] = (name, latf, lonf)
            by_name[name].append(sid)
    # rep = lexicographically smallest stop_id for each stop_name
    rep_for_name = {name: min(sids) for name, sids in by_name.items()}
    return nodes, by_name, rep_for_name

def load_run_edges(stop_times_path):
    rows = []
    with open(stop_times_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            tid = (row.get("trip_id") or "").strip()
            sid = (row.get("stop_id") or "").strip()
            if not tid or not sid: continue
            seq_str = (row.get("stop_sequence") or "").strip()
            try:
                seq = int(seq_str)
            except:
                continue
            arr = parse_time_to_seconds(row.get("arrival_time"))
            dep = parse_time_to_seconds(row.get("departure_time"))
            rows.append((tid, seq, sid, arr, dep))
    rows.sort(key=lambda x: (x[0], x[1]))

    edge_min = {}  # (a,b) -> seconds
    prev = None; prev_tid = None
    for tid, seq, sid, arr, dep in rows:
        if tid != prev_tid:
            prev = (tid, seq, sid, arr, dep)
            prev_tid = tid
            continue
        _, pseq, psid, parr, pdep = prev
        if psid != sid:
            depart = pdep if pdep is not None else parr
            arrive = arr if arr is not None else dep
            if depart is not None and arrive is not None:
                d = arrive - depart
                if d > 0:
                    key = (psid, sid)
                    if key not in edge_min or d < edge_min[key]:
                        edge_min[key] = d
        prev = (tid, seq, sid, arr, dep)
    return edge_min

def chunked(iterable, n=1000):
    it = iter(iterable)
    while True:
        buf = []
        try:
            for _ in range(n):
                buf.append(next(it))
        except StopIteration:
            if buf: yield buf
            break
        yield buf

def main():
    if len(sys.argv) != 4:
        print("Usage: python ingest_gtfs_sqlite.py <stops.txt> <stop_times.txt> <network.db>", file=sys.stderr)
        sys.exit(1)

    stops_path, stop_times_path, db_path = sys.argv[1], sys.argv[2], sys.argv[3]
    if not os.path.exists(stops_path) or not os.path.exists(stop_times_path):
        print("stops.txt or stop_times.txt not found.", file=sys.stderr); sys.exit(1)

    con = sqlite3.connect(db_path)
    create_schema(con)
    cur = con.cursor()

    # 1) Nodes
    nodes, by_name, rep_for_name = load_platforms(stops_path)

    cur.execute("BEGIN;")
    for batch in chunked(((sid, n[0], n[1], n[2]) for sid, n in nodes.items()), 5000):
        cur.executemany("""
            INSERT INTO node (stop_id, stop_name, stop_lat, stop_lon)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(stop_id) DO UPDATE SET
              stop_name=excluded.stop_name,
              stop_lat=excluded.stop_lat,
              stop_lon=excluded.stop_lon;
        """, batch)
    con.commit()

    # Mark reps (one per stop_name)
    cur.execute("BEGIN;")
    # Clear old flags (optional)
    cur.execute("UPDATE node SET is_rep=0;")
    for batch in chunked(((1, rep) for rep in rep_for_name.values()), 5000):
        cur.executemany("UPDATE node SET is_rep=? WHERE stop_id=?;", batch)
    con.commit()

    # 2) Run edges
    edge_min = load_run_edges(stop_times_path)
    cur.execute("BEGIN;")
    for batch in chunked(((a, b, w, 'run') for (a,b), w in edge_min.items()
                          if a in nodes and b in nodes), 5000):
        cur.executemany("""
            INSERT INTO edge (src_stop_id, dst_stop_id, weight_s, edge_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(src_stop_id, dst_stop_id) DO UPDATE SET
              weight_s = MIN(edge.weight_s, excluded.weight_s);
        """, batch)
    con.commit()

    # 3) Zero-weight star edges via reps (bidirectional)
    zero_rows = []
    for name, sids in by_name.items():
        rep = rep_for_name[name]
        for sid in sids:
            if sid == rep: continue
            zero_rows.append((sid, rep, 0, 'intra_station0'))  # platform -> rep
            zero_rows.append((rep, sid, 0, 'intra_station0'))  # rep -> platform

    cur.execute("BEGIN;")
    for batch in chunked(zero_rows, 10000):
        cur.executemany("""
            INSERT OR IGNORE INTO edge (src_stop_id, dst_stop_id, weight_s, edge_type)
            VALUES (?, ?, ?, ?);
        """, batch)
    con.commit()

    # Summary
    node_count = cur.execute("SELECT COUNT(*) FROM node;").fetchone()[0]
    edge_count = cur.execute("SELECT COUNT(*) FROM edge;").fetchone()[0]
    rep_count  = cur.execute("SELECT COUNT(*) FROM node WHERE is_rep=1;").fetchone()[0]
    print(f"Done. nodes={node_count}, reps={rep_count}, edges={edge_count}")

    cur.close(); con.close()

if __name__ == "__main__":
    main()
