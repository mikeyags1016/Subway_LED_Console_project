import sqlite3
import networkx as nx

# Connect to DB
conn = sqlite3.connect("subway.db")
conn.row_factory = sqlite3.Row

# Fetch all platform stop IDs and all rep IDs
stop_ids = [row['stop_id'] for row in conn.execute("SELECT stop_id FROM node")]
rep_ids = [row['stop_id'] for row in conn.execute("SELECT stop_id FROM node WHERE is_rep")]
edges = [(row['src_stop_id'], row['dst_stop_id'], row['weight_s'])
         for row in conn.execute("SELECT src_stop_id, dst_stop_id, weight_s FROM edge")]

# Build graph with all platforms and all edges
G = nx.DiGraph()
G.add_nodes_from(stop_ids)
G.add_weighted_edges_from(edges)

# Compute heursitics for all (rep, rep) pairs using all platforms as intermediates
heuristics = []
unreachable = []
for src in rep_ids:
    lengths = nx.single_source_dijkstra_path_length(G, src, weight='weight')
    for dst in rep_ids:
        if src == dst:
            continue
        if dst in lengths:
            heuristics.append((src, dst, lengths[dst]))
        else:
            unreachable.append((src, dst))

print(f"Coverage: {len(heuristics)}/{len(rep_ids)*(len(rep_ids)-1)} ({100*len(heuristics)/(len(rep_ids)*(len(rep_ids)-1)):.2f}%)")
if unreachable:
    print("Unreachable example pairs:", unreachable[:10])

# Save to DB
with conn:
    conn.execute("DELETE FROM heuristic")
    conn.executemany(
        "INSERT INTO heuristic (src_stop_id, dst_stop_id, min_time_s) VALUES (?, ?, ?)",
        heuristics
    )

print("Heuristic table updated.")
conn.close()
