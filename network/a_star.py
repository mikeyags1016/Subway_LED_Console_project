import sqlite3
import networkx as nx

# Set your source and destination stop_ids
SRC_STOP_ID = 'D29N'   # replace with your actual source
DST_STOP_ID = 'G16N'   # replace with your actual destination

# Connect to db
conn = sqlite3.connect('network/subway.db')
conn.row_factory = sqlite3.Row

# Load nodes (all platforms)
stop_ids = [row['stop_id'] for row in conn.execute('SELECT stop_id FROM node')]

# Load edges (all connections)
edges = [
    (row['src_stop_id'], row['dst_stop_id'], row['weight_s'])
    for row in conn.execute('SELECT src_stop_id, dst_stop_id, weight_s FROM edge')
]

# Build directed graph
G = nx.DiGraph()
G.add_nodes_from(stop_ids)
for src, dst, wt in edges:
    G.add_edge(src, dst, weight=wt)

# Load heuristics table into memory for fast lookup
heuristic_map = {}
for row in conn.execute('SELECT src_stop_id, dst_stop_id, min_time_s FROM heuristic'):
    heuristic_map[(row['src_stop_id'], row['dst_stop_id'])] = row['min_time_s']

# Heuristic function to use for A*
def heuristic(u, v):
    return heuristic_map.get((u, v), 0) # default to 0 if no heuristic available

# Find shortest path using A*
try:
    path = nx.astar_path(G, SRC_STOP_ID, DST_STOP_ID, heuristic=heuristic, weight='weight')
    total_time = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
    print(f"Shortest path from {SRC_STOP_ID} to {DST_STOP_ID}:")
    print(" -> ".join(path))
    print(f"Total travel time (seconds): {total_time}")
except nx.NetworkXNoPath:
    print(f"No path found from {SRC_STOP_ID} to {DST_STOP_ID}")

conn.close()