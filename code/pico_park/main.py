import network
import time
import urequests
from machine import Pin
from hcsr04 import HCSR04
import secrets

SSID = secrets.SSID
PASSWORD = secrets.PASSWORD
GATE_IP = secrets.GATE_IP
GATE_URL = f"http://{GATE_IP}"

# ultrasonic sensor config
# (trigger, echo)
SENSORS_CONFIG = [
    (7, 8),   # sen 1
    (9, 10),  # sen 2
    (11, 12)  # sen 3
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
        print('[STATUS]  Waiting for connection...')
        time.sleep(1)
        
    if wlan.status() != 3:
        raise RuntimeError('[ERROR]   Network connection failed')
    else:
        status = wlan.ifconfig()
        print('[SUCCESS] IP = ' + status[0])

def main():
    print("[STATUS]  Initializing Parking Sensors...")
    
    # init sensors
    sensors = []
    for trig, echo in SENSORS_CONFIG:
        sensors.append(HCSR04(trigger_pin=trig, echo_pin=echo))
    
    while True:
        try:
            connect_wifi()
            break
        except Exception as e:
            print(f"[ERROR]   Unable to connect to WiFi: {e}")
            time.sleep(5)
        
    while True:
        occupied_count = 0
        status_list = []
        
        print("[STATUS]  Scanning Spots...")
        for i, sensor in enumerate(sensors):
            try:
                distance = sensor.distance_cm()
                is_occupied = distance < OCCUPIED_THRESHOLD_CM and distance > 0
                status_list.append(is_occupied)
                
                status_str = "OCCUPIED" if is_occupied else "EMPTY"
                print(f"[STATUS]  Spot {i+1}: {status_str} ({distance:.1f} cm)")
                
                if is_occupied:
                    occupied_count += 1
            except OSError as e:
                print(f"[ERROR]   Spot {i+1}: {e}")
            
            time.sleep(0.06) # 60ms delay to prevent cross-talk
                
        print(f"[STATUS]  Total Occupied: {occupied_count}/{len(sensors)}")
        
        # send data to pico_gate
        try:
            url = f"{GATE_URL}/?occupied={occupied_count}"
            print(f"[STATUS]  Sending to {url}...")
            response = urequests.get(url)
            print(f"[STATUS]  Response: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"[ERROR]   Communication Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    main()
