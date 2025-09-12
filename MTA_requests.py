from google.transit import gtfs_realtime_pb2
import requests
import csv

'''
MTA_REQUESTS:

Script for making API calls for General Transit Feed Specification (GTFS) for the NYC MTA API
GTFS is a specification for transit data that allows transit data to be used inoperably by organizations

'''

ENDPOINT = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
STOPS = "stops.txt"
TRIPS = "trips.txt"
ROUTES = "routes.txt"

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get(ENDPOINT)
feed.ParseFromString(response.content)

# open("GTFS_updates.txt", "w").close()
# open("GTFS_positions.txt", "w").close()
# open("GTFS_alerts.txt", "w").close()

# for entity in feed.entity:
#     if entity.HasField('trip_update'):
#         with open("GTFS_updates.txt", "a") as file:
#             file.write(str(entity.trip_update) + "\n")
#     elif entity.HasField('vehicle'):
#         with open("GTFS_positions.txt", "a") as file:
#             file.write(str(entity.vehicle) + "\n")
#     elif entity.HasField('alert'):
#         with open("GTFS_alerts.txt", "a") as file:
#             file.write(str(entity.alert) + "\n")

'''
find_train_stop:

- figures out which stop the user is looking for within the GTFS data
- Associates specific lines, related services, alerts, etc. with this stop
- Updates A* pathing list

'''

def find_train_stop(station_name):
    with open(ROUTES, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(row)

find_train_stop('asdf')

'''
find_line:

- selects correct trainline associated with a stop and returns API endpoint 
'''

def find_line(station_name):
    pass