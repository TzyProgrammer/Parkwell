import time
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

# Daftar sensor: [(TRIG, ECHO, BUZZER, slot_number)]
sensors = [
    (23, 24, 18, "1"),
    (17, 27, 16, "2"),
    (5, 6, 20, "3"),
    (19, 26, 21, "4")
]

# Flags untuk status buzzer dimatikan oleh admin
admin_buzzer_off_flags = {
    "1": False,
    "2": False,
    "3": False,
    "4": False
}

# Flags untuk status kendaraan terdeteksi terus selama delay
pre_buzzer_flags = {
    "1": 0,
    "2": 0,
    "3": 0,
    "4": 0
}

DELAY_THRESHOLD = 10  # detik
DISTANCE_THRESHOLD = 30  # cm (testing)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

broker_address = ""  # IP broker (laptop)
client = mqtt.Client()

# Callback MQTT
def on_connect(client, userdata, flags, rc):
    print("[MQTT] ? Terhubung ke broker")
    for _, _, _, slot in sensors:
        topic = f"parkir/slot{slot}/buzzer"
        client.subscribe(topic)
        print(f"[MQTT] ?? Subscribed ke: {topic}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic.startswith("parkir/slot") and topic.endswith("/buzzer"):
        slot = topic.replace("parkir/slot", "").replace("/buzzer", "")
        if payload.lower() == "off":
            admin_buzzer_off_flags[slot] = True
            print(f"[BUZZER] ?? Admin mematikan buzzer slot {slot}")

client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address, 1883, 60)
client.loop_start()

# Setup pin
for trig, echo, buzzer, _ in sensors:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.output(buzzer, GPIO.LOW)

def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    pulse_start = time.time()
    timeout = pulse_start + 0.04
    while GPIO.input(echo) == 0 and time.time() < timeout:
        pulse_start = time.time()
    while GPIO.input(echo) == 1 and time.time() < timeout:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    return round(pulse_duration * 17150, 2)

# Loop utama
try:
    while True:
        for trig, echo, buzzer, slot in sensors:
            distance = get_distance(trig, echo)
            print(f"[SENSOR] Slot {slot} - {distance} cm")

            topic = f"parkir/slot{slot}"
            client.publish(topic, str(distance))

            if distance < DISTANCE_THRESHOLD:
                pre_buzzer_flags[slot] += 1
                print(f"[DETECT] Slot {slot} - kendaraan terdeteksi {pre_buzzer_flags[slot]}x")

                if pre_buzzer_flags[slot] >= DELAY_THRESHOLD:
                    if not admin_buzzer_off_flags[slot]:
                        GPIO.output(buzzer, GPIO.HIGH)
                        print(f"[BUZZER] Slot {slot} ?? HIDUP (setelah delay)")
                    else:
                        GPIO.output(buzzer, GPIO.LOW)
                        print(f"[BUZZER] Slot {slot} ? DIMATIKAN ADMIN")
                else:
                    GPIO.output(buzzer, GPIO.LOW)  # Jangan nyalakan dulu
                    print(f"[BUZZER] Slot {slot} ? Menunggu delay...")
            else:
                pre_buzzer_flags[slot] = 0
                GPIO.output(buzzer, GPIO.LOW)
                admin_buzzer_off_flags[slot] = False  # Reset jika kendaraan pergi
                print(f"[BUZZER] Slot {slot} ? MATI")

            time.sleep(0.2)
        print("=" * 40)
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    client.loop_stop()
    print("[EXIT] Sensor dihentikan.")
