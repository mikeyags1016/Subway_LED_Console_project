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
from kivy.graphics import Color, Ellipse, Line
import sqlite3

# -------------------------
# Marker Classes
# -------------------------
class ColoredMarker(FloatLayout):
    def __init__(self, color=(1, 0, 0, 0.85), size=10, **kwargs):
        """Small semi-transparent centered dot to be less obtrusive on the map."""
        super().__init__(**kwargs)
        # Draw a small centered ellipse so the marker doesn't cover much of the map
        half = size / 2.0
        with self.canvas:
            Color(*color)
            Ellipse(size=(size, size), pos=(-half, -half))

# -------------------------
# Autocomplete Input
# -------------------------
class AutocompleteTextInput(TextInput):
    """TextInput with a scrollable dropdown of stops.

    `stops` is expected to be a list of (stop_name, stop_id) tuples. The
    dropdown displays human-readable `stop_name` entries (one per rep node),
    and the widget stores the selected stop_id in `self.selected_id`.
    """
    def __init__(self, stops, **kwargs):
        super().__init__(**kwargs)
        # stops: list of (stop_name, stop_id)
        self.stops = list(stops)
        self.dropdown = DropDown()
        self.selected_id = None

        # Bind text changes and focus so the dropdown appears even with empty input
        self.bind(text=self.on_text_change)
        self.bind(focus=self.on_focus)

    def build_dropdown(self, matches):
        """Rebuilds dropdown contents from an iterable of (stop_name, stop_id)."""
        self.dropdown.dismiss()
        self.dropdown = DropDown()

        # Create a scrollable container
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.boxlayout import BoxLayout

        scroll = ScrollView(size_hint=(None, None), size=(self.width, 300))
        box = BoxLayout(orientation='vertical', size_hint_y=None)
        # each button has fixed height
        btn_h = 40
        box.bind(minimum_height=box.setter('height'))

        for name, sid in matches:
            btn = Button(text=name, size_hint_y=None, height=btn_h)
            # capture values correctly in lambda
            btn.bind(on_release=lambda btn, n=name, s=sid: self.select_stop(n, s))
            box.add_widget(btn)

        scroll.add_widget(box)
        self.dropdown.add_widget(scroll)

        # Only open if there are matches
        if matches:
            # Open below this widget
            self.dropdown.open(self)

    def on_text_change(self, instance, value):
        value = value.strip().lower()
        if not value:
            # show all rep stops when input is empty
            matches = self.stops
        else:
            matches = [s for s in self.stops if s[0].lower().startswith(value)]

        # Limit to a reasonable number but allow scrolling
        self.build_dropdown(matches)

    def on_focus(self, instance, value):
        # When focused, show the full list (even if text is empty)
        if value:
            self.on_text_change(self, self.text)
        else:
            # dismiss when losing focus
            if self.dropdown:
                self.dropdown.dismiss()

    def select_stop(self, stop_name, stop_id):
        self.text = stop_name
        self.selected_id = stop_id
        if self.dropdown:
            self.dropdown.dismiss()

