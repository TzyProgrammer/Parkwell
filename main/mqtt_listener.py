# main/mqtt_listener.py
import paho.mqtt.client as mqtt
from main import views  # Untuk update latest_data
import json

# Callback ketika konek ke broker
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke broker MQTT dengan kode:", rc)
    client.subscribe("parkir/slot1")

# Callback ketika pesan diterima
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(f"Pesan diterima: {payload}")
        views.latest_data["distance"] = payload  # Update tampilan web
    except Exception as e:
        print("Error parsing message:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)  # Gunakan IP broker jika tidak di localhost
client.loop_forever()
