import os
import django
import paho.mqtt.client as mqtt
import json

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Parkwell.settings")
django.setup()

from main.models import Spot

def on_connect(client, userdata, flags, rc):
    print("Terhubung ke broker MQTT")
    client.subscribe("parkir/slot1")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        distance = float(payload)
        print(f"Jarak diterima: {distance} cm")

        spot = Spot.objects.get(spot_number="1")
        spot.update_status_from_distance(distance)
        print(f"Status spot 1 diperbarui menjadi {spot.status}")

    except Spot.DoesNotExist:
        print("Spot dengan nomor 1 tidak ditemukan.")
    except Exception as e:
        print("Gagal memproses pesan:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()
