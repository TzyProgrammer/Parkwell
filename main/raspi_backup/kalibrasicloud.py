import time
import json
import requests
import RPi.GPIO as GPIO

# ------------------------ Konfigurasi Sensor ------------------------
sensors = [
    (23, 24, 18, "1"),
    (17, 27, 16, "2"),
    (5, 6, 20, "3"),
    (19, 26, 21, "4")
]

# Flags delay kendaraan
pre_buzzer_flags = { slot: 0 for _, _, _, slot in sensors }

# Threshold
DELAY_THRESHOLD = 5        # Deteksi berturut-turut sebelum nyalakan buzzer
DISTANCE_THRESHOLD = 30    # Jarak maksimum deteksi kendaraan (cm)

# URL REST API
BASE_URL = "https://PBLIF18.pythonanywhere.com"  # Ganti dengan URL kamu
POST_SENSOR_URL = f"{BASE_URL}/api/sensor/"
GET_CONTROL_URL = f"{BASE_URL}/api/buzzer-control/"

# ------------------------ Setup GPIO ------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for trig, echo, buzzer, _ in sensors:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.output(buzzer, GPIO.LOW)

# ------------------------ Fungsi ------------------------
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

def send_distance_to_server(slot, distance):
    try:
        payload = {"slot": slot, "distance": distance}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(POST_SENSOR_URL, data=json.dumps(payload), headers=headers, timeout=5)
        print(f"[HTTP] ? POST Slot {slot} - {distance} cm ? {response.status_code}")
    except Exception as e:
        print(f"[HTTP ERROR] ? Slot {slot} - Gagal kirim: {e}")

def get_buzzer_control_status(slot):
    try:
        url = f"{GET_CONTROL_URL}{slot}/"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("buzzer", "enable")
        return "enable"
    except Exception as e:
        print(f"[ERROR] Gagal polling kontrol buzzer slot {slot}: {e}")
        return "enable"

# ------------------------ Loop Utama ------------------------
try:
    while True:
        for trig, echo, buzzer, slot in sensors:
            distance = get_distance(trig, echo)
            print(f"[SENSOR] Slot {slot} - {distance} cm")

            # Kirim ke server
            send_distance_to_server(slot, distance)

            # Ambil status kontrol dari server
            control_status = get_buzzer_control_status(slot)

            if control_status == "disabled":
                GPIO.output(buzzer, GPIO.LOW)
                print(f"[BUZZER] ?? Slot {slot} DISABLED via Server")
                continue

            if distance < DISTANCE_THRESHOLD:
                pre_buzzer_flags[slot] += 1
                print(f"[DETECT] Slot {slot} - Terdeteksi {pre_buzzer_flags[slot]}x")

                if pre_buzzer_flags[slot] >= DELAY_THRESHOLD:
                    if control_status == "off":
                        GPIO.output(buzzer, GPIO.LOW)
                        print(f"[BUZZER] ? Slot {slot} DIMATIKAN ADMIN via Server")
                    else:
                        GPIO.output(buzzer, GPIO.HIGH)
                        print(f"[BUZZER] ?? Slot {slot} HIDUP (setelah delay)")
                else:
                    GPIO.output(buzzer, GPIO.LOW)
                    print(f"[BUZZER] ? Slot {slot} Menunggu delay...")
            else:
                pre_buzzer_flags[slot] = 0
                GPIO.output(buzzer, GPIO.LOW)
                print(f"[BUZZER] ?? Slot {slot} MATI")

            time.sleep(0.2)
        print("=" * 40)
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("[EXIT] Sensor dihentikan.")
