#!/usr/bin/env python3
"""
Main Raspberry Pi Service for NYC Subway LED Display

This script:
1. Loads the SubwayNetwork and updates edges every 60 seconds in a background thread.
2. Accepts start/goal stop IDs from stdin and computes A* path.
3. Enriches the path with run/index info from stop_lookup.json.
4. Sends LED commands over UART to ESP32 for FastLED display.

Usage:
  python3 network/main_pi_service.py --port /dev/serial0 --baud 115200 --db network/subway.db

Protocol:
  - Sends newline-delimited commands to ESP32:
    <run>,<index>,<color>\n
    where run is the line identifier, index is the LED position, color is RGB hex.
  - Example: "3,42,00FF00\n" -> turn LED at run=3, index=42 green.

Interactive mode:
  - Enter start and goal stop IDs separated by space: "257N 235N"
  - The service will compute the path and send LED commands to the ESP32.
  - Press Ctrl-C to quit.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import signal
from pathlib import Path
from typing import Dict, List, Optional

try:
    import serial
except ImportError:
    serial = None

from network.SubwayNetwork import SubwayNetwork


# Global flag for graceful shutdown
shutdown_flag = threading.Event()


def load_stop_lookup(json_path: str) -> Dict:
    """Load stop_lookup.json into memory."""
    with open(json_path, 'r') as f:
        return json.load(f)


def update_edges_periodically(network: SubwayNetwork, interval_sec: int = 60):
    """Background thread that updates network edges every `interval_sec` seconds."""
    print(f"🔄 Edge updater thread started (interval: {interval_sec}s)")
    while not shutdown_flag.is_set():
        try:
            network.update_from_live_feeds(verbose=False, remove_inactive=False)
            print(f"✅ Edges updated at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"⚠️ Edge update failed: {e}")
        
        # Sleep in small increments to allow responsive shutdown
        for _ in range(interval_sec):
            if shutdown_flag.is_set():
                break
            time.sleep(1)
    
    print("🛑 Edge updater thread stopped")


def compute_path(network: SubwayNetwork, start: str, goal: str) -> Optional[Dict]:
    """Compute A* path from start to goal using SubwayNetwork.
    
    Returns the full result dict from find_route including path, delays, etc.
    """
    try:
        result = network.find_route(start, goal, use_live_data=False)
        path = result.get('path')
        if path:
            print(f"✅ Path found: {len(path)} stops, {result.get('total_time_minutes', 0):.1f} min")
            return result
        else:
            print("❌ No path found")
            return None
    except Exception as e:
        print(f"❌ Routing error: {e}")
        return None


def enrich_path_with_metadata(path: List[str], stop_lookup: Dict) -> List[Dict]:
    """
    Enrich each stop_id in the path with run and index from stop_lookup.json.
    
    Returns:
        List of dicts with keys: stop_id, run, index, name
    """
    enriched = []
    for stop_id in path:
        entry = stop_lookup.get(stop_id)
        if not entry:
            print(f"⚠️ Warning: stop_id '{stop_id}' not found in stop_lookup.json, skipping")
            continue
        
        enriched.append({
            'stop_id': stop_id,
            'run': entry.get('run'),
            'index': entry.get('index'),
            'name': entry.get('name', 'Unknown')
        })
    
    return enriched


def send_led_commands(ser, enriched_path: List[Dict], delayed_segments: List = None):
    """
    Send LED commands to ESP32 over serial.
    
    Protocol:
      <run>,<index>,<color>\n
    
    Args:
        ser: Serial port object
        enriched_path: List of dicts with run/index keys and stop_id
        delayed_segments: List of (src_stop_id, dst_stop_id) tuples for delayed segments
    """
    if ser is None:
        print("⚠️ Serial port not available, commands will be printed instead:")
    
    if delayed_segments is None:
        delayed_segments = []
    
    # Convert delayed_segments to a set for faster lookup
    delayed_set = set(delayed_segments)
    
    for i, item in enumerate(enriched_path):
        run = item.get('run')
        index = item.get('index')
        
        if run is None or index is None:
            print(f"⚠️ Skipping {item['stop_id']} (missing run or index)")
            continue
        
        # Check if the segment leading to this stop is delayed
        is_delayed = False
        if i > 0:
            prev_stop_id = enriched_path[i-1]['stop_id']
            curr_stop_id = item['stop_id']
            is_delayed = (prev_stop_id, curr_stop_id) in delayed_set
        
        # Use amber (FFA500) for delayed segments, green (00FF00) for normal
        color = "FFA500" if is_delayed else "00FF00"
        status = "⚠️ DELAYED" if is_delayed else "✓"
        
        # Format command: run,index,color
        cmd = f"{run},{index},{color}\n"
        
        if ser:
            try:
                ser.write(cmd.encode('utf-8'))
                print(f"TX: {cmd.strip()} {status} ({item['name']})")
            except Exception as e:
                print(f"❌ Serial write error: {e}")
        else:
            print(f"[DRY-RUN] {cmd.strip()} {status} ({item['name']})")
    
    # Send a terminator or "done" signal (optional, adapt to your ESP32 protocol)
    if ser:
        try:
            ser.write(b"END\n")
            print("TX: END")
        except Exception:
            pass


def signal_handler(sig, frame):
    """Handle Ctrl-C gracefully."""
    print("\n🛑 Shutting down...")
    shutdown_flag.set()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Raspberry Pi NYC Subway LED Service")
    parser.add_argument('--port', default='/dev/serial0', help='Serial device (e.g., /dev/serial0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    parser.add_argument('--db', default='subway.db', help='Path to subway.db')
    parser.add_argument('--lookup', default='stop_lookup.json', help='Path to stop_lookup.json')
    parser.add_argument('--update-interval', type=int, default=60, help='Edge update interval (seconds)')
    parser.add_argument('--no-serial', action='store_true', help='Run without serial (dry-run mode)')
    args = parser.parse_args(argv)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load network
    print(f"📡 Loading network from {args.db}...")
    network = SubwayNetwork(args.db)
    
    # Load stop lookup
    print(f"📖 Loading stop lookup from {args.lookup}...")
    stop_lookup = load_stop_lookup(args.lookup)
    print(f"✅ Loaded {len(stop_lookup)} stop entries")
    
    # Open serial port
    ser = None
    if not args.no_serial:
        if serial is None:
            print("⚠️ pyserial not installed. Install with: pip install pyserial")
            print("Running in dry-run mode (no serial output)")
        else:
            try:
                ser = serial.Serial(args.port, args.baud, timeout=1)
                print(f"✅ Serial port {args.port} opened at {args.baud} baud")
            except Exception as e:
                print(f"⚠️ Could not open serial port {args.port}: {e}")
                print("Running in dry-run mode (no serial output)")
    else:
        print("🔕 Serial output disabled (dry-run mode)")
    
    # Start background edge updater thread
    updater_thread = threading.Thread(
        target=update_edges_periodically,
        args=(network, args.update_interval),
        daemon=True
    )
    updater_thread.start()
    
    # Wait a moment for the first update to complete
    time.sleep(2)
    
    print("\n" + "="*60)
    print("🚇 NYC Subway LED Service Ready")
    print("="*60)
    print("Enter start and goal stop IDs separated by space (e.g., '257N 235N')")
    print("Press Ctrl-C to quit")
    print("="*60 + "\n")
    
    # Main interactive loop
    try:
        while not shutdown_flag.is_set():
            try:
                # Read input with a timeout check for shutdown
                print("> ", end='', flush=True)
                
                # Use select or threading to allow responsive shutdown
                # For simplicity, we'll use input() with a short timeout via stdin
                import select
                if select.select([sys.stdin], [], [], 1.0)[0]:
                    line = sys.stdin.readline().strip()
                else:
                    continue  # timeout, check shutdown flag again
                
                if not line:
                    continue
                
                # Parse input
                parts = line.split()
                if len(parts) != 2:
                    print("❌ Invalid input. Please enter: <start_id> <goal_id>")
                    continue
                
                start_id, goal_id = parts
                print(f"\n🔍 Computing path: {start_id} → {goal_id}")
                
                # Compute path
                path = compute_path(network, start_id, goal_id)
                if not path:
                    continue
                
                # Extract path and delayed segments from result
                path_list = path.get('path', [])
                delayed_segments = path.get('delayed_segments', [])
                has_delays = path.get('has_delays', False)
                
                if not path_list:
                    print("❌ Empty path returned")
                    continue
                
                # Show delay warning
                if has_delays:
                    print(f"⚠️  Route includes {len(delayed_segments)} delayed segment(s)")
                
                # Enrich with metadata
                enriched = enrich_path_with_metadata(path_list, stop_lookup)
                if not enriched:
                    print("❌ No valid stops found in path after enrichment")
                    continue
                
                print(f"📍 Enriched path: {len(enriched)} stops")
                
                # Send LED commands with delay information
                print("💡 Sending LED commands to ESP32...")
                send_led_commands(ser, enriched, delayed_segments=delayed_segments)
                print("✅ Done\n")
                
            except EOFError:
                # stdin closed
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        shutdown_flag.set()
        updater_thread.join(timeout=5)
        
        if ser:
            try:
                ser.close()
                print("✅ Serial port closed")
            except Exception:
                pass
        
        print("👋 Goodbye!")


if __name__ == '__main__':
    main()
