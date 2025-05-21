from gpiozero import DistanceSensor
import time
import paho.mqtt.client as mqtt

# Sesuaikan dengan pin yang kamu gunakan
# trigger=23, echo=24 artinya BCM23 = GPIO23, BCM24 = GPIO24
sensor = DistanceSensor(echo=24, trigger=23, max_distance=2)

client = mqtt.Client()
client.connect("localhost", 1883, 60)

try:
    while True:
        # sensor.distance mengembalikan nilai 0.0 - 1.0 (berdasarkan max_distance)
        distance_cm = round(sensor.distance * 100, 2)
        print(f"Jarak: {distance_cm} cm")

        client.publish("parkir/slot1", str(distance_cm))
        time.sleep(2)

except KeyboardInterrupt:
    print("Dihentikan oleh user.")
