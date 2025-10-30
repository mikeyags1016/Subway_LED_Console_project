from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.textinput import TextInput
from subway_API import MTA_requests
from kivymd.app import MDApp
from kivy_garden.mapview import MapView, MapMarker
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse
import sqlite3
import os

class ColoredMarker(FloatLayout):
    def __init__(self, color=(1, 0, 0, 1), size=20, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*color)  # RGBA (1,0,0,1) = red
            Ellipse(size=(size, size), pos=(0, 0))

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

        # Filter stops that start with what’s typed
        matches = [s for s in self.stops if s.lower().startswith(value)]
        for stop in matches[:10]:  # limit results
            btn = Button(text=stop, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.select_stop(btn.text))
            self.dropdown.add_widget(btn)

        if matches:
            self.dropdown.open(self)

    def select_stop(self, stop_name):
        self.text = stop_name
        self.dropdown.dismiss()

'''
PACKAGE NOTES:

- To run UI, navigate to folder above Subway_LED_Console_project and type: python3 -m Subway_LED_Console_project.ui.run_ui 
- This will avoid relative pathing issues 
'''

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
    """Return (lat, lon) tuple for a stop where isrep = 1."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stop_lat, stop_lon FROM node WHERE stop_name = ? AND is_rep = 1",
            (stop_name,)
        )
        result = cursor.fetchone()
        conn.close()
        return result  # (lat, lon)
    except Exception as e:
        print(f"Error fetching coordinates for {stop_name}: {e}")
        return None

def add_colored_marker(mapview, lat, lon, color):
    marker = MapMarker(lat=lat, lon=lon)
    dot = ColoredMarker(color=color)
    marker.add_widget(dot)
    mapview.add_marker(marker)
    return marker

class TouchPadUI(MDApp):
    def build(self):

        db_path = os.path.join(os.path.dirname(__file__), "..", "network", "subway.db")
        db_path = os.path.abspath(db_path)
        print("Using DB:", db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("Tables found:", tables)

        conn.close()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "..", "network", "subway.db")
        DB_PATH = os.path.normpath(DB_PATH)

        stops = get_stops(DB_PATH)

        # Outer layout to center content towards the top
        outer_layout = AnchorLayout(anchor_x="center", anchor_y="top", padding=20)

        # Inner vertical layout (dropdown row + confirm button)
        container = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, 1))

        # Horizontal layout for the two dropdowns/text boxes
        main_layout = BoxLayout(orientation="horizontal", spacing=40, size_hint=(None, None))
        main_layout.size = (700, 100)

        # Layouts for each selection tool
        select_one_lay = BoxLayout(orientation="vertical", size_hint=(None, None))
        select_one_lay.size = (300, 100)
        select_two_lay = BoxLayout(orientation="vertical", size_hint=(None, None))
        select_two_lay.size = (300, 100)

        # First dropdown
        dropdown_one = DropDown()
        for stop in stops:
            btn = Button(text=stop, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: dropdown_one.select(btn.text))
            dropdown_one.add_widget(btn)

        select_one = Button(text='Select first stop', size_hint=(None, None), size=(200, 50))
        #select_one_text = TextInput(text='Select first stop', size_hint=(None, None), size=(200, 50))
        select_one_text = AutocompleteTextInput(stops, size_hint=(None, None), size=(200, 50))
        
        select_one.bind(on_release=dropdown_one.open)
        dropdown_one.bind(on_select=lambda instance, x: (
            setattr(select_one, 'text', x),
            setattr(select_one_text, 'text', x)
        ))

        # Second dropdown
        dropdown_two = DropDown()
        for stop in stops:
            btn2 = Button(text=stop, size_hint_y=None, height=40)
            btn2.bind(on_release=lambda btn2: dropdown_two.select(btn2.text))
            dropdown_two.add_widget(btn2)

        select_two = Button(text='Select second stop', size_hint=(None, None), size=(200, 50))
        #select_two_text = TextInput(text='Select second stop', size_hint=(None, None), size=(200, 50))
        select_two_text = AutocompleteTextInput(stops, size_hint=(None, None), size=(200, 50))

        select_two.bind(on_release=dropdown_two.open)
        dropdown_two.bind(on_select=lambda instance, x: (
            setattr(select_two, 'text', x),
            setattr(select_two_text, 'text', x)
        ))

        # Add widgets to their layouts
        select_one_lay.add_widget(select_one_text)
        select_one_lay.add_widget(select_one)
        select_two_lay.add_widget(select_two_text)
        select_two_lay.add_widget(select_two)

        main_layout.add_widget(select_one_lay)
        main_layout.add_widget(select_two_lay)

        # Confirm button
        confirm_btn = Button(text="Confirm Stops", size_hint=(None, None), size=(200, 50))

        def confirm_selection(instance):
            stop1 = select_one_text.text.strip()
            stop2 = select_two_text.text.strip()
            print(f"First stop: {stop1}, Second stop: {stop2}")

            coords1 = get_stop_coordinates(stop1, DB_PATH)
            coords2 = get_stop_coordinates(stop2, DB_PATH)

            # Clear previous markers if needed
            mapview.children[:] = [w for w in mapview.children if not isinstance(w, MapMarker)]

    # Add markers if coordinates exist
            if coords1:
                #marker1 = MapMarker(lat=coords1[0], lon=coords1[1], source="marker_start.png")
                #mapview.add_marker(marker1)
                add_colored_marker(mapview, coords1[0], coords1[1], color=(0, 1, 0, 1))

            if coords2:
                #marker2 = MapMarker(lat=coords2[0], lon=coords2[1], source="marker_end.png")
                #mapview.add_marker(marker2)
                add_colored_marker(mapview, coords2[0], coords2[1], color=(1, 0, 0, 1))

            print(f"Coordinates: {coords1}, {coords2}")

        confirm_btn.bind(on_release=confirm_selection)

        mapview = MapView(
            zoom=10,
            lat=40.7580,
            lon=-73.9855,
            size_hint=(1, 1)
        )

        # Add layouts
        container.add_widget(main_layout)
        container.add_widget(confirm_btn)
        container.add_widget(mapview)

        outer_layout.add_widget(container)
        return outer_layout

if __name__ == '__main__':
    TouchPadUI().run()
