import time
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

# Daftar sensor: [(TRIG, ECHO, slot_number)]
sensors = [
    (23, 24, "slot1"),
    (17, 27, "slot2"),
    (5, 6, "slot3"),
    (19, 26, "slot4")
]

GPIO.setmode(GPIO.BCM)

client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Setup semua pin
for trig, echo, _ in sensors:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)

def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    while GPIO.input(echo) == 0:
        pulse_start = time.time()
    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    return round(pulse_duration * 17150, 2)

try:
    while True:
        for trig, echo, slot_topic in sensors:
            distance = get_distance(trig, echo)
            print(f"{slot_topic} - {distance} cm")
            client.publish(f"parkir/{slot_topic}", str(distance))
            time.sleep(0.2)  # Delay antar-sensor
        print("="*30)
        time.sleep(3)  # Delay antar-siklus

except KeyboardInterrupt:
    GPIO.cleanup()

