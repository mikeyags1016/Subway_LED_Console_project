# Auto-Start Setup Instructions

This directory contains scripts to run the Subway LED Console system automatically on Raspberry Pi boot.

## Quick Start (Manual)

### One-time setup:
```bash
cd /home/pi/repos/cpeg_capstone/Subway_LED_Console_project
chmod +x start_subway_system.sh
```

### Run manually:
```bash
./start_subway_system.sh
```

This will:
1. ✅ Activate the Python virtual environment
2. ✅ Start the main_pi_service.py (handles routing and LED commands)
3. ✅ Set DISPLAY=:0.0
4. ✅ Start the UI (run_ui.py)
5. ✅ Log all output to `logs/service.log` and `logs/ui.log`
6. ✅ Monitor both processes and restart if they crash

Press `Ctrl-C` to gracefully shut down both services.

---

## Auto-Start on Boot (Systemd)

To have the system automatically start when the Pi powers on:

### 1. Make the startup script executable
```bash
chmod +x /home/pi/repos/cpeg_capstone/Subway_LED_Console_project/start_subway_system.sh
```

### 2. Install the systemd service
```bash
sudo cp /home/pi/repos/cpeg_capstone/Subway_LED_Console_project/subway-console.service \
        /etc/systemd/system/subway-console.service
```

### 3. Reload systemd and enable the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable subway-console.service
```

### 4. Verify it's enabled
```bash
sudo systemctl status subway-console.service
```

You should see: `enabled` (highlighted)

### 5. Start it now (without rebooting)
```bash
sudo systemctl start subway-console.service
```

### 6. Verify it's running
```bash
sudo systemctl status subway-console.service
```

You should see: `active (running)`

---

## Troubleshooting

### View logs
```bash
# View all system logs
sudo journalctl -u subway-console.service -f

# View just the last 50 lines
sudo journalctl -u subway-console.service -n 50

# View detailed output
sudo journalctl -u subway-console.service --no-pager | tail -100
```

### Check if it's enabled
```bash
sudo systemctl is-enabled subway-console.service
```

### Disable auto-start (keep it installed)
```bash
sudo systemctl disable subway-console.service
```

### Stop the service
```bash
sudo systemctl stop subway-console.service
```

### Restart the service
```bash
sudo systemctl restart subway-console.service
```

### Remove auto-start completely
```bash
sudo systemctl disable subway-console.service
sudo systemctl stop subway-console.service
sudo rm /etc/systemd/system/subway-console.service
sudo systemctl daemon-reload
```

---

## Configuration

Edit `start_subway_system.sh` to customize:

- **SERIAL_PORT** (default: `/dev/serial0`) - Change if using a different UART port
- **SERIAL_BAUD** (default: `115200`) - Change if ESP32 uses different baud rate
- **UPDATE_INTERVAL** (default: `60`) - How often to refresh GTFS-RT data (seconds)

Example custom serial configuration:
```bash
SERIAL_PORT=/dev/ttyUSB0 SERIAL_BAUD=9600 ./start_subway_system.sh
```

Or edit the variables directly in `start_subway_system.sh` (lines ~13-16).

---

## Log Files

Logs are stored in `logs/` directory:

- **logs/service.log** - Output from main_pi_service.py
- **logs/ui.log** - Output from run_ui.py
- **logs/subway_system.pid** - Process IDs (auto-generated)

View them anytime:
```bash
tail -f logs/service.log
tail -f logs/ui.log
```

---

## What Happens on Boot

1. systemd triggers the service
2. `start_subway_system.sh` runs
3. Activates Python virtual environment
4. Starts main_pi_service.py (waits 3 seconds for it to initialize)
5. Starts run_ui.py with DISPLAY=:0.0
6. Monitors both processes
7. If either crashes, the service restarts
8. Logs all output to files and systemd journal

---

## Performance Notes

- **First startup:** ~5-10 seconds (loading network graph)
- **Subsequent starts:** ~3-5 seconds (loading from hot cache)
- **Edge updates:** Every 60 seconds in background
- **UI response:** <100ms when service is running

---

## Verify Everything Works

1. Open the logs:
   ```bash
   tail -f logs/service.log
   ```

2. In another terminal, check the UI:
   ```bash
   tail -f logs/ui.log
   ```

3. Both should show:
   - Service: `✅ NYC Subway LED Service Ready`
   - UI: `Kivy started successfully`

4. Stop with:
   ```bash
   sudo systemctl stop subway-console.service
   ```

---

## Advanced: Running on Different Display

If you have multiple displays, set the DISPLAY variable:

```bash
# In start_subway_system.sh, change this line:
export DISPLAY=:0.0

# To something like:
export DISPLAY=:1.0  # Second display
```

Or pass it when running manually:
```bash
DISPLAY=:1.0 ./start_subway_system.sh
```
