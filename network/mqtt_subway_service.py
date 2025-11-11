import time
import json
import paho.mqtt.client as mqtt
from network.SubwayNetwork import SubwayNetwork

# MQTT Configuration
BROKER = "mqtt.eclipseprojects.io"  # Replace with your MQTT broker address
REQUEST_TOPIC = "subway/directions/request"
RESPONSE_TOPIC = "subway/directions/response"

# Initialize Subway Network
network = SubwayNetwork('subway.db')

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(REQUEST_TOPIC)

def on_message(client, userdata, msg):
    try:
        # Parse the request
        request = json.loads(msg.payload.decode())
        start = request.get("start")
        goal = request.get("goal")

        print(f"Received direction request: {start} → {goal}")

        # Find the route
        result = network.find_route(start, goal, use_live_data=True)

        # Prepare the response
        response = {
            "path": result.get("path"),
            "total_time_minutes": result.get("total_time_minutes"),
            "num_stops": result.get("num_stops"),
            "stop_names": result.get("stop_names"),
        }

        # Publish the response
        client.publish(RESPONSE_TOPIC, json.dumps(response))
        print(f"Sent response: {response}")

    except Exception as e:
        print(f"Error processing request: {e}")

# Main Function
def main():
    # Initialize MQTT Client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to MQTT Broker
    client.connect(BROKER, 1883, 60)

    # Start MQTT Loop
    client.loop_forever()

if __name__ == "__main__":
    main()