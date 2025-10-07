import sqlite3
import networkx as nx

# Connect to database
conn = sqlite3.connect('subway.db')
conn.row_factory = sqlite3.Row

# Fetch node and edge info
with conn:
    cursor = conn.execute("SELECT stop_id FROM node")
    stop_ids = [row['stop_id'] for row in cursor.fetchall()]

    cursor = conn.execute('''
                          SELECT src_stop_id, dst_stop_id, weight_s 
                          FROM edge
                          INNER JOIN node
                          ON edge.dst_stop_id = node.stop_id
                          WHERE node.is_rep
                          '''
                          )
    edges = [(row['src_stop_id'], row['dst_stop_id'], row['weight_s']) for row in cursor.fetchall()]

# Build directed graph
G = nx.DiGraph()
G.add_nodes_from(stop_ids)
for src, dst, wt in edges:
    G.add_edge(src, dst, weight=wt)

# Prepare to collect heuristics
heuristics = []
for src in stop_ids:
    # Dijkstra's single-source shortest paths
    lengths = nx.single_source_dijkstra_path_length(G, src, weight='weight')
    for dst, min_time in lengths.items():
        if src != dst:  # Skip self
            heuristics.append((src, dst, min_time))

# Save to heuristics table
with conn:
    conn.execute("DELETE FROM heuristic")  # Optionally clear existing contents
    conn.executemany(
        "INSERT OR REPLACE INTO heuristic (src_stop_id, dst_stop_id, min_time_s) VALUES (?, ?, ?)",
        heuristics
    )

print(f"Inserted {len(heuristics)} all-pairs paths into the heuristic table.")
