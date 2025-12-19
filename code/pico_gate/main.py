# for handling the gate & OLED
import network
import socket
import time
import _thread
import machine
import secrets
from machine import Pin, I2C, PWM
import ssd1306

SSID = secrets.SSID
PASSWORD = secrets.PASSWORD
PORT = 80

ENTRANCE_IR_PIN = 16
ENTRANCE_SERVO_PIN = 17
EXIT_IR_PIN = 18
EXIT_SERVO_PIN = 19
GATE_OPEN_DUTY = 8000 
GATE_CLOSE_DUTY = 2000
# 1000-9000 is a safe range to test, usually 1638 (0.5ms) to 8192 (2.5ms)

OLED_WIDTH = 128
OLED_HEIGHT = 32
OLED_SDA_PIN = 0
OLED_SCL_PIN = 1

MAX_SPOTS = 3
current_occupancy = 0

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
        return status[0]

# OLED UPDATE STUFF HERE
def update_oled(oled, data_to_process):
    oled.fill(0)
    oled.text("Occupied Spots", 10, 0)
    oled.text(f"{data_to_process}/{MAX_SPOTS}", 55, 20)
    oled.show()

# runs the networking functions
# simple HTTP server to listen for requests
def core0_task(ip):
    global current_occupancy
    i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
    addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print(f'[Core 0]  Server listening on {ip}:{PORT}')

    while True:
        try:
            cl, addr = s.accept()
            print('[Core 0]  Client connected from', addr)
            request = cl.recv(1024)
            request = str(request)
            
            if 'GET' in request:
                # parse the 'occupied' count from the URL 
                # (ex: /?occupied=2)
                occupied_count = "?"
                if "occupied=" in request:
                    try:
                        start_index = request.find("occupied=") + 9
                        # find th end of number (space or &)
                        end_index = request.find(" ", start_index)
                        if end_index == -1: 
                            end_index = len(request)
                        occupied_count = request[start_index:end_index]
                    except:
                        pass

                print(f"[Core 0]  Request received. Spots: {occupied_count}")
                
                # update occupancy
                if occupied_count.isdigit():
                    current_occupancy = int(occupied_count)
                
                # update oled
                update_oled(oled, occupied_count)
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nUpdated"
                cl.send(response)
            
            cl.close()
        except OSError as e:
            cl.close()
            print('[STATUS]  Connection closed')

# runs the IO functions (gate control)
# checks IR sensors and moves servos
def core1_task():
    print("[Core 1]  Gate Control started.")
    
    entrance_ir = Pin(ENTRANCE_IR_PIN, Pin.IN, Pin.PULL_UP)
    exit_ir = Pin(EXIT_IR_PIN, Pin.IN, Pin.PULL_UP)
    
    entrance_servo = PWM(Pin(ENTRANCE_SERVO_PIN))
    entrance_servo.freq(50)
    exit_servo = PWM(Pin(EXIT_SERVO_PIN))
    exit_servo.freq(50)
    
    # closed on initial state
    entrance_servo.duty_u16(GATE_CLOSE_DUTY)
    exit_servo.duty_u16(GATE_CLOSE_DUTY)
    
    # track when sensors were last blocked
    entrance_last_blocked = time.ticks_add(time.ticks_ms(), -5000)
    exit_last_blocked = time.ticks_add(time.ticks_ms(), -5000)
    
    CLOSE_DELAY_MS = 1000
    
    while True:
        current_time = time.ticks_ms()
        
        # active low for both entrance and exit
        # active low for both entrance and exit
        if entrance_ir.value() == 0:
            if current_occupancy < MAX_SPOTS:
                entrance_servo.duty_u16(GATE_OPEN_DUTY)
                entrance_last_blocked = current_time
            else:
                # FULL - Ensure closed
                entrance_servo.duty_u16(GATE_CLOSE_DUTY)
        else:
            # check delay once sensor clears
            if time.ticks_diff(current_time, entrance_last_blocked) > CLOSE_DELAY_MS:
                entrance_servo.duty_u16(GATE_CLOSE_DUTY)
            else:
                # keep open if within delay window, BUT check occupancy again? 
                # actually, if we opened it, we let them in.
                entrance_servo.duty_u16(GATE_OPEN_DUTY)
                
        if exit_ir.value() == 0:
            exit_servo.duty_u16(GATE_OPEN_DUTY)
            exit_last_blocked = current_time
        else:
            # check delay once sensor clears
            if time.ticks_diff(current_time, exit_last_blocked) > CLOSE_DELAY_MS:
                exit_servo.duty_u16(GATE_CLOSE_DUTY)
            else:
                exit_servo.duty_u16(GATE_OPEN_DUTY)
        
        time.sleep(0.05)

def main():
    try:
        ip = connect_wifi()
        _thread.start_new_thread(core1_task, ())
        core0_task(ip)
        
    except KeyboardInterrupt:
        machine.reset()
    except Exception as e:
        print(f"[ERROR]   {e}")

if __name__ == "__main__":
    main()