# -------------------------
# Database Helpers
# -------------------------
def get_stops(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Provide (stop_name, stop_id) choices for representative platforms
        cursor.execute("SELECT stop_name, stop_id FROM node WHERE is_rep = 1 ORDER BY stop_name ASC")
        stops = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return stops
    except Exception as e:
        print(f"Error loading stops: {e}")
        return []

def get_stop_coordinates(stop_id, db_path):
    """Return (lat, lon) tuple for a stop_id.

    Behavior:
      - If the node is a representative (is_rep=1) return its coords.
      - If not, and a `rep` column exists and is set, return the rep node's coords.
      - Otherwise fall back to the node's own coords if available.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check whether the `rep` column exists
        cursor.execute("PRAGMA table_info(node)")
        cols = [r[1] for r in cursor.fetchall()]
        has_rep = 'rep' in cols

        if has_rep:
            cursor.execute(
                "SELECT stop_lat, stop_lon, is_rep, rep FROM node WHERE stop_id = ?",
                (stop_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            lat, lon, is_rep, rep = row
            # If this node is a rep, use its coords
            if is_rep:
                conn.close()
                return (lat, lon)
            # If a rep is set, prefer its coords
            if rep:
                cursor.execute("SELECT stop_lat, stop_lon FROM node WHERE stop_id = ?", (rep,))
                r = cursor.fetchone()
                conn.close()
                if r:
                    return (r[0], r[1])
                # fall through to return the original node coords if rep missing
            conn.close()
            return (lat, lon)

        else:
            # No rep column: fall back to selecting by stop_id
            cursor.execute("SELECT stop_lat, stop_lon FROM node WHERE stop_id = ?", (stop_id,))
            result = cursor.fetchone()
            conn.close()
            return result
    except Exception as e:
        print(f"Error fetching coordinates for {stop_id}: {e}")
        return None

def add_colored_marker(mapview, lat, lon, color):
    marker = MapMarker(lat=lat, lon=lon)
    # use a small, slightly transparent dot
    dot = ColoredMarker(color=(color[0], color[1], color[2], 0.85), size=10)
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
        # store on self so other methods can draw/clear lines
        self.mapview = mapview
        # keep references to any canvas instructions we add so we can remove them later
        self._line_instr = []

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
            # Prefer the selected_id (stop_id) from the autocomplete widgets.
            # If not set, try to resolve by exact stop_name match.
            def resolve(widget):
                if getattr(widget, 'selected_id', None):
                    return widget.selected_id
                name = widget.text.strip()
                if not name:
                    return None
                # try exact match in stops list
                for nm, sid in stops:
                    if nm == name:
                        return sid
                return None

            stop1_id = resolve(select_one_text)
            stop2_id = resolve(select_two_text)
            if not stop1_id or not stop2_id:
                print("Please select both stops from the list (use the dropdown).")
                return

            # -------------------------
            # Find path
            # -------------------------
            path_result = self.network.find_route(stop1_id, stop2_id, use_live_data=True)
            path = path_result['path']

            # Clear previous markers
            mapview.children[:] = [w for w in mapview.children if not isinstance(w, MapMarker)]
            # Clear any existing path lines from the mapview canvas
            for instr in list(getattr(self, '_line_instr', [])):
                try:
                    mapview.canvas.remove(instr)
                except Exception:
                    pass
            self._line_instr = []

            if path:
                print(f"Path found: {path_result['stop_names']}")
                # Collect coordinates in sequence so we can draw a line between them
                coords_seq = []
                # Start = green
                coords_start = get_stop_coordinates(path[0], db_path)
                if coords_start:
                    add_colored_marker(mapview, coords_start[0], coords_start[1], color=(0, 1, 0, 1))
                    coords_seq.append(coords_start)

                # Draw intermediate path in blue
                for stop_id in path[1:-1]:
                    coords = get_stop_coordinates(stop_id, db_path)
                    if coords:
                        add_colored_marker(mapview, coords[0], coords[1], color=(0, 0, 1, 1))
                        coords_seq.append(coords)

                # End = red
                coords_end = get_stop_coordinates(path[-1], db_path)
                if coords_end:
                    add_colored_marker(mapview, coords_end[0], coords_end[1], color=(1, 0, 0, 1))
                    coords_seq.append(coords_end)

                # Draw polyline between the plotted coordinates
                try:
                    points = []
                    for lat, lon in coords_seq:
                        # convert geographical coords to widget/window positions
                        try:
                            x, y = mapview.get_window_xy_from(lat, lon, mapview.zoom)
                        except TypeError:
                            # some versions accept only lat, lon
                            x, y = mapview.get_window_xy_from(lat, lon)
                        points.extend([x, y])

                    if len(points) >= 4:
                        c = Color(0, 0.4, 1, 0.7)
                        l = Line(points=points, width=2)
                        # add to canvas and keep refs so we can remove later
                        mapview.canvas.add(c)
                        mapview.canvas.add(l)
                        self._line_instr.extend([c, l])
                except Exception as e:
                    # drawing failed (e.g., method missing) — ignore but log
                    print("Could not draw path line:", e)
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

