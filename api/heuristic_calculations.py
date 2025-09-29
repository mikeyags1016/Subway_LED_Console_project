#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import os
from collections import defaultdict
import heapq

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def parse_time_to_seconds(t):
    """
    GTFS times may exceed 24:00:00 (e.g., '25:10:00'). Returns int seconds or None.
    """
    if not t or t.strip() == "":
        return None
    parts = t.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h = int(parts[0]); m = int(parts[1]); s = int(parts[2])
        return h*3600 + m*60 + s
    except Exception:
        return None

def read_stops(stops_path):
    """
    Reads stops.txt and returns:
      stops: stop_id -> dict(name, lat, lon, parent_station, location_type)
      stop_ids_in_order: list of stop_ids (stable order)
    """
    stops = {}
    stop_ids_in_order = []
    with open(stops_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            sid = (row.get("stop_id") or "").strip()
            if not sid:
                continue
            stop_ids_in_order.append(sid)
            stops[sid] = {
                "name": (row.get("stop_name") or "").strip(),
                "lat":  (row.get("stop_lat") or "").strip(),
                "lon":  (row.get("stop_lon") or "").strip(),
                "parent_station": (row.get("parent_station") or "").strip(),
                "location_type": (row.get("location_type") or "0").strip(),
            }
    return stops, stop_ids_in_order

def read_stop_times(stop_times_path):
    """
    Reads stop_times.txt rows minimally needed for adjacency and sorts by (trip_id, stop_sequence).
    Returns list of tuples: (trip_id, stop_sequence:int, stop_id, arrival_s:int|None, departure_s:int|None)
    """
    rows = []
    with open(stop_times_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            trip_id = (row.get("trip_id") or "").strip()
            stop_id = (row.get("stop_id") or "").strip()
            if not trip_id or not stop_id:
                continue
            try:
                seq = int((row.get("stop_sequence") or "").strip())
            except Exception:
                continue
            arr = parse_time_to_seconds(row.get("arrival_time"))
            dep = parse_time_to_seconds(row.get("departure_time"))
            rows.append((trip_id, seq, stop_id, arr, dep))
    rows.sort(key=lambda x: (x[0], x[1]))
    return rows

# ------------------------------------------------------------
# Graph construction (edge weights = min scheduled time between consecutive stops)
# ------------------------------------------------------------

def build_min_edge_weights(stop_times_rows):
    """
    Returns dict edge_min[(from_stop_id, to_stop_id)] = min_seconds across all trips
    Only considers *consecutive* stop pairs within the same trip_id ordered by stop_sequence.
    """
    edge_min = {}
    prev = None
    prev_trip = None

    for row in stop_times_rows:
        trip_id, seq, stop_id, arr, dep = row
        if trip_id != prev_trip:
            prev = row
            prev_trip = trip_id
            continue

        _, p_seq, p_stop, p_arr, p_dep = prev

        # Skip degenerate repeats
        if p_stop != stop_id:
            depart_t = p_dep if p_dep is not None else p_arr
            arrive_t = arr if arr is not None else dep
            if depart_t is not None and arrive_t is not None:
                delta = arrive_t - depart_t
                if delta > 0:
                    key = (p_stop, stop_id)
                    old = edge_min.get(key)
                    if old is None or delta < old:
                        edge_min[key] = delta

        prev = row

    return edge_min

def build_adjacency(all_stop_ids, edge_min):
    """
    Builds adjacency list: adj[stop_id] = list[(neighbor_stop_id, weight_seconds)]
    Ensures every stop_id from stops.txt appears as a node (even if it has no edges).
    """
    adj = {sid: [] for sid in all_stop_ids}
    for (a, b), w in edge_min.items():
        if a not in adj:
            adj[a] = []
        adj[a].append((b, w))
    # Sort neighbors by id for stable traversal (optional)
    for sid in adj:
        adj[sid].sort(key=lambda t: t[0])
    return adj

# ------------------------------------------------------------
# Dijkstra (single-source on directed, non-negative graph)
# ------------------------------------------------------------

def dijkstra_from_source(src_id, node_index, index_node, adj):
    """
    Runs Dijkstra from src_id using adjacency on stop_ids.
    Returns distances dict: stop_id -> best_time_seconds (int), excluding unreachable nodes.
    """
    INF = 2**31 - 1
    N = len(node_index)
    dist = { }  # we’ll keep a sparse dict to save memory
    visited = set()
    pq = []
    heapq.heappush(pq, (0, src_id))
    dist[src_id] = 0

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        for v, w in adj.get(u, []):
            nd = d + w
            # relax
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))

    return dist  # distances from src_id to reachable nodes

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 build_all_pairs_from_gtfs.py <path/to/stops.txt> <path/to/stop_times.txt>", file=sys.stderr)
        sys.exit(1)

    stops_path = sys.argv[1]
    stop_times_path = sys.argv[2]

    if not os.path.exists(stops_path):
        print(f"stops.txt not found at {stops_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(stop_times_path):
        print(f"stop_times.txt not found at {stop_times_path}", file=sys.stderr)
        sys.exit(1)

    # 1) Load stops (nodes)
    stops, stop_ids_in_order = read_stops(stops_path)

    # 2) Load stop_times and compute min edge weights between consecutive stops
    st_rows = read_stop_times(stop_times_path)
    edge_min = build_min_edge_weights(st_rows)

    # 3) Build adjacency (directed)
    adj = build_adjacency(stop_ids_in_order, edge_min)

    # 4) Index maps (if you later want arrays; here we keep IDs directly)
    node_index = {sid: i for i, sid in enumerate(stop_ids_in_order)}
    index_node = {i: sid for sid, i in node_index.items()}

    # 5) Output header exactly as requested
    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow([
        "from_stop_id","from_stop_name","from_stop_lat","from_stop_lon",
        "from_parent_station","to_stop_id","to_stop_name",
        "to_stop_lat","to_stop_lon","to_parent_station",
        "min_travel_time_seconds"
    ])

    # 6) Run Dijkstra from every stop and write reachable pairs
    #    (Skip identity pairs; skip unreachable.)
    for src in stop_ids_in_order:
        dists = dijkstra_from_source(src, node_index, index_node, adj)
        s_info = stops.get(src, {})
        s_name = s_info.get("name", src)
        s_lat  = s_info.get("lat", "")
        s_lon  = s_info.get("lon", "")
        s_par  = s_info.get("parent_station", "")

        for dst, best in dists.items():
            if dst == src:
                continue  # skip self
            t_info = stops.get(dst, {})
            t_name = t_info.get("name", dst)
            t_lat  = t_info.get("lat", "")
            t_lon  = t_info.get("lon", "")
            t_par  = t_info.get("parent_station", "")

            out.writerow([
                src, s_name, s_lat, s_lon,
                s_par, dst, t_name,
                t_lat, t_lon, t_par,
                best
            ])

if __name__ == "__main__":
    main()
