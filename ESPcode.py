import network
import urequests
import time
from machine import Pin, ADC, time_pulse_us
import dht

# === Wi-Fi Setup ===
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)

    print("🔄 Attempting WiFi connection...")
    wlan.connect(ssid, password)

    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        print("🔌 Connecting...")
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print("✅ Connected:", wlan.ifconfig())
    else:
        raise RuntimeError("❌ Failed to connect to WiFi")

# === Connect to Wi-Fi ===
try:
    connect_wifi("The Plug", "Warchief")
except Exception as e:
    print("🚫 Wi-Fi Error:", e)

# === Sensor Setup ===
dht_sensor = dht.DHT11(Pin(15))         # DHT11 on GPIO 15
ldr = ADC(Pin(34))                      # LDR on GPIO 34
ldr.atten(ADC.ATTN_11DB)                # Full 0-3.3V range

# === Fan Setup ===
fan = Pin(14, Pin.OUT)                  # Fan control on GPIO 14
fan.value(0)

# === Ultrasonic Sensor Setup ===
TRIG = Pin(13, Pin.OUT)                 # TRIG on GPIO 13
ECHO = Pin(12, Pin.IN)                  # ECHO on GPIO 12

def measure_distance():
    TRIG.off()
    time.sleep_us(2)
    TRIG.on()
    time.sleep_us(10)
    TRIG.off()

    try:
        duration = time_pulse_us(ECHO, 1, 30000)  # max 30 ms
        if duration <= 0:
            return -1
        distance_cm = (duration / 2) / 29.1
        return round(distance_cm, 2)
    except Exception as e:
        print("❗Ultrasonic error:", e)
        return -1

# === Flask Backend ===
url = "http://172.16.21.214:5000/update_sensors"

# === Thresholds ===
TEMP_THRESHOLD = 27
PRESENCE_THRESHOLD = 100

# === Main Loop ===
try:
    while True:
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()

            light_raw = ldr.read()
            light_percent = round((light_raw / 4095) * 100)

            distance_cm = measure_distance()
            presence = distance_cm > 0 and distance_cm < PRESENCE_THRESHOLD

            # Fan control
            if temp >= TEMP_THRESHOLD:
                fan.value(1)
                print("🌀 Fan ON (Auto)")
            else:
                fan.value(0)
                print("🛑 Fan OFF (Auto)")

            print(f"📤 Sending: {temp}°C, {light_percent}% light, Presence: {presence}, Distance: {distance_cm} cm")

            # POST data
            response = urequests.post(
                url,
                json={
                    "temperature": temp,
                    "light_level": light_percent,
                    "presence": presence,
                    "distance_cm": distance_cm
                },
                headers={"Content-Type": "application/json"},
            )
            print("✅ Server response:", response.text)
            response.close()

        except Exception as sensor_err:
            print("⚠️ Sensor/POST error:", sensor_err)

        time.sleep(5)

except Exception as fatal_err:
    print("❌ Fatal Error:", fatal_err)

