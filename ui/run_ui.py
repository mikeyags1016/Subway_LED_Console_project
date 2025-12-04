import sys
import os
import socket
import json
import sqlite3

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from kivy_garden.mapview import MapView, MapMarker, MapLayer
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse, Line

# -------------------------
# Marker Classes
# -------------------------
class ColoredMarker(FloatLayout):
    def __init__(self, color=(1, 0, 0, 0.85), size=10, **kwargs):
        super().__init__(**kwargs)
        half = size / 2.0
        with self.canvas:
            Color(*color)
            Ellipse(size=(size, size), pos=(-half, -half))

# -------------------------
# Autocomplete Input
# -------------------------
class AutocompleteTextInput(TextInput):
    """Persistent autocomplete dropdown for stops."""
    def __init__(self, stops, **kwargs):
        super().__init__(**kwargs)
        self.stops = list(stops)  # (stop_name, stop_id)
        self.selected_id = None
        self.dropdown = DropDown()
        self._last_matches = []

        # Always track changes
        self.bind(text=self.on_text_change)
        self.bind(focus=self.on_focus)

    def build_dropdown(self, matches):
        if matches == self._last_matches:
            return
        self._last_matches = matches

        self.dropdown.clear_widgets()

        from kivy.uix.scrollview import ScrollView
        from kivy.uix.boxlayout import BoxLayout

        scroll = ScrollView(size_hint=(None, None), size=(self.width, 250))
        box = BoxLayout(orientation='vertical', size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        for name, sid in matches:
            btn = Button(text=name, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn, n=name, s=sid: self.select_stop(n, s))
            box.add_widget(btn)

        scroll.add_widget(box)
        self.dropdown.add_widget(scroll)

        if matches:
            self.dropdown.auto_dismiss = False
            self.dropdown.open(self)
        else:
            self.dropdown.dismiss()

    def on_text_change(self, instance, value):
        value = value.strip().lower()
        if not value:
            matches = self.stops
        else:
            matches = [s for s in self.stops if value in s[0].lower()]
        self.build_dropdown(matches)

    def on_focus(self, instance, value):
        if value:
            self.on_text_change(self, self.text)
        else:
            self.dropdown.dismiss()

    def select_stop(self, stop_name, stop_id):
        self.text = stop_name
        self.selected_id = stop_id
        self.dropdown.dismiss()

# -------------------------
# Database Helpers
# -------------------------
def get_stops(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT stop_name, stop_id FROM node WHERE is_rep = 1 ORDER BY stop_name ASC")
        stops = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return stops
    except Exception as e:
        print(f"Error loading stops: {e}")
        return []

def get_stop_coordinates(stop_id, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(node)")
        cols = [r[1] for r in cursor.fetchall()]
        has_rep = 'rep' in cols

        if has_rep:
            cursor.execute("SELECT stop_lat, stop_lon, is_rep, rep FROM node WHERE stop_id = ?", (stop_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            lat, lon, is_rep, rep = row
            if is_rep:
                conn.close()
                return (lat, lon)
            if rep:
                cursor.execute("SELECT stop_lat, stop_lon FROM node WHERE stop_id = ?", (rep,))
                r = cursor.fetchone()
                conn.close()
                if r:
                    return (r[0], r[1])
            conn.close()
            return (lat, lon)
        else:
            cursor.execute("SELECT stop_lat, stop_lon FROM node WHERE stop_id = ?", (stop_id,))
            result = cursor.fetchone()
            conn.close()
            return result
    except Exception as e:
        print(f"Error fetching coordinates for {stop_id}: {e}")
        return None

def add_colored_marker(mapview, lat, lon, color):
    marker = MapMarker(lat=lat, lon=lon)
    dot = ColoredMarker(color=(color[0], color[1], color[2], 0.85), size=10)
    marker.add_widget(dot)
    mapview.add_marker(marker)
    return marker

# -------------------------
# Route Line Layer
# -------------------------
class RouteLineLayer(MapLayer):
    """Draws polyline that scales with zoom."""
    def __init__(self, coords=None, **kwargs):
        super().__init__(**kwargs)
        self.coords = coords or []

    def update_coords(self, coords):
        self.coords = coords or []
        try:
            self.reposition()
        except Exception:
            pass

    def reposition(self, *args):
        self.canvas.clear()
        if not self.coords:
            return
        with self.canvas:
            Color(0, 0.4, 1, 0.7)
            points = []
            for lat, lon in self.coords:
                try:
                    x, y = self.parent.get_window_xy_from(lat, lon, self.parent.zoom)
                except Exception:
                    continue
                points.extend([x, y])
            if len(points) >= 4:
                Line(points=points, width=2)

# -------------------------
# Main App
# -------------------------
class TouchPadUI(App):
    def build(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.normpath(os.path.join(base_dir, "..", "network", "subway.db"))
        stops = get_stops(db_path)

        mapview = MapView(zoom=10, lat=40.7580, lon=-73.9855, size_hint=(1, 1))
        self.mapview = mapview
        self.route_layer = None

        # Layouts
        outer_layout = AnchorLayout(anchor_x="center", anchor_y="top", padding=20)
        container = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, 1))
        main_layout = BoxLayout(orientation="horizontal", spacing=40, size_hint=(None, None))
        main_layout.size = (700, 100)

        select_one_text = AutocompleteTextInput(stops, size_hint=(None, None), size=(200, 50))
        select_two_text = AutocompleteTextInput(stops, size_hint=(None, None), size=(200, 50))

        select_one_lay = BoxLayout(orientation="vertical", size_hint=(None, None), size=(300, 100))
        select_two_lay = BoxLayout(orientation="vertical", size_hint=(None, None), size=(300, 100))
        select_one_lay.add_widget(select_one_text)
        select_two_lay.add_widget(select_two_text)

        main_layout.add_widget(select_one_lay)
        main_layout.add_widget(select_two_lay)
        container.add_widget(main_layout)

        # Confirm Button
        confirm_btn = Button(text="Confirm Stops", size_hint=(None, None), size=(200, 50))
        def confirm_selection(instance):
            def resolve(widget):
                if getattr(widget, 'selected_id', None):
                    return widget.selected_id
                name = widget.text.strip()
                if not name:
                    return None
                for nm, sid in stops:
                    if nm == name:
                        return sid
                return None

            stop1_id = resolve(select_one_text)
            stop2_id = resolve(select_two_text)
            if not stop1_id or not stop2_id:
                print("Please select both stops from the list (use the dropdown).")
                return

            # Connect to main_pi_service.py via Unix socket
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect('/tmp/subway_service.sock')
                request = json.dumps({"start": stop1_id, "goal": stop2_id})
                sock.sendall(request.encode('utf-8') + b'\n')
                response_data = b''
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                    if b'\n' in response_data:
                        break
                sock.close()
                path_result = json.loads(response_data.decode('utf-8').strip())
                if path_result.get('status') == 'error':
                    print(f"Error from service: {path_result.get('message')}")
                    return
            except socket.timeout:
                print("Service request timed out.")
                return
            except FileNotFoundError:
                print("main_pi_service.py not running.")
                return
            except Exception as e:
                print(f"Error: {e}")
                return

            path = path_result.get('path')
            delayed_segments = path_result.get('delayed_segments', [])

            # Clear previous markers
            mapview.children[:] = [w for w in mapview.children if not isinstance(w, MapMarker)]
            if self.route_layer:
                try:
                    mapview.remove_layer(self.route_layer)
                except Exception:
                    mapview.remove_widget(self.route_layer)
                self.route_layer = None

            if path:
                print(f"Path found: {path_result.get('stop_names')}")
                coords_seq = []

                # Start = green
                coords_start = get_stop_coordinates(path[0], db_path)
                if coords_start:
                    add_colored_marker(mapview, coords_start[0], coords_start[1], color=(0, 1, 0, 1))
                    coords_seq.append(coords_start)

                # Intermediate = blue
                for sid in path[1:-1]:
                    coords = get_stop_coordinates(sid, db_path)
                    if coords:
                        add_colored_marker(mapview, coords[0], coords[1], color=(0, 0, 1, 1))
                        coords_seq.append(coords)

                # End = red
                coords_end = get_stop_coordinates(path[-1], db_path)
                if coords_end:
                    add_colored_marker(mapview, coords_end[0], coords_end[1], color=(1, 0, 0, 1))
                    coords_seq.append(coords_end)

                # Draw RouteLineLayer that scales with zoom
                try:
                    self.route_layer = RouteLineLayer(coords_seq)
                    mapview.add_layer(self.route_layer)
                    self.route_layer.update_coords(coords_seq)
                except Exception as e:
                    print("Could not create route layer:", e)

        confirm_btn.bind(on_release=confirm_selection)
        container.add_widget(confirm_btn)

        container.add_widget(mapview)
        outer_layout.add_widget(container)
        return outer_layout

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    TouchPadUI().run()
