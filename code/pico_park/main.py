import network
import time
import urequests
from machine import Pin
from hcsr04 import HCSR04
import secrets

# Network Settings
SSID = secrets.SSID
PASSWORD = secrets.PASSWORD
GATE_IP = secrets.GATE_IP
GATE_URL = f"http://{GATE_IP}"

# Sensor Configuration (Pins from prototype.py)
# Trigger, Echo
SENSORS_CONFIG = [
    (7, 8),   # Sensor 1
    (9, 10),  # Sensor 2
    (11, 12)  # Sensor 3
]

OCCUPIED_THRESHOLD_CM = 10

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)
        
    if wlan.status() != 3:
        raise RuntimeError('Network connection failed')
    else:
        status = wlan.ifconfig()
        print('Connected! IP = ' + status[0])

def main():
    print("Initializing Parking Sensors...")
    
    # Initialize Sensors
    sensors = []
    for trig, echo in SENSORS_CONFIG:
        sensors.append(HCSR04(trigger_pin=trig, echo_pin=echo))
        
    try:
        connect_wifi()
    except Exception as e:
        print(f"WiFi Error: {e}")
        # Continue anyway for debugging sensors? No, need wifi.
        # But maybe we retry?
        
    while True:
        occupied_count = 0
        status_list = []
        
        print("\n--- Scanning Spots ---")
        for i, sensor in enumerate(sensors):
            try:
                distance = sensor.distance_cm()
                is_occupied = distance < OCCUPIED_THRESHOLD_CM and distance > 0
                status_list.append(is_occupied)
                
                status_str = "OCCUPIED" if is_occupied else "EMPTY"
                print(f"Spot {i+1}: {status_str} ({distance:.1f} cm)")
                
                if is_occupied:
                    occupied_count += 1
            except OSError as e:
                print(f"Spot {i+1}: Error {e}")
                # Assume empty if error to avoid false positives?
                
        print(f"Total Occupied: {occupied_count}/{len(sensors)}")
        
        # Send data to Gate
        try:
            url = f"{GATE_URL}/?occupied={occupied_count}"
            print(f"Sending to {url}...")
            response = urequests.get(url)
            print(f"Response: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Communication Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    main()
