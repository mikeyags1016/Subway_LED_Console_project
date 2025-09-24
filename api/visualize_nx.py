#!/usr/bin/env python3
# visualize_nx.py
import sqlite3, argparse
import networkx as nx
import matplotlib.pyplot as plt

EDGE_TYPES = ("run","intra_station0","station_link")

def load_graph(db_path, include_types=("run",), limit=None):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute("SELECT stop_id, stop_name, stop_lat, stop_lon, is_rep FROM node")
    nodes = {}
    for sid, name, lat, lon, is_rep in cur.fetchall():
        if lat is None or lon is None:  # skip if no coords
            continue
        nodes[sid] = {"name": name, "lat": float(lat), "lon": float(lon), "is_rep": bool(is_rep)}

    q = f"""
      SELECT src_stop_id, dst_stop_id, weight_s, edge_type
      FROM edge
      WHERE edge_type IN ({",".join("?"*len(include_types))})
    """
    params = list(include_types)
    if limit:
        q += " LIMIT ?"
        params.append(limit)
    cur.execute(q, params)
    edges = cur.fetchall()

    con.close()

    G = nx.DiGraph()
    for sid, attrs in nodes.items():
        G.add_node(sid, **attrs)
    for u, v, w, t in edges:
        if u in nodes and v in nodes:
            G.add_edge(u, v, weight=w, edge_type=t)
    return G

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", help="network.db (SQLite)")
    ap.add_argument("--types", default="run,intra_station0,station_link",
                    help="edge types to include, comma-separated")
    ap.add_argument("--limit", type=int, default=None, help="limit edges (for quick draft)")
    ap.add_argument("--out", default="graph.png")
    args = ap.parse_args()

    include = tuple(s.strip() for s in args.types.split(",") if s.strip())
    G = load_graph(args.db, include_types=include, limit=args.limit)

    # positions from lon/lat
    pos = {n: (G.nodes[n]["lon"], G.nodes[n]["lat"]) for n in G.nodes}

    # draw edges by type (thin/light for zero-transfer)
    run_edges = [(u,v) for u,v,d in G.edges(data=True) if d.get("edge_type")=="run"]
    zero_edges = [(u,v) for u,v,d in G.edges(data=True) if d.get("edge_type")=="intra_station0"]
    link_edges = [(u,v) for u,v,d in G.edges(data=True) if d.get("edge_type")=="station_link"]

    plt.figure(figsize=(10,10))
    if zero_edges:
        nx.draw_networkx_edges(G, pos, edgelist=zero_edges, width=0.5, alpha=0.15)
    if link_edges:
        nx.draw_networkx_edges(G, pos, edgelist=link_edges, width=1.5, alpha=0.6)
    if run_edges:
        nx.draw_networkx_edges(G, pos, edgelist=run_edges, width=0.8, alpha=0.5)

    # draw nodes (smaller) and highlight reps a bit bigger
    reps = [n for n,d in G.nodes(data=True) if d.get("is_rep")]
    others = [n for n in G.nodes if n not in reps]
    nx.draw_networkx_nodes(G, pos, nodelist=others, node_size=8, alpha=0.8)
    if reps:
        nx.draw_networkx_nodes(G, pos, nodelist=reps, node_size=20, alpha=0.9)

    plt.axis("equal"); plt.axis("off")
    plt.tight_layout()
    plt.savefig(args.out, dpi=250)
    print(f"Saved {args.out}")

if __name__ == "__main__":
    main()
