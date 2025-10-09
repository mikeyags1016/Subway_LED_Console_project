import pandas as pd
import sqlite3
from collections import defaultdict

def parse_gtfs_ids(value):
    return [x.strip() for x in str(value).split(";") if x.strip()]

def main(complexes_path, stop_times_path, db_path, transfer_time=300, transfer_walk=0.1):
    complexes_df = pd.read_csv(complexes_path)
    platform_col = next(c for c in complexes_df.columns if 'GTFS Stop IDs' in c)
    name_col = next(c for c in complexes_df.columns if 'Display Name' in c)
    lat_col = next((c for c in complexes_df.columns if 'Lat' in c), None)
    lon_col = next((c for c in complexes_df.columns if 'Long' in c), None)
    node_records = {}
    complexes = []
    for idx, row in complexes_df.iterrows():
        raw_ids = parse_gtfs_ids(row[platform_col])
        expanded_ids = []
        for base_id in raw_ids:
            expanded_ids.extend([f"{base_id}N", f"{base_id}S"])
        rep = min(expanded_ids)
        complex_record = {
            'complex_id': idx,
            'stop_name': str(row[name_col]),
            'lat': float(row[lat_col]) if lat_col else None,
            'lon': float(row[lon_col]) if lon_col else None,
            'platforms': expanded_ids,
            'rep': rep
        }
        complexes.append(complex_record)
        for pid in expanded_ids:
            node_records[pid] = (pid, complex_record['stop_name'], complex_record['lat'], complex_record['lon'], pid == rep)

    print(f"{len(complexes)} complexes, {len(node_records)} platform nodes prepared.")

    # Hub and spoke intra-station edges: all spokes → rep (0.1), rep → all spokes (300)
    intra_edges = []
    for c in complexes:
        platforms = c['platforms']
        rep = c['rep']
        for plat in platforms:
            if plat != rep:
                intra_edges.append((plat, rep, transfer_walk, "intra_station0"))      # spoke → hub (short transfer)
                intra_edges.append((rep, plat, transfer_time, "intra_station0"))      # hub → spoke (penalty transfer)

    # Parse stop_times and build run edges
    stop_times = pd.read_csv(stop_times_path, dtype=str)
    stop_times['stop_id'] = stop_times['stop_id'].astype(str)
    stop_times['stop_sequence'] = stop_times['stop_sequence'].astype(int)
    found_stop_ids = set()
    for sid in stop_times['stop_id'].unique():
        if sid not in node_records:
            print(f"WARNING: stop_id {sid} in stop_times.txt not found in complexes csv")
            found_stop_ids.add(sid)

    run_edges = defaultdict(list)
    for trip_id, group in stop_times.groupby('trip_id'):
        group = group.sort_values('stop_sequence')
        prev_row = None
        for _, row in group.iterrows():
            src, dst = row['stop_id'], None
            if prev_row is not None:
                src, dst = prev_row['stop_id'], row['stop_id']
                if src in node_records and dst in node_records and src != dst:
                    try:
                        h1, m1, s1 = map(int, str(prev_row['departure_time']).split(':'))
                        h2, m2, s2 = map(int, str(row['arrival_time']).split(':'))
                        dep_t = h1 * 3600 + m1 * 60 + s1
                        arr_t = h2 * 3600 + m2 * 60 + s2
                        delta = arr_t - dep_t
                    except Exception:
                        continue
                    if delta > 0:
                        run_edges[(src, dst)].append(delta)
            prev_row = row
    run_records = [(src, dst, min(times), "run") for (src, dst), times in run_edges.items()]

    print(f"{len(run_records)} run edges, {len(intra_edges)} intra-station/transfer edges to be inserted.")

    # Write nodes and edges to DB
    con = sqlite3.connect(db_path)
    with con:
        con.execute("DELETE FROM node")
        con.execute("DELETE FROM edge")
        con.executemany("INSERT INTO node (stop_id, stop_name, stop_lat, stop_lon, is_rep) VALUES (?, ?, ?, ?, ?)", list(node_records.values()))
        con.executemany("INSERT INTO edge (src_stop_id, dst_stop_id, weight_s, edge_type) VALUES (?, ?, ?, ?)", run_records + intra_edges)

    print(f"Inserted {len(node_records)} nodes and {len(run_records) + len(intra_edges)} edges.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--complexes', required=True)
    parser.add_argument('--stop_times', required=True)
    parser.add_argument('--db', required=True)
    parser.add_argument('--transfer_time', type=int, default=300)
    parser.add_argument('--transfer_walk', type=float, default=0.1)
    args = parser.parse_args()
    main(args.complexes, args.stop_times, args.db, args.transfer_time, args.transfer_walk)
