import network
import socket
import time
import _thread
import machine
import secrets
from machine import Pin, I2C
import ssd1306

SSID = secrets.SSID
PASSWORD = secrets.PASSWORD
PORT = 80

OLED_WIDTH = 128
OLED_HEIGHT = 32
OLED_SDA_PIN = 0
OLED_SCL_PIN = 1
i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# this queue is for passing data from Core 0 (server) to Core 1 (worker)
job_queue = []
# lock for thread safety when accessing the queue
queue_lock = _thread.allocate_lock()

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
        return status[0]

def update_oled(data_to_process):
    oled.fill(0)
    oled.text("Occupied Spots", 10, 0)
    oled.text(f"{data_to_process}/6", 55, 20)
    oled.show()

# runs the networking functions
# simple HTTP server to listen for requests
def core0_task(ip):
    addr = socket.getaddrinfo('0.0.0.0', PORT)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print(f'[Core 0] Server listening on {ip}:{PORT}')

    while True:
        try:
            cl, addr = s.accept()
            print('[Core 0] Client connected from', addr)
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

                print(f"[Core 0] Request received. Spots: {occupied_count}")
                
                # add task to queue for Core 1
                with queue_lock:
                    job_queue.append(occupied_count)
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nUpdated"
                cl.send(response)
            
            cl.close()
        except OSError as e:
            cl.close()
            print('Connection closed')

# runs the IO functions (gate & OLED)
# constantly checks the queue for new jobs
def core1_task():
    print("[Core 1] Worker thread started.")
    
    while True:
        data_to_process = None
        
        # check for new data
        with queue_lock:
            if job_queue:
                data_to_process = job_queue.pop(0)
        
        if data_to_process:
            print(f"[Core 1] Processing received data: {data_to_process}")
            
            # update oled
            update_oled(data_to_process)
            
            print(f"[Core 1] Task complete.")
        
        time.sleep(0.1)

def main():
    try:
        ip = connect_wifi()
        _thread.start_new_thread(core1_task, ())
        core0_task(ip)
        
    except KeyboardInterrupt:
        machine.reset()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
