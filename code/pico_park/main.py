import network
import time
import urequests
from machine import Pin
from hcsr04 import HCSR04
import config

SSID = config.SSID
PASSWORD = config.PASSWORD
GATE_IP = config.GATE_IP
GATE_URL = f"http://{GATE_IP}"

# ultrasonic sensor config
# (trigger, echo)
SENSORS_CONFIG = [
    (16, 17),  # sen 1
    (18, 19),  # sen 2
    (20, 21),  # sen 3
    (26, 27)   # sen 4
]
LED_PINS = [13, 12, 11, 10]

OCCUPIED_THRESHOLD_CM = 10

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("[STATUS]  Connecting to network...")
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("[STATUS]  Waiting for connection...")
        time.sleep(1)
        
    if wlan.status() != 3:
        raise RuntimeError("[ERROR]   Network connection failed")
    else:
        status = wlan.ifconfig()
        print("[SUCCESS] Connection successful!")
        print("[SUCCESS] IP = " + status[0])

def main():
    print("[STATUS]  Initializing Parking Sensors...")
    
    # init sensors
    sensors = []
    for trig, echo in SENSORS_CONFIG:
        sensors.append(HCSR04(trigger_pin=trig, echo_pin=echo))
    
    # init LEDs
    leds = []
    for pin_num in LED_PINS:
        leds.append(Pin(pin_num, Pin.OUT))

    # heartbeat
    last_occupied_count = -1
    last_send_time = time.ticks_ms()
    HEARTBEAT = 5000
    
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

                # update LED status
                if is_occupied:
                    leds[i].value(1)
                else:
                    leds[i].value(0)
                
                status_str = "OCCUPIED" if is_occupied else "EMPTY"
                print(f"[STATUS]  Spot {i+1}: {status_str} ({distance:.1f} cm)")
                
                if is_occupied:
                    occupied_count += 1
            except OSError as e:
                print(f"[ERROR]   Spot {i+1}: {e}")
                leds[i].value(0)
            
            time.sleep(0.06) # 60ms delay to prevent cross-talk
                
        print(f"[STATUS]  Total Occupied: {occupied_count}/{len(sensors)}")

        # only send the data if the count changed or its been 5 sec
        current_time = time.ticks_ms()
        last_send_comp = time.ticks_diff(current_time, last_send_time)
        
        if occupied_count != last_occupied_count or last_send_comp > HEARTBEAT:
            # send data to pico_gate
            try:
                url = f"{GATE_URL}/?occupied={occupied_count}"
                print(f"[STATUS]  Sending to {url}...")
                response = urequests.get(url)
                print(f"[STATUS]  Response: {response.status_code}")
                response.close()
            except Exception as e:
                print(f"[ERROR]   Communication Error: {e}")
            
        time.sleep(0.1)

if __name__ == "__main__":
    main()
