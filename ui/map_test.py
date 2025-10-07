import math
import re
import sqlite3
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.mapview import MapView, MapMarker, MapMarkerPopup

KV = r"""
<Root>:
    orientation: "vertical"
    spacing: dp(6)
    padding: dp(6)

    # Top row: DB path + load + reps/all toggle
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(6)

        TextInput:
            id: dbpath
            hint_text: "Path to SQLite DB (e.g., nyc_subway.db)"
            text: root.db_path
            multiline: False
            on_text_validate: root.load_stations()

        Button:
            text: "Load Stations"
            on_release: root.load_stations()

        CheckBox:
            id: allnodes
            size_hint_x: None
            width: dp(24)
            active: False
            on_active: root.show_all_nodes = self.active
        Label:
            text: "All platforms"
            size_hint_x: None
            width: dp(110)
            valign: "middle"

    # Search row
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(6)

        TextInput:
            id: search
            hint_text: "Search NYC address (e.g., 'Times Square') or 'lat,lon'"
            multiline: False
            on_text_validate: root.on_search(self.text)

        Button:
            text: "Search"
            on_release: root.on_search(search.text)

        Button:
            text: "Clear"
            on_release: root.clear_search()

    # Map
    MapView:
        id: map
        lat: root.center_lat
        lon: root.center_lon
        zoom: 11

    # Status line
    Label:
        id: status
        size_hint_y: None
        height: dp(24)
        text: root.status_text
        halign: "left"
        valign: "middle"
        text_size: self.size
"""

NYC_LAT, NYC_LON = 40.7128, -74.0060

COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2*R*math.asin(math.sqrt(a))

def parse_coords_maybe(text):
    m = COORD_RE.match(text or "")
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))

def geocode_address_async(query, callback, *, user_agent="kivy-mapview-nyc/1.0"):
    import requests
    def worker():
        try:
            params = {
                "q": query,
                "format": "json",
                "limit": 1,
                "viewbox": "-74.2591,40.9158,-73.7002,40.4774",  # NYC bounding box
                "bounded": 1,
                "addressdetails": 0,
            }
            headers = {"User-Agent": user_agent}
            r = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data:
                _dispatch(callback, None); return
            lat = float(data[0]["lat"]); lon = float(data[0]["lon"])
            _dispatch(callback, (lat, lon))
        except Exception:
            _dispatch(callback, None)
    threading.Thread(target=worker, daemon=True).start()

from kivy.uix.label import Label
class _MarkerPopup(BoxLayout):
    def __init__(self, text="", **kw):
        super().__init__(orientation="vertical", padding=6, **kw)
        self.add_widget(Label(text=text, size_hint=(1, 1)))

@mainthread
def _dispatch(cb, value):
    try:
        cb(value)
    except Exception:
        pass

class Root(BoxLayout):
    mapview = ObjectProperty(None)
    stations = ListProperty([])  # list of dicts: {id, name, lat, lon, marker}
    db_path = StringProperty("nyc_subway.db")
    status_text = StringProperty("Ready.")
    center_lat = NumericProperty(NYC_LAT)
    center_lon = NumericProperty(NYC_LON)
    show_all_nodes = BooleanProperty(False)

    _search_marker = None
    _last_highlight_idx = None

    def on_kv_post(self, _):
        self.ids.dbpath.text = self.db_path

    def set_status(self, text):
        self.status_text = text
        self.ids.status.text = text

    # --------- DB LOADING ----------
    def load_stations(self):
        path = self.ids.dbpath.text.strip() or self.db_path
        only_reps = not self.show_all_nodes

        sql = """
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM node
        WHERE stop_lat IS NOT NULL AND stop_lon IS NOT NULL
        """
        if only_reps:
            sql += " AND is_rep = 1"
        sql += " ORDER BY stop_name, stop_id"

        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            self.set_status(f"DB error: {e}")
            return

        self._clear_station_markers()

        loaded = []
        m = self.ids.map
        count = 0
        for stop_id, stop_name, lat, lon in rows:
            try:
                lat = float(lat); lon = float(lon)
            except Exception:
                continue
            marker = MapMarkerPopup(lat=lat, lon=lon, size=(24, 24))
            marker.anchor = (12, 24)
            marker.add_widget(_MarkerPopup(text=f"{stop_name}\n[{stop_id}]"))
            m.add_widget(marker)
            loaded.append({"id": stop_id, "name": stop_name, "lat": lat, "lon": lon, "marker": marker})
            count += 1

        self.stations = loaded
        self.set_status(f"Loaded {count} station node(s){' (representatives)' if only_reps else ''}.")

    def _clear_station_markers(self):
        m = self.ids.map
        for s in getattr(self, "stations", []):
            mk = s.get("marker")
            if mk and mk.parent is m:
                m.remove_widget(mk)
        self.stations = []
        self._clear_highlight()

    # --------- SEARCH ----------
    def on_search(self, text):
        q = (text or "").strip()
        if not q:
            self.set_status("Enter an address or 'lat,lon'."); return

        as_coords = parse_coords_maybe(q)
        if as_coords:
            self._place_search_point(*as_coords); return

        self.set_status("Geocoding…")
        geocode_address_async(q, self._on_geocode_done)

    def _on_geocode_done(self, latlon):
        if not latlon:
            self.set_status("No results in NYC.")
            return
        self._place_search_point(*latlon)

    def _place_search_point(self, lat, lon):
        m = self.ids.map
        if self._search_marker is None:
            self._search_marker = MapMarker(lat=lat, lon=lon, size=(36, 36))
            self._search_marker.anchor = (18, 36)
            m.add_widget(self._search_marker)
        else:
            self._search_marker.lat = lat
            self._search_marker.lon = lon

        m.center_on(lat, lon)
        if m.zoom < 13: m.zoom = 13

        self._highlight_nearest(lat, lon)

    def clear_search(self):
        if self._search_marker and self._search_marker.parent is self.ids.map:
            self.ids.map.remove_widget(self._search_marker)
        self._search_marker = None
        self._clear_highlight()
        self.set_status("Cleared search.")

    # --------- HIGHLIGHT ----------
    def _highlight_nearest(self, lat, lon):
        if not self.stations:
            self.set_status("No stations loaded."); return

        best_idx, best_d = None, float("inf")
        for i, s in enumerate(self.stations):
            d = haversine(lat, lon, s["lat"], s["lon"])
            if d < best_d:
                best_d, best_idx = d, i
        self._apply_highlight(best_idx, best_d)

    def _apply_highlight(self, idx, distance_m):
        if idx is None:
            self._clear_highlight(); return

        if self._last_highlight_idx is not None and 0 <= self._last_highlight_idx < len(self.stations):
            prev = self.stations[self._last_highlight_idx]["marker"]
            prev.size = (24, 24)
            prev.opacity = 1.0

        s = self.stations[idx]
        mk = s["marker"]
        mk.size = (48, 48)
        mk.opacity = 1.0
        self._last_highlight_idx = idx

        human = f"{int(distance_m)} m" if distance_m < 1000 else f"{distance_m/1000:.2f} km"
        self.set_status(f"Nearest: {s['name']} [{s['id']}] ({human}).")

    def _clear_highlight(self):
        if self._last_highlight_idx is not None and self.stations:
            try:
                prev = self.stations[self._last_highlight_idx]["marker"]
                prev.size = (24, 24); prev.opacity = 1.0
            except Exception:
                pass
        self._last_highlight_idx = None


class NYCSubwayApp(App):
    def build(self):
        Builder.load_string(KV)
        return Root()

if __name__ == "__main__":
    NYCSubwayApp().run()
