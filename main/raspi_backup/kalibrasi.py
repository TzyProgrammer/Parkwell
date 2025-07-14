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

# Flags: status buzzer dimatikan oleh admin
admin_buzzer_off_flags = { slot: False for _, _, _, slot in sensors }

# Flags: slot sedang di-disable oleh admin
buzzer_disabled_flags = { slot: False for _, _, _, slot in sensors }

# Flags: kendaraan terdeteksi selama delay
pre_buzzer_flags = { slot: 0 for _, _, _, slot in sensors }

DELAY_THRESHOLD = 5  # detik
DISTANCE_THRESHOLD = 30  # cm (threshold jarak)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

broker_address = "192.168.18.11"  # IP broker (laptop)
client = mqtt.Client()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("[MQTT] âœ… Terhubung ke broker")
    for _, _, _, slot in sensors:
        topic = f"parkir/slot{slot}/buzzer"
        client.subscribe(topic)
        print(f"[MQTT] ðŸ“¡ Subscribed ke: {topic}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    if topic.startswith("parkir/slot") and topic.endswith("/buzzer"):
        slot = topic.replace("parkir/slot", "").replace("/buzzer", "")
        if payload.lower() == "off":
            admin_buzzer_off_flags[slot] = True
            print(f"[BUZZER] âœ‹ Admin mematikan buzzer slot {slot}")
        elif payload.lower() == "disabled":
            buzzer_disabled_flags[slot] = True
            print(f"[BUZZER] âŒ Slot {slot} dinonaktifkan")
        elif payload.lower() == "enable":
            buzzer_disabled_flags[slot] = False
            admin_buzzer_off_flags[slot] = False
            print(f"[BUZZER] âœ… Slot {slot} diaktifkan kembali")

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

            if buzzer_disabled_flags[slot]:
                GPIO.output(buzzer, GPIO.LOW)
                print(f"[BUZZER] ðŸ”‡ Slot {slot} DISABLED - buzzer tidak akan aktif")
                continue

            if distance < DISTANCE_THRESHOLD:
                pre_buzzer_flags[slot] += 1
                print(f"[DETECT] Slot {slot} - kendaraan terdeteksi {pre_buzzer_flags[slot]}x")

                if pre_buzzer_flags[slot] >= DELAY_THRESHOLD:
                    if not admin_buzzer_off_flags[slot]:
                        GPIO.output(buzzer, GPIO.HIGH)
                        print(f"[BUZZER] ðŸ”Š Slot {slot} HIDUP (setelah delay)")
                    else:
                        GPIO.output(buzzer, GPIO.LOW)
                        print(f"[BUZZER] âœ‹ Slot {slot} DIMATIKAN ADMIN")
                else:
                    GPIO.output(buzzer, GPIO.LOW)
                    print(f"[BUZZER] â³ Slot {slot} Menunggu delay...")
            else:
                pre_buzzer_flags[slot] = 0
                GPIO.output(buzzer, GPIO.LOW)
                admin_buzzer_off_flags[slot] = False  # reset
                print(f"[BUZZER] â›” Slot {slot} MATI")

            time.sleep(0.2)
        print("=" * 40)
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    client.loop_stop()
    print("[EXIT] Sensor dihentikan.")
