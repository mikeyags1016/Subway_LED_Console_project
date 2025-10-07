#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import os
import heapq
from collections import defaultdict

# ------------------------------------------------------------
# Parse helpers
# ------------------------------------------------------------
def parse_time_to_seconds(t):
    if not t or t.strip() == "":
        return None
    parts = t.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h*3600 + m*60 + s
    except Exception:
        return None

# ------------------------------------------------------------
# Load stops (platform rows only) and station rows
# ------------------------------------------------------------
def read_stops(stops_path):
    """
    Returns:
      platforms: stop_id -> {name, lat, lon, parent_station}
      station_children: parent_station -> [platform_stop_id,...]
      station_exists: set of station (parent) ids (location_type==1)
      name_groups: stop_name -> [platform_stop_id,...]  (only platforms)
    """
    platforms = {}
    station_children = defaultdict(list)
    station_exists = set()
    name_groups = defaultdict(list)

    with open(stops_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            stop_id = (row.get("stop_id") or "").strip()
            if not stop_id:
                continue
            name = (row.get("stop_name") or "").strip()
            lat  = (row.get("stop_lat") or "").strip()
            lon  = (row.get("stop_lon") or "").strip()
            parent = (row.get("parent_station") or "").strip()
            lt = (row.get("location_type") or "0").strip()

            if lt == "1":
                # Station (parent)
                station_exists.add(stop_id)
                continue

            # Treat lt != '1' as platforms (including '0' or blank)
            platforms[stop_id] = {
                "name": name,
                "lat": lat,
                "lon": lon,
                "parent_station": parent
            }
            if parent:
                station_children[parent].append(stop_id)
            if name:
                name_groups[name].append(stop_id)

    return platforms, station_children, station_exists, name_groups

# ------------------------------------------------------------
# Run edges from stop_times (consecutive pairs in same trip)
# ------------------------------------------------------------
def build_run_edges(stop_times_path):
    rows = []
    with open(stop_times_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            tid = (row.get("trip_id") or "").strip()
            sid = (row.get("stop_id") or "").strip()
            if not tid or not sid:
                continue
            try:
                seq = int((row.get("stop_sequence") or "").strip())
            except Exception:
                continue
            arr = parse_time_to_seconds(row.get("arrival_time"))
            dep = parse_time_to_seconds(row.get("departure_time"))
            rows.append((tid, seq, sid, arr, dep))
    rows.sort(key=lambda x: (x[0], x[1]))

    edge_min = {}  # (a,b) -> seconds
    prev = None
    prev_tid = None

    for row in rows:
        tid, seq, sid, arr, dep = row
        if tid != prev_tid:
            prev = row
            prev_tid = tid
            continue
        _, pseq, psid, parr, pdep = prev
        if psid != sid:
            depart_t = pdep if pdep is not None else parr
            arrive_t = arr if arr is not None else dep
            if depart_t is not None and arrive_t is not None:
                delta = arrive_t - depart_t
                if delta > 0:
                    key = (psid, sid)
                    if key not in edge_min or delta < edge_min[key]:
                        edge_min[key] = delta
        prev = row

    return edge_min

# ------------------------------------------------------------
# Zero-time station grouping via hubs
# ------------------------------------------------------------
class UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.rank = {x: 0 for x in items}
    def find(self, x):
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

def build_station_hubs(platforms, station_children, name_groups):
    """
    Build union-find groups where:
      - any platforms with the same parent_station are in one group
      - any platforms with the same stop_name are in one group
    Returns:
      hub_of_platform: platform_id -> hub_id (string)
      hub_members: hub_id -> [platform_id,...]
    """
    p_ids = list(platforms.keys())
    uf = UnionFind(p_ids)

    # union by parent_station
    for parent, kids in station_children.items():
        for i in range(1, len(kids)):
            uf.union(kids[0], kids[i])

    # union by stop_name
    for name, kids in name_groups.items():
        for i in range(1, len(kids)):
            uf.union(kids[0], kids[i])

    # collect groups
    groups = defaultdict(list)
    for pid in p_ids:
        groups[uf.find(pid)].append(pid)

    hub_of_platform = {}
    hub_members = {}
    for idx, (root, members) in enumerate(groups.items()):
        hub_id = f"@HUB:{idx}"  # unique internal node ID, not a real stop_id
        hub_members[hub_id] = sorted(members)
        for pid in members:
            hub_of_platform[pid] = hub_id

    return hub_of_platform, hub_members

# ------------------------------------------------------------
# Optional station-level links (parent_station ↔ parent_station, bidirectional)
# CSV header: from_parent_station,to_parent_station,transfer_time_seconds
# ------------------------------------------------------------
def load_station_links(csv_path):
    links = []  # (from_parent, to_parent, time_s)
    if not csv_path:
        return links
    if not os.path.exists(csv_path):
        sys.stderr.write(f"Warning: station links file not found: {csv_path}\n")
        return links
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            a = (row.get("from_parent_station") or "").strip()
            b = (row.get("to_parent_station") or "").strip()
            t = (row.get("transfer_time_seconds") or "").strip()
            if not a or not b or not t:
                continue
            try:
                w = int(t)
            except Exception:
                continue
            if w <= 0:
                continue
            links.append((a, b, w))
    return links

# ------------------------------------------------------------
# Build adjacency with: run edges + 0s to/from hubs + station-level hub↔hub edges
# ------------------------------------------------------------
def build_adjacency(platforms, run_edges, hub_of_platform, hub_members, station_links, station_children):
    """
    Returns adjacency dict: node_id -> list[(neighbor_id, weight)]
    Nodes include platform stop_ids and hub_ids.
    """
    adj = defaultdict(list)

    # 1) Run edges (platform -> platform)
    for (a, b), w in run_edges.items():
        if a in platforms and b in platforms:
            adj[a].append((b, w))

    # 2) Zero-time edges platform <-> hub (bidirectional)
    for hub_id, members in hub_members.items():
        for pid in members:
            adj[pid].append((hub_id, 0))
            adj[hub_id].append((pid, 0))

    # 3) Station-level links: connect hubs of the two stations (bidirectional)
    #    Map parent_station id -> one representative platform (if any), then to hub
    parent_to_any_platform = {p: kids[0] for p, kids in station_children.items() if kids}
    for a_parent, b_parent, w in station_links:
        a_pid = parent_to_any_platform.get(a_parent)
        b_pid = parent_to_any_platform.get(b_parent)
        if not a_pid or not b_pid:
            # If either station lacks platforms in our model, skip
            continue
        ha = hub_of_platform.get(a_pid)
        hb = hub_of_platform.get(b_pid)
        if not ha or not hb or ha == hb:
            # Same hub already (same-name or same-parent merged), or missing; skip
            continue
        adj[ha].append((hb, w))
        adj[hb].append((ha, w))

    # sort neighbors for stability (optional)
    for k in adj:
        adj[k].sort(key=lambda t: t[0])
    return adj

# ------------------------------------------------------------
# Dijkstra (single-source)
# ------------------------------------------------------------
def dijkstra_from(src, adj):
    dist = {src: 0}
    pq = [(0, src)]
    visited = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        for v, w in adj.get(u, []):
            nd = d + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python3 build_all_pairs_zero_transfer_stations.py <path/to/stops.txt> <path/to/stop_times.txt> [station_links.csv]",
              file=sys.stderr)
        sys.exit(1)

    stops_path = sys.argv[1]
    stop_times_path = sys.argv[2]
    station_links_csv = sys.argv[3] if len(sys.argv) == 4 else None

    if not os.path.exists(stops_path):
        print(f"stops.txt not found at {stops_path}", file=sys.stderr); sys.exit(1)
    if not os.path.exists(stop_times_path):
        print(f"stop_times.txt not found at {stop_times_path}", file=sys.stderr); sys.exit(1)

    # 1) Load stops & group platforms
    platforms, station_children, station_exists, name_groups = read_stops(stops_path)
    platform_ids = sorted(platforms.keys())

    # 2) Build zero-time station hubs (same parent OR same name)
    hub_of_platform, hub_members = build_station_hubs(platforms, station_children, name_groups)

    # 3) Run edges from schedule
    run_edges = build_run_edges(stop_times_path)

    # 4) Optional station-level in-fare links (between parent stations)
    station_links = load_station_links(station_links_csv)

    # 5) Build adjacency
    adj = build_adjacency(platforms, run_edges, hub_of_platform, hub_members, station_links, station_children)

    # 6) Output CSV header (exactly as requested)
    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow([
        "from_stop_id","from_stop_name","from_stop_lat","from_stop_lon",
        "to_stop_id","to_stop_name","from_parent_station",
        "to_stop_lat","to_stop_lon","to_parent_station",
        "min_travel_time_seconds"
    ])

    # 7) All-pairs Dijkstra over (platforms + hubs), but only output platform→platform rows
    for src in platform_ids:
        s = platforms[src]
        dist = dijkstra_from(src, adj)
        for dst, secs in dist.items():
            if dst == src:
                continue
            if dst not in platforms:
                continue  # don't output hub destinations
            t = platforms[dst]
            out.writerow([
                src, s["name"], s["lat"], s["lon"],
                dst, t["name"], s["parent_station"],
                t["lat"], t["lon"], t["parent_station"],
                int(secs)
            ])

if __name__ == "__main__":
    main()
