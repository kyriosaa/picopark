hey since we're using two separate boards, I've moved the drivers and stuff into their own respective folders.

If you're working on the parking spots, go to the pico_park folder

If you're working on the gate & OLED, go to the pico_gate folder

1. Please update mywifi.py file with wifi you're connecting

2. For testing network only, change TEST_MODE =  True in main.py under pico_park folder


ignore prototype.py, it's leftover from the prototype