# Unix Socket Setup for UI ↔ Service Communication

## Architecture

The system now uses **two separate processes** communicating via Unix socket:

1. **`main_pi_service.py`** — Background routing service
   - Loads SubwayNetwork once at startup
   - Updates edges every 60 seconds in background
   - Listens on Unix socket `/tmp/subway_service.sock`
   - Sends LED commands to ESP32 via serial

2. **`run_ui.py`** — Kivy UI
   - Displays map and autocomplete inputs
   - Sends routing requests to service via socket
   - Receives path + delay info back
   - Displays route on map with color-coded delays

## Performance Benefits

- **~100x faster UI response**: 0.1 sec vs 7-13 sec
- **No UI freezing**: Routing happens in background service
- **Always fresh data**: Edge updates run continuously
- **Can restart UI** without losing network state

## How to Run

### Terminal 1: Start the Service (runs continuously)

```bash
cd /home/vandriacco/repos/cpeg_capstone/Subway_LED_Console_project

# Start the background service
python3 network/main_pi_service.py \
  --port /dev/serial0 \
  --baud 115200 \
  --db network/subway.db \
  --lookup network/stop_lookup.json \
  --update-interval 60
```

**Output:**
```
📡 Loading network from network/subway.db...
✅ Loaded network: 1234 nodes, 5678 edges
📖 Loading stop lookup from network/stop_lookup.json...
✅ Loaded 2468 stop entries
✅ Serial port /dev/serial0 opened at 115200 baud
🔄 Edge updater thread started (interval: 60s)
============================================================
🚇 NYC Subway LED Service Ready
============================================================
Listening on Unix socket: /tmp/subway_service.sock
UI can now connect and send routing requests
Press Ctrl-C to quit
============================================================
```

### Terminal 2: Start the UI

```bash
# In a separate terminal
python3 ui/run_ui.py
```

The UI will now connect to the service when "Confirm Stops" is clicked.

## Communication Protocol

### Request (UI → Service)
```json
{"start": "257N", "goal": "235N"}
```

### Response (Service → UI)
```json
{
  "status": "ok",
  "path": ["257N", "256N", "255N", ...],
  "total_time_minutes": 12.5,
  "num_stops": 8,
  "stop_names": ["New Lots Av (3)", "Van Siclen Av (3)", ...],
  "has_delays": true,
  "delayed_segments": [["256N", "255N"], ["254N", "253N"]]
}
```

### Error Response
```json
{
  "status": "error",
  "message": "No path found"
}
```

## LED Display

The service sends commands to ESP32:
- **Green (00FF00)**: Normal service segments
- **Amber (FFA500)**: Delayed service segments

Format: `<run>,<index>,<color>\n`

Example:
```
3,100,00FF00   ✓ New Lots Av (3)
3,101,FFA500   ⚠️ DELAYED Van Siclen Av (3)
3,102,00FF00   ✓ Pennsylvania Av (3)
END
```

## Troubleshooting

### "Could not connect to service"
- Make sure `main_pi_service.py` is running first
- Check socket exists: `ls -l /tmp/subway_service.sock`

### "Service request timed out"
- Service may be busy updating edges (takes ~10 sec)
- Wait a moment and try again

### Service crashes on startup
- Check DB path is correct: `ls network/subway.db`
- Check stop_lookup.json exists: `ls network/stop_lookup.json`
- Check serial port permissions: `ls -l /dev/serial0`

## Auto-Start on Boot (Optional)

Create systemd service `/etc/systemd/system/subway-service.service`:

```ini
[Unit]
Description=NYC Subway LED Routing Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/vandriacco/repos/cpeg_capstone/Subway_LED_Console_project
ExecStart=/usr/bin/python3 network/main_pi_service.py --port /dev/serial0 --db network/subway.db --lookup network/stop_lookup.json
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable subway-service
sudo systemctl start subway-service
sudo systemctl status subway-service
```

## Development

### Testing without serial port
```bash
python3 network/main_pi_service.py --no-serial
```

### Testing with different socket path
```bash
# Service
python3 network/main_pi_service.py --socket /tmp/test.sock

# UI needs manual edit to match socket path (line ~253)
```

### Viewing service logs
```bash
# If using systemd
journalctl -u subway-service -f
```
