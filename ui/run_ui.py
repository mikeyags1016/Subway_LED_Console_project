import sys
import os

# Add the parent directory (Subway_LED_Console_project) to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Now you can import SubwayNetwork from the network folder
from network.SubwayNetwork import SubwayNetwork

# The rest of your imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivy_garden.mapview import MapView, MapMarker
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse
import sqlite3

# -------------------------
# Marker Classes
# -------------------------
class ColoredMarker(FloatLayout):
    def __init__(self, color=(1, 0, 0, 1), size=20, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*color)
            Ellipse(size=(size, size), pos=(0, 0))

# -------------------------
# Autocomplete Input
# -------------------------
class AutocompleteTextInput(TextInput):
    def __init__(self, stops, **kwargs):
        super().__init__(**kwargs)
        self.stops = stops
        self.dropdown = DropDown()
        self.bind(text=self.on_text_change)

    def on_text_change(self, instance, value):
        self.dropdown.dismiss()
        self.dropdown = DropDown()
        value = value.strip().lower()
        if not value:
            return
        matches = [s for s in self.stops if s.lower().startswith(value)]
        for stop in matches[:10]:
            btn = Button(text=stop, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_stop(btn.text))
            self.dropdown.add_widget(btn)
        if matches:
            self.dropdown.open(self)

    def select_stop(self, stop_name):
        self.text = stop_name
        self.dropdown.dismiss()

# -------------------------
# Database Helpers
# -------------------------
def get_stops(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT stop_name FROM node WHERE is_rep = 1 ORDER BY stop_name ASC")
        stops = [row[0] for row in cursor.fetchall()]
        conn.close()
        return stops
    except Exception as e:
        print(f"Error loading stops: {e}")
        return []

def get_stop_coordinates(stop_name, db_path):
    """Return (lat, lon) tuple for a stop where is_rep = 1."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stop_lat, stop_lon FROM node WHERE stop_name = ? AND is_rep = 1",
            (stop_name,)
        )
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error fetching coordinates for {stop_name}: {e}")
        return None

def add_colored_marker(mapview, lat, lon, color):
    marker = MapMarker(lat=lat, lon=lon)
    dot = ColoredMarker(color=color)
    marker.add_widget(dot)
    mapview.add_marker(marker)
    return marker

# -------------------------
# Main UI
# -------------------------
class TouchPadUI(App):
    def build(self):
        # -------------------------
        # Database setup
        # -------------------------
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.normpath(os.path.join(base_dir, "..", "network", "subway.db"))
        print("Using DB:", db_path)
        stops = get_stops(db_path)

        # -------------------------
        # Subway Network
        # -------------------------
        self.network = SubwayNetwork(db_path)

        # -------------------------
        # MapView
        # -------------------------
        mapview = MapView(zoom=10, lat=40.7580, lon=-73.9855, size_hint=(1, 1))

        # -------------------------
        # UI Layouts
        # -------------------------
        outer_layout = AnchorLayout(anchor_x="center", anchor_y="top", padding=20)
        container = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, 1))
        main_layout = BoxLayout(orientation="horizontal", spacing=40, size_hint=(None, None))
        main_layout.size = (700, 100)

        # First stop selection
        select_one_lay = BoxLayout(orientation="vertical", size_hint=(None, None))
        select_one_lay.size = (300, 100)
        select_one_text = AutocompleteTextInput(stops, size_hint=(None, None), size=(200, 50))

        # Second stop selection
        select_two_lay = BoxLayout(orientation="vertical", size_hint=(None, None))
        select_two_lay.size = (300, 100)
        select_two_text = AutocompleteTextInput(stops, size_hint=(None, None), size=(200, 50))

        # Add widgets to layouts
        select_one_lay.add_widget(select_one_text)
        select_two_lay.add_widget(select_two_text)
        main_layout.add_widget(select_one_lay)
        main_layout.add_widget(select_two_lay)
        container.add_widget(main_layout)

        # -------------------------
        # Confirm Button
        # -------------------------
        confirm_btn = Button(text="Confirm Stops", size_hint=(None, None), size=(200, 50))
        def confirm_selection(instance):
            stop1 = select_one_text.text.strip()
            stop2 = select_two_text.text.strip()
            if not stop1 or not stop2:
                print("Please select both stops.")
                return

            # -------------------------
            # Find path
            # -------------------------
            path_result = self.network.find_route(stop1, stop2, use_live_data=True)
            path = path_result['path']

            # Clear previous markers
            mapview.children[:] = [w for w in mapview.children if not isinstance(w, MapMarker)]

            if path:
                print(f"Path found: {path_result['stop_names']}")
                # Draw intermediate path in blue
                for stop_id in path[1:-1]:
                    coords = get_stop_coordinates(stop_id, db_path)
                    if coords:
                        add_colored_marker(mapview, coords[0], coords[1], color=(0, 0, 1, 1))
                # Start = green
                coords_start = get_stop_coordinates(path[0], db_path)
                if coords_start:
                    add_colored_marker(mapview, coords_start[0], coords_start[1], color=(0, 1, 0, 1))
                # End = red
                coords_end = get_stop_coordinates(path[-1], db_path)
                if coords_end:
                    add_colored_marker(mapview, coords_end[0], coords_end[1], color=(1, 0, 0, 1))
            else:
                print("No path found.")

        confirm_btn.bind(on_release=confirm_selection)
        container.add_widget(confirm_btn)

        # -------------------------
        # Add MapView to layout
        # -------------------------
        container.add_widget(mapview)
        outer_layout.add_widget(container)

        return outer_layout

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    TouchPadUI().run()

