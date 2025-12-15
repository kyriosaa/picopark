print("=== THIS IS Client PICO ===")

import time
import network
import urequests
import mywifi as secrets

SSID = secrets.SSID
PASSWORD = secrets.PASSWORD

PICO_B_IP = "192.168.0.6"# <-- hard code=> don't forget to change this to Pico B's actual IP
PORT = 80

TOTAL_SLOTS = 6
OCCUPIED_THRESHOLD_CM = 10.0

TEST_MODE = True
TEST_VALUES = [0, 1, 3, 5, 2]

# Only import sensors when needed (prevents ImportError in TEST_MODE)
if not TEST_MODE:
    from hcsr04 import HCSR04
    sensors = [
        HCSR04(trigger_pin=7,  echo_pin=8),
        HCSR04(trigger_pin=9,  echo_pin=10),
        HCSR04(trigger_pin=11, echo_pin=12),
        HCSR04(trigger_pin=13, echo_pin=14),
        HCSR04(trigger_pin=15, echo_pin=16),
        HCSR04(trigger_pin=17, echo_pin=18),
    ]

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Pico A connecting to Wi-Fi...")
    while not wlan.isconnected():
        time.sleep(0.5)

    ip = wlan.ifconfig()[0]
    print("Pico A connected, IP:", ip)

def count_occupied_slots():
    occupied = 0
    for idx, sensor in enumerate(sensors):
        try:
            distance = sensor.distance_cm()
            print("Slot", idx + 1, "distance:", distance, "cm")
            if distance < OCCUPIED_THRESHOLD_CM:
                occupied += 1
        except OSError:
            print("Slot", idx + 1, "sensor error")
    return occupied

def send_to_pico_b(occupied):
    url = "http://{}:{}/?occupied={}".format(PICO_B_IP, PORT, occupied)
    print("Sending to Pico B:", url)

    r = None
    try:
        r = urequests.get(url)
    finally:
        if r:
            r.close()

def main():
    connect_wifi()

    idx = 0
    while True:
        if TEST_MODE:
            v = TEST_VALUES[idx % len(TEST_VALUES)]
            idx += 1
            print("TEST occupied =", v)
            try:
                send_to_pico_b(v)
            except Exception as e:
                print("HTTP send failed:", e)
            time.sleep(3)#send every 3 sec for test mode
        else:
            occupied = count_occupied_slots()
            print("Occupied slots:", occupied, "/", TOTAL_SLOTS)
            try:
                send_to_pico_b(occupied)
            except Exception as e:
                print("HTTP send failed:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()