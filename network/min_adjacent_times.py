#!/usr/bin/env python3
import csv, sys, os, re

# ----------------------------
# Robust CSV reading (case-insensitive headers)
# ----------------------------
def open_csv_rows(folder_path, filename):
    p = os.path.join(folder_path, filename)
    if not os.path.exists(p):
        raise FileNotFoundError(f"{filename} not found at {folder_path}")
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.reader(f)
        try:
            headers = next(rdr)
        except StopIteration:
            return
        headers_l = [h.strip().lower() for h in headers]
        for row in rdr:
            # pad/truncate row length just in case
            if len(row) < len(headers_l):
                row = row + [""] * (len(headers_l) - len(row))
            elif len(row) > len(headers_l):
                row = row[:len(headers_l)]
            yield {headers_l[i]: (row[i] or "").strip() for i in range(len(headers_l))}

# ----------------------------
# Helpers
# ----------------------------
def parse_int(s, default=None):
    try:
        return int(s)
    except Exception:
        return default

def parse_time_to_seconds(t):
    if not t:
        return None
    parts = t.split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h*3600 + m*60 + s
    except Exception:
        return None

# ----------------------------
# Lookups (with robust fallbacks)
# ----------------------------
def load_stop_names(folder_path):
    names = {}
    for r in open_csv_rows(folder_path, "stops.txt"):
        sid = r.get("stop_id", "")
        if not sid:
            continue
        names[sid] = r.get("stop_name", "") or sid
    return names

def load_routes(folder_path):
    """
    Returns:
      route_id -> symbol (prefer short; else route_id; else long)
      known_tokens: set of candidate tokens to match in trip_id fallback
    """
    rmap = {}
    tokens = set()
    for r in open_csv_rows(folder_path, "routes.txt"):
        rid   = r.get("route_id", "")
        short = r.get("route_short_name", "")
        longn = r.get("route_long_name", "")
        sym = (short or rid or longn or "").strip()
        if rid or sym:
            rmap[rid or sym] = sym
            if rid:   tokens.add(rid)
            if short: tokens.add(short)
            # common express variants like "6X", "7X"
            if short and short.endswith(("X", "x")):
                tokens.add(short.upper())
                tokens.add(short.lower())
    return rmap, tokens

TRIP_ID_TOKEN_RE = re.compile(r"^[A-Za-z0-9]+")
def derive_symbol_from_trip_id(trip_id, known_tokens):
    """
    Heuristic fallback: many MTA trip_ids begin with the route symbol (A, C, N, 6, 6X, etc.).
    We grab the leading alnum token and try progressively shorter prefixes against known tokens.
    """
    if not trip_id:
        return None
    m = TRIP_ID_TOKEN_RE.match(trip_id)
    if not m:
        return None
    tok = m.group(0)
    # Try the whole token, then shorten (e.g., "6X" -> "6X", then "6")
    for L in range(len(tok), 0, -1):
        cand = tok[:L]
        if cand in known_tokens or cand.upper() in known_tokens or cand.lower() in known_tokens:
            return cand.upper()  # normalize to upper for letters
    return None

def build_trip_to_symbol(folder_path, route_map, known_tokens):
    """
    Returns: trip_id -> symbol string (never empty; 'NA' if we cannot determine)
    """
    t2s = {}
    for r in open_csv_rows(folder_path, "trips.txt"):
        tid = r.get("trip_id", "")
        rid = r.get("route_id", "")
        sym = ""
        if rid:
            sym = route_map.get(rid, "") or rid
        if not sym:
            # fallback: derive from trip_id
            sym = derive_symbol_from_trip_id(tid, known_tokens) or ""
        t2s[tid] = sym if sym else "NA"
    return t2s

# ----------------------------
# Core computation
# ----------------------------
def compute_min_segments_with_single_line(folder_path):
    names = load_stop_names(folder_path)
    route_map, known_tokens = load_routes(folder_path)
    trip2sym = build_trip_to_symbol(folder_path, route_map, known_tokens)

    # Read stop_times and sort by (trip_id, stop_sequence)
    rows = []
    for r in open_csv_rows(folder_path, "stop_times.txt"):
        tid = r.get("trip_id", "")
        sid = r.get("stop_id", "")
        if not tid or not sid:
            continue
        seq = parse_int(r.get("stop_sequence", ""), None)
        if seq is None:
            continue
        arr = parse_time_to_seconds(r.get("arrival_time", ""))
        dep = parse_time_to_seconds(r.get("departure_time", ""))
        rows.append((tid, seq, sid, arr, dep))
    rows.sort(key=lambda x: (x[0], x[1]))

    mins   = {}  # (a,b) -> seconds
    winner = {}  # (a,b) -> single symbol

    prev = None
    prev_trip = None

    for row in rows:
        trip_id, seq, stop_id, arr, dep = row
        if trip_id != prev_trip:
            prev = row
            prev_trip = trip_id
            continue

        _, p_seq, p_stop, p_arr, p_dep = prev
        if p_stop == stop_id:
            prev = row
            continue

        depart_t = p_dep if p_dep is not None else p_arr
        arrive_t = arr if arr is not None else dep
        if depart_t is None or arrive_t is None:
            prev = row
            continue

        delta = arrive_t - depart_t
        if delta <= 0:
            prev = row
            continue

        key = (p_stop, stop_id)
        best = mins.get(key)
        if best is None or delta < best:
            mins[key] = delta
            winner[key] = trip2sym.get(trip_id, "NA")

        prev = row

    return mins, winner, names

# ----------------------------
# Main
# ----------------------------
def main():
    if len(sys.argv) != 2:
        print("Usage: python min_adjacent_times_platform_directed_with_line_fixed.py <path_to_extracted_gtfs_folder>", file=sys.stderr)
        sys.exit(1)

    folder = sys.argv[1]
    mins, winner, names = compute_min_segments_with_single_line(folder)

    print("from_stop_id,from_stop_name,to_stop_id,to_stop_name,min_travel_time_seconds,line")
    def nm(sid): return names.get(sid, sid).replace(",", " ")
    for (a, b) in sorted(mins.keys(), key=lambda k: (nm(k[0]), nm(k[1]), k[0], k[1])):
        print(f"{a},{nm(a)},{b},{nm(b)},{mins[(a,b)]},{winner.get((a,b),'NA')}")

if __name__ == "__main__":
    main()
