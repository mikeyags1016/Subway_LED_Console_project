#!/usr/bin/env python3
import sqlite3
from collections import defaultdict
import heapq
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
from nyct_gtfs import NYCTFeed


class SubwayNetwork:
    """
    A class representing the NYC subway network as a graph with live updates.
    Loads initial network from SQLite database and updates edge weights in memory
    based on MTA GTFS-RT feed data.
    """
    
    def __init__(self, db_path: str = 'subway.db', edge_timeout_seconds: int = 1800):
        """
        Initialize the subway network by loading from database.
        
        Args:
            db_path: Path to the SQLite database containing network data
            edge_timeout_seconds: Time in seconds before considering an edge inactive (default 30 min)
        """
        self.db_path = db_path
        self.nodes = {}
        self.edges = defaultdict(list)
        self.heuristics = {}
        self.live_updates_timestamp = None
        self.edge_timeout_seconds = edge_timeout_seconds
        
        # Track when each edge was last seen
        self.edge_last_seen = {}  # (from, to) -> timestamp
        self.edge_update_history = defaultdict(list)  # (from, to) -> [(timestamp, weight)]
        
        # Define line groupings for MTA API
        self.feed_to_lines = {
            "ACE": ["A", "C", "E"],
            "BDFM": ["B", "D", "F", "M"],
            "NQRW": ["N", "Q", "R", "W"],
            "JZ": ["J", "Z"],
            "L": ["L"],
            "G": ["G"],
            "1234567": ["1", "2", "3", "4", "5", "6", "7"]
        }
        
        # Load initial network from database
        self._load_network_from_db()
        print(f"✅ Loaded network: {len(self.nodes)} nodes, {sum(len(e) for e in self.edges.values())} edges")
    
    def _load_network_from_db(self):
        """Load nodes, edges, and heuristics from the SQLite database."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        
        try:
            # Load nodes
            node_rows = con.execute('SELECT * FROM node').fetchall()
            self.nodes = {row['stop_id']: dict(row) for row in node_rows}
            
            # Load edges
            edge_rows = con.execute('SELECT * FROM edge').fetchall()
            self.edges = defaultdict(list)
            for row in edge_rows:
                self.edges[row['src_stop_id']].append({
                    'target': row['dst_stop_id'],
                    'weight': row['weight_s'],
                    'edge_type': row['edge_type'],
                    'original_weight': row['weight_s']  # Store original weight
                })
            
            # Load heuristics
            heuristic_rows = con.execute('SELECT * FROM heuristic').fetchall()
            self.heuristics = {
                (row['src_stop_id'], row['dst_stop_id']): row['min_time_s']
                for row in heuristic_rows
            }
        finally:
            con.close()
    
    def update_from_live_feeds(self, verbose: bool = True, remove_inactive: bool = False) -> Dict[str, int]:
        """
        Update edge weights based on live MTA GTFS-RT feeds.
        
        Args:
            verbose: If True, print update progress
            remove_inactive: If True, remove edges not seen recently (use with caution!)
            
        Returns:
            Dictionary with update statistics
        """
        from datetime import datetime
        current_time = datetime.now()
        
        stats = {
            'edges_updated': 0,
            'edges_removed': 0,
            'edges_stale': 0,
            'lines_processed': 0,
            'lines_failed': 0
        }
        
        # Track which edges we've seen in this update
        edges_seen_now = set()
        
        # Flatten all lines to process
        all_lines = [line for lines_group in self.feed_to_lines.values() 
                     for line in lines_group]
        
        if verbose:
            print(f"🔄 Fetching live updates for {len(all_lines)} subway lines...")
        
        for line in all_lines:
            try:
                if verbose:
                    print(f"  Processing line {line}...", end=" ")
                
                feed = NYCTFeed(line)
                stats['lines_processed'] += 1
                
                # Process each trip
                last_seen = {}
                for trip in feed.trips:
                    trip_id = trip.trip_id
                    
                    for stu in trip.stop_time_updates:
                        if not stu.arrival:
                            continue
                        
                        stop_id = stu.stop_id
                        arrival = stu.arrival.timestamp()
                        
                        if trip_id in last_seen:
                            prev_stop, prev_arrival = last_seen[trip_id]
                            if prev_stop != stop_id and arrival > prev_arrival:
                                travel_time = int(arrival - prev_arrival)
                                
                                # Update edge weight and tracking
                                edge_key = (prev_stop, stop_id)
                                self._update_edge_weight(prev_stop, stop_id, travel_time)
                                
                                # Track when we saw this edge
                                self.edge_last_seen[edge_key] = current_time
                                self.edge_update_history[edge_key].append((current_time, travel_time))
                                
                                # Keep history limited to last 100 updates
                                if len(self.edge_update_history[edge_key]) > 100:
                                    self.edge_update_history[edge_key] = self.edge_update_history[edge_key][-100:]
                                
                                edges_seen_now.add(edge_key)
                                stats['edges_updated'] += 1
                        
                        last_seen[trip_id] = (stop_id, arrival)
                
                if verbose:
                    print("✓")
                    
            except Exception as e:
                stats['lines_failed'] += 1
                if verbose:
                    print(f"✗ Failed: {e}")
        
        # Optionally remove inactive edges (based on timeout, not just current visibility)
        if remove_inactive:
            stats['edges_removed'] = self._remove_stale_edges(current_time)
        
        # Count stale edges (informational)
        for source, edges in self.edges.items():
            for edge in edges:
                if edge['edge_type'] == 'run':
                    edge_key = (source, edge['target'])
                    if edge_key in self.edge_last_seen:
                        time_since_update = (current_time - self.edge_last_seen[edge_key]).total_seconds()
                        if time_since_update > self.edge_timeout_seconds:
                            stats['edges_stale'] += 1
        
        self.live_updates_timestamp = current_time
        
        if verbose:
            print(f"\n📊 Update complete:")
            print(f"   - Lines processed: {stats['lines_processed']}/{len(all_lines)}")
            print(f"   - Edges updated: {stats['edges_updated']}")
            print(f"   - Edges stale (>{self.edge_timeout_seconds}s): {stats['edges_stale']}")
            if remove_inactive:
                print(f"   - Edges removed: {stats['edges_removed']}")
            print(f"   - Last updated: {self.live_updates_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return stats
    
    def _update_edge_weight(self, from_stop: str, to_stop: str, new_weight: int):
        """Update the weight of a specific edge if it exists."""
        if from_stop in self.edges:
            for edge in self.edges[from_stop]:
                if edge['target'] == to_stop and edge['edge_type'] == 'run':
                    edge['weight'] = new_weight
                    break
    
    def _remove_stale_edges(self, current_time) -> int:
        """
        Remove edges that haven't been seen within the timeout period.
        Only removes 'run' type edges, preserves transfers.
        
        Returns:
            Number of edges removed
        """
        from datetime import datetime
        removed_count = 0
        
        for source in list(self.edges.keys()):
            original_edges = self.edges[source]
            updated_edges = []
            
            for edge in original_edges:
                # Keep all non-run edges (transfers, etc.)
                if edge['edge_type'] != 'run':
                    updated_edges.append(edge)
                else:
                    edge_key = (source, edge['target'])
                    # Keep edge if we've seen it within timeout period
                    if edge_key in self.edge_last_seen:
                        time_since_update = (current_time - self.edge_last_seen[edge_key]).total_seconds()
                        if time_since_update <= self.edge_timeout_seconds:
                            updated_edges.append(edge)
                        else:
                            removed_count += 1
                    else:
                        # Never seen in live updates - keep it (assume baseline is valid)
                        updated_edges.append(edge)
            
            if updated_edges:
                self.edges[source] = updated_edges
            else:
                del self.edges[source]
        
        return removed_count
    
    def get_edge_status(self, from_stop: str, to_stop: str) -> Dict:
        """
        Get detailed status information about a specific edge.
        
        Args:
            from_stop: Source stop ID
            to_stop: Target stop ID
            
        Returns:
            Dictionary with edge status information
        """
        from datetime import datetime
        
        edge_key = (from_stop, to_stop)
        status = {
            'exists': False,
            'current_weight': None,
            'last_seen': None,
            'time_since_update': None,
            'is_stale': False,
            'update_count': 0,
            'recent_weights': []
        }
        
        # Check if edge exists
        if from_stop in self.edges:
            for edge in self.edges[from_stop]:
                if edge['target'] == to_stop:
                    status['exists'] = True
                    status['current_weight'] = edge['weight']
                    status['original_weight'] = edge.get('original_weight')
                    break
        
        # Add tracking information
        if edge_key in self.edge_last_seen:
            status['last_seen'] = self.edge_last_seen[edge_key].isoformat()
            time_since = (datetime.now() - self.edge_last_seen[edge_key]).total_seconds()
            status['time_since_update'] = time_since
            status['is_stale'] = time_since > self.edge_timeout_seconds
        
        # Add update history
        if edge_key in self.edge_update_history:
            history = self.edge_update_history[edge_key]
            status['update_count'] = len(history)
            # Get last 5 updates
            status['recent_weights'] = [
                {'time': t.isoformat(), 'weight': w} 
                for t, w in history[-5:]
            ]
        
        return status
    
    def reset_to_baseline(self):
        """Reset the network to the baseline state from the database."""
        self.edges.clear()
        self.nodes.clear()
        self.heuristics.clear()
        self._load_network_from_db()
        self.live_updates_timestamp = None
        print("🔄 Network reset to baseline database state")
    
    def a_star(self, start: str, goal: str) -> Tuple[Optional[List[str]], float]:
        """
        Find the shortest path between two stops using A* algorithm.
        
        Args:
            start: Starting stop ID (e.g., 'D29N')
            goal: Goal stop ID (e.g., 'G16N')
            
        Returns:
            Tuple of (path, total_time) where path is a list of stop IDs
            or (None, inf) if no path exists
        """
        if start not in self.nodes:
            print(f"⚠️ Start node '{start}' not found in network")
            return None, float('inf')
        
        if goal not in self.nodes:
            print(f"⚠️ Goal node '{goal}' not found in network")
            return None, float('inf')
        
        frontier = []
        heapq.heappush(frontier, (self.heuristics.get((start, goal), 0), 0, start, [start]))
        explored = set()
        
        while frontier:
            f_score, g_score, current, path = heapq.heappop(frontier)
            
            if current == goal:
                return path, g_score
            
            if current in explored:
                continue
                
            explored.add(current)
            
            for edge in self.edges.get(current, []):
                neighbor = edge['target']
                cost = edge['weight']
                new_g = g_score + cost
                h_val = self.heuristics.get((neighbor, goal), 0)
                
                heapq.heappush(
                    frontier,
                    (new_g + h_val, new_g, neighbor, path + [neighbor])
                )
        
        return None, float('inf')
    
    def find_route(self, start: str, goal: str, use_live_data: bool = True, 
                   remove_stale: bool = False) -> Dict:
        """
        Find a route between two stops with optional live data updates.
        
        Args:
            start: Starting stop ID
            goal: Goal stop ID
            use_live_data: If True, update with live data before routing
            remove_stale: If True and use_live_data is True, remove stale edges
            
        Returns:
            Dictionary containing route information
        """
        if use_live_data:
            print("📡 Fetching live updates before routing...")
            self.update_from_live_feeds(verbose=False, remove_inactive=remove_stale)
        
        path, total_time = self.a_star(start, goal)
        
        result = {
            'path': path,
            'total_time_seconds': total_time if path else None,
            'total_time_minutes': round(total_time / 60, 1) if path else None,
            'num_stops': len(path) if path else 0,
            'using_live_data': use_live_data,
            'last_update': self.live_updates_timestamp.isoformat() if self.live_updates_timestamp else None
        }
        
        if path:
            # Get stop names for the path
            result['stop_names'] = [
                self.nodes[stop_id]['stop_name'] if stop_id in self.nodes else stop_id
                for stop_id in path
            ]
        
        return result
    
    def get_network_stats(self) -> Dict:
        """Get current network statistics."""
        total_edges = sum(len(edges) for edges in self.edges.values())
        edge_types = defaultdict(int)
        
        for edges in self.edges.values():
            for edge in edges:
                edge_types[edge['edge_type']] += 1
        
        return {
            'num_nodes': len(self.nodes),
            'num_edges': total_edges,
            'edge_types': dict(edge_types),
            'num_heuristics': len(self.heuristics),
            'last_live_update': self.live_updates_timestamp.isoformat() if self.live_updates_timestamp else None
        }
    
    def get_disrupted_edges(self) -> List[Tuple[str, str]]:
        """
        Get a list of edges that have been removed due to service disruptions.
        Compares current state with baseline database.
        
        Returns:
            List of (source, target) tuples for disrupted edges
        """
        # Load baseline edges from database
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        
        baseline_edges = set()
        edge_rows = con.execute("SELECT src_stop_id, dst_stop_id FROM edge WHERE edge_type = 'run'").fetchall()
        for row in edge_rows:
            baseline_edges.add((row['src_stop_id'], row['dst_stop_id']))
        con.close()
        
        # Current edges in memory
        current_edges = set()
        for source, edges in self.edges.items():
            for edge in edges:
                if edge['edge_type'] == 'run':
                    current_edges.add((source, edge['target']))
        
        # Find disrupted edges
        disrupted = list(baseline_edges - current_edges)
        
        return disrupted


# Example usage
if __name__ == "__main__":
    # Initialize network
    network = SubwayNetwork('subway.db')
    
    # Get network stats
    print("\n📊 Initial network stats:")
    stats = network.get_network_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Find route with baseline data
    print("\n🗺️ Finding route (baseline data)...")
    result = network.find_route('D29N', 'G16N', use_live_data=False)
    if result['path']:
        print(f"   Path: {' → '.join(result['path'][:5])}... ({result['num_stops']} stops)")
        print(f"   Time: {result['total_time_minutes']} minutes")
    
    # Find route with live data
    print("\n🗺️ Finding route (with live updates)...")
    result = network.find_route('D29N', 'G16N', use_live_data=True)
    if result['path']:
        print(f"   Path: {' → '.join(result['path'][:5])}... ({result['num_stops']} stops)")
        print(f"   Time: {result['total_time_minutes']} minutes")
        print(f"   Last update: {result['last_update']}")
    
    # Check for disruptions
    disrupted = network.get_disrupted_edges()
    if disrupted:
        print(f"\n⚠️ Found {len(disrupted)} disrupted edges")
        print(f"   Examples: {disrupted[:5]}")