import sqlite3
from collections import defaultdict
import heapq

def load_graph_from_sqlite(db_path, node_table, edge_table, heuristic_table,
                          node_id_col, edge_source_col, edge_target_col,
                          edge_weight_col, heuristic_from_col,
                          heuristic_goal_col, heuristic_value_col):
    """
    Loads the nodes, edges, and heuristic information from sqlite3 and
    returns them as efficient Python data structures.

    Parameters:
      db_path: Path to the sqlite3 database file.
      node_table: Name of the node table.
      edge_table: Name of the edge table.
      heuristic_table: Name of the heuristic table.
      node_id_col, edge_source_col, edge_target_col, edge_weight_col: Column names for nodes/edges.
      heuristic_from_col, heuristic_goal_col, heuristic_value_col: Column names for heuristics.

    Returns:
      nodes: {node_id: attributes_dict}
      edges: {source_node: [{target, weight, ...}]}
      heuristics: {(from_node, to_node): heuristic_value}
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    # Nodes
    node_rows = con.execute(f'SELECT * FROM {node_table}').fetchall()
    nodes = {row[node_id_col]: dict(row) for row in node_rows}

    # Edges
    edge_rows = con.execute(f'SELECT * FROM {edge_table}').fetchall()
    edges = defaultdict(list)
    for row in edge_rows:
        edges[row[edge_source_col]].append({
            'target': row[edge_target_col],
            'weight': row[edge_weight_col],
            **dict(row)
        })

    # Heuristics
    heuristic_rows = con.execute(f'SELECT * FROM {heuristic_table}').fetchall()
    heuristics = {
        (row[heuristic_from_col], row[heuristic_goal_col]): row[heuristic_value_col]
        for row in heuristic_rows
    }

    con.close()
    return nodes, edges, heuristics

def a_star(start, goal):
    nodes, edges, heuristics = load_graph_from_sqlite(
        'subway.db', 'node', 'edge', 'heuristic', 'stop_id',
        'src_stop_id', 'dst_stop_id', 'weight_s', 
        'src_stop_id', 'dst_stop_id', 'min_time_s'
    )
    
    frontier = []
    heapq.heappush(frontier, (heuristics.get((start, goal), 0), 0, start, [start]))
    explored = set()

    while frontier:
        f_score, g_score, current, path = heapq.heappop(frontier)
        if current == goal:
            return path, g_score
        if current in explored:
            continue
        explored.add(current)
        for edge in edges.get(current, []):
            neighbor = edge['target']
            cost = edge['weight']
            new_g = g_score + cost
            h_val = heuristics.get((neighbor, goal), 0)
            heapq.heappush(
                frontier,
                (new_g + h_val, new_g, neighbor, path + [neighbor])
            )
    return None, float('inf')

path, total_time = a_star(
    start='D29N',
    goal='G16N'
)
print("Best path:", path)
print("Total time:", total_time)