from machine import Pin, I2C
import time
import ssd1306
from hcsr04 import HCSR04

OLED_WIDTH    = 128
OLED_HEIGHT   = 32
OLED_SDA_PIN  = 0
OLED_SCL_PIN  = 1

SEN1_TRIG_PIN = 2
SEN1_ECHO_PIN = 3
SEN2_TRIG_PIN = 4
SEN2_ECHO_PIN = 5
SEN3_TRIG_PIN = 6
SEN3_ECHO_PIN = 7

LED1_PIN = 8
LED2_PIN = 9
LED3_PIN = 10

# ultrasonic distance threshold
OCCUPIED_THRESHOLD_CM = 10

# init stuff
i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

sensor1 = HCSR04(trigger_pin=SEN1_TRIG_PIN, echo_pin=SEN1_ECHO_PIN)
sensor2 = HCSR04(trigger_pin=SEN2_TRIG_PIN, echo_pin=SEN2_ECHO_PIN)
sensor3 = HCSR04(trigger_pin=SEN3_TRIG_PIN, echo_pin=SEN3_ECHO_PIN)
sensors = [sensor1, sensor2, sensor3]

led1 = Pin(LED1_PIN, Pin.OUT)
led2 = Pin(LED2_PIN, Pin.OUT)
led3 = Pin(LED3_PIN, Pin.OUT)
leds = [led1, led2, led3]

def update_display(occupied_count, total_spots):
    # ts will be drawn in the main loop based on actual status
    oled.fill(0)
    oled.text("Smart Parking", 10, 0)
    oled.text("Occupied:", 0, 20)
    oled.text(f"{occupied_count}/{total_spots}", 80, 20)
    oled.text("Spots:", 0, 40)
    oled.show()

def main():
    print("Starting Smart Parking System...")
    
    while True:
        occupied_count = 0
        spot_status = []
        
        # read each ultrasonic sensor
        for i, sensor in enumerate(sensors):
            try:
                distance = sensor.distance_cm()
                is_occupied = distance < OCCUPIED_THRESHOLD_CM
                spot_status.append(is_occupied)
                
                if is_occupied:
                    occupied_count += 1
                    print(f"Spot {i+1}: Occupied ({distance:.1f}cm)")
                else:
                    print(f"Spot {i+1}: Empty ({distance:.1f}cm)")
                    
            except OSError as e:
                print(f"Spot {i+1}: Error reading sensor")
                spot_status.append(False) # assume empty on error

        # update oled
        oled.fill(0)
        oled.text("Smart Parking", 10, 0)
        oled.text(f"Occupied: {occupied_count}/3", 10, 20)
        oled.show()

        # update led
        for i, is_occupied in enumerate(spot_status):
            leds[i].value(1 if is_occupied else 0)
        
        time.sleep(1)

if __name__ == "__main__":
    main()