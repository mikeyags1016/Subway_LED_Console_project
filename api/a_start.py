import csv
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def read_stations(csv_file):
    stations = {}
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            station_id = row['parent_station'] if row['parent_station'] else row['stop_id']
            stations[station_id] = {
                'station_id': station_id,
                'stop_name': row['stop_name'],
                'lat': row['stop_lat'],
                'lon': row['stop_lon']
            }
    return stations

def calculate_distances(stations):
    # stations is a dict: station_id -> station_info
    distances = {}
    station_ids = list(stations.keys())
    for i in range(len(station_ids)):
        for j in range(i + 1, len(station_ids)):
            from_id = station_ids[i]
            to_id = station_ids[j]
            # Skip if same station
            if from_id == to_id:
                continue
            # Store only one direction (from_id, to_id), never (to_id, from_id)
            s1 = stations[from_id]
            s2 = stations[to_id]
            dist = float(haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon']))
            key = tuple(sorted((from_id, to_id)))
            if key not in distances:
                distances[key] = dist
    return distances

if __name__ == "__main__":
    csv_file = "stops.txt"  # Change to your CSV file path
    stations = read_stations(csv_file)
    distances = calculate_distances(stations)
    # Build a lookup for station id -> name for printing
    id_to_name = {s['station_id']: s['stop_name'] for s in stations}
    i = 0
    for (from_id, to_id), dist in distances.items():
        from_name = id_to_name.get(from_id, from_id)
        to_name = id_to_name.get(to_id, to_id)
        print(f"{i}: {from_name} ({from_id}) -> {to_name} ({to_id}): {dist:.2f} km")
        i += 1