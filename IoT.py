import network
import urequests
import time
from machine import Pin, ADC, time_pulse_us

# === Configuration ===
SSID = "The Plug"
PASSWORD = "Warchief"
BACKEND_URL = "http://192.168.137.1:5000/update_sensors"

TEMP_THRESHOLD = 27
PRESENCE_THRESHOLD_CM = 100
LIGHT_THRESHOLD = 30  # Light % below which it's considered dark

# === Wi-Fi Setup ===
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)

    print("[INFO] Connecting to Wi-Fi...")
    wlan.connect(SSID, PASSWORD)
    for _ in range(10):
        if wlan.isconnected():
            print("[INFO] Wi-Fi Connected:", wlan.ifconfig())
            return wlan
        print("[INFO] Waiting for Wi-Fi...")
        time.sleep(1)

    raise RuntimeError("[ERROR] Failed to connect to Wi-Fi")

# === Sensor & Actuator Setup ===
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

TRIG = Pin(13, Pin.OUT)
ECHO = Pin(12, Pin.IN)

fan = Pin(14, Pin.OUT)
fan.value(0)

led = Pin(27, Pin.OUT)
led.value(0)

# === Distance Measurement ===
def measure_distance():
    TRIG.off()
    time.sleep_us(2)
    TRIG.on()
    time.sleep_us(10)
    TRIG.off()
    try:
        duration = time_pulse_us(ECHO, 1, 30000)
        if duration <= 0:
            return -1
        return round((duration / 2) / 29.1, 2)
    except Exception as e:
        print("[ERROR] Ultrasonic:", e)
        return -1

# === Main Loop ===
try:
    wlan = connect_wifi()

    while True:
        try:
            if not wlan.isconnected():
                print("[INFO] Reconnecting Wi-Fi...")
                wlan = connect_wifi()

            # Placeholder temperature (DHT11 disabled)
            temp = 25

            light_raw = ldr.read()
            light_percent = round((light_raw / 4095) * 100)

            distance = measure_distance()
            presence = 0 < distance < PRESENCE_THRESHOLD_CM

            # Control fan
            fan.value(1 if temp >= TEMP_THRESHOLD else 0)
            fan_state = "ON" if fan.value() else "OFF"

            # Control LED based on light
            led.value(1 if light_percent < LIGHT_THRESHOLD else 0)
            led_state = "ON" if led.value() else "OFF"

            # Print sensor status
            print("\n===============================")
            print("📡 SENSOR STATUS UPDATE")
            print(f"🌡️  Temperature    : {temp} °C")
            print(f"💡 Light Level     : {light_percent} %")
            print(f"📏 Distance        : {distance} cm")
            print(f"🚶 Presence        : {'Yes' if presence else 'No'}")
            print(f"🌀 Fan             : {fan_state}")
            print(f"💡 LED             : {led_state}")
            print("===============================\n")

            # Send data to backend
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
                print("[INFO] Server response:", response.text)
                response.close()
            except Exception as post_err:
                print("[WARN] POST error:", post_err)

        except Exception as loop_err:
            print("[WARN] Loop error:", loop_err)

        time.sleep(5)

except Exception as fatal:
    print("[FATAL] Startup error:", fatal)
