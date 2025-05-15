from flask import Flask, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests, useful for frontend integration

# === Simulated endpoints for frontend preview/testing ===
@app.route('/')
def home():
    return "Welcome to the IntelliRoom Dashboard!"

@app.route('/temperature_sensing', methods=['GET'])
def temperature(): 
    """Simulate temperature sensor reading."""
    return jsonify({
        "temperature": round(random.uniform(20.0, 30.0), 2)
    })

@app.route('/light_sensing', methods=['GET'])
def light():
    """Simulate light sensor reading."""
    return jsonify({
        "light_level": random.randint(0, 100)
    })

@app.route('/presence_detection', methods=['GET'])
def presence():
    """Simulate ultrasonic sensor presence detection."""
    simulated_distance_cm = random.uniform(30.0, 150.0)
    presence_detected = simulated_distance_cm < 100.0
    return jsonify({
        "presence": presence_detected,
        "distance_cm": round(simulated_distance_cm, 2)
    })

# === 🔧 Actual data receiver for ESP32 ===
@app.route('/update_sensors', methods=['POST'])
def update_sensors():
    data = request.get_json()
    print("\n[📥] Received sensor data from ESP32:")
    print(data)
    return jsonify({"message": "Sensor data received successfully"}), 200

# === Run the server ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
