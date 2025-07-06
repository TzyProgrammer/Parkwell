import os
import django
import paho.mqtt.client as mqtt

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Parkwell.settings")
django.setup()

from main.models import Spot

# Map topik ke spot_number
topic_to_spot = {
    "parkir/slot1": "1",
    "parkir/slot2": "2",
    "parkir/slot3": "3",
    "parkir/slot4": "4",
}

def on_connect(client, userdata, flags, rc):
    print("Terhubung ke MQTT")
    for topic in topic_to_spot.keys():
        client.subscribe(topic)

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        distance = float(payload)
        spot_number = topic_to_spot[topic]
        print(f"Data dari {topic} = {distance} cm")

        spot = Spot.objects.get(spot_number=spot_number)
        spot.update_status_from_distance(distance)
        print(f"Slot {spot_number} diupdate ke {spot.status}")
        print("="*30)

    except Exception as e:
        print("Gagal memproses:", e)
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()