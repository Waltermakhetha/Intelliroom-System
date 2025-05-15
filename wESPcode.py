import network
import urequests
import time
from machine import Pin, ADC, time_pulse_us
# import dht  # DHT11 temporarily disabled

# === Configuration ===
SSID = "The Plug"
PASSWORD = "Warchief"
BACKEND_URL = "http://172.16.21.214:5000/update_sensors"

TEMP_THRESHOLD = 27
PRESENCE_THRESHOLD_CM = 100
POST_TIMEOUT = 3000  # ms

# === Wi-Fi Setup ===
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)

    print("🔄 Connecting to Wi-Fi...")
    wlan.connect(SSID, PASSWORD)

    for _ in range(10):
        if wlan.isconnected():
            print("✅ Wi-Fi Connected:", wlan.ifconfig())
            return wlan
        print("🔌 Waiting for Wi-Fi...")
        time.sleep(1)

    raise RuntimeError("❌ Failed to connect to Wi-Fi")

# === Sensor Setup ===
# dht_sensor = dht.DHT11(Pin(15))  # GPIO 15 - TEMPORARILY DISABLED
ldr = ADC(Pin(34))                 # GPIO 34
ldr.atten(ADC.ATTN_11DB)           # 0–3.3V range

TRIG = Pin(13, Pin.OUT)            # Ultrasonic TRIG
ECHO = Pin(12, Pin.IN)             # Ultrasonic ECHO

fan = Pin(14, Pin.OUT)             # GPIO 14
fan.value(0)

# === Measure distance ===
def measure_distance():
    TRIG.off()
    time.sleep_us(2)
    TRIG.on()
    time.sleep_us(10)
    TRIG.off()

    try:
        duration = time_pulse_us(ECHO, 1, 30000)  # Max wait 30ms
        if duration <= 0:
            return -1
        return round((duration / 2) / 29.1, 2)
    except Exception as e:
        print("❗ Ultrasonic error:", e)
        return -1

# === Main ===
try:
    wlan = connect_wifi()

    while True:
        try:
            if not wlan.isconnected():
                print("📡 Reconnecting Wi-Fi...")
                wlan = connect_wifi()

            # Sensor Readings
            # dht_sensor.measure()
            # temp = dht_sensor.temperature()
            temp = 25  # Placeholder for testing without DHT11

            light_raw = ldr.read()
            light_percent = round((light_raw / 4095) * 100)

            distance = measure_distance()
            presence = 0 < distance < PRESENCE_THRESHOLD_CM

            # Fan Control
            fan.value(1 if temp >= TEMP_THRESHOLD else 0)
            fan_state = "ON" if fan.value() else "OFF"

            print(f"📤 Temp: {temp}°C | Light: {light_percent}% | Distance: {distance} cm | Presence: {presence} | Fan: {fan_state}")

            # POST Data
            try:
                response = urequests.post(
                    BACKEND_URL,
                    json={
                        "temperature": temp,
                        "light_level": light_percent,
                        "presence": presence,
                        "distance_cm": distance
                    },
                    headers={"Content-Type": "application/json"},
                )
                print("✅ Server response:", response.text)
                response.close()
            except Exception as post_err:
                print("⚠️ POST error:", post_err)

        except Exception as err:
            print("⚠️ Read loop error:", err)

        time.sleep(5)

except Exception as fatal:
    print("❌ Startup Error:", fatal)
