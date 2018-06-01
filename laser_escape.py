#!/usr/bin/python
# Example using an RGB character LCD connected to an MCP23017 GPIO extender.
import time
import datetime
import threading
from enum import Enum
import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import random
from getch import getch, pause
import csv
from gpiozero import LightSensor
import os

BUZZER_PIN = 23
#LDR_PINS = [26, 19, 13, 16, 6, 27, 17, 4, 21]
TIMER_BUTTON_PIN = 20
NAME_ENTRY_BUTTON_PIN = 21

LDR_THRESHOLD = 0.2

#COLORS = ['WHITE','BROWN', 'GRAY', 'GREEN', 'RED', 'YELLOW', 'PURPLE', 'BLUE','ORANGE']
#COLORS_DICT = {pin:color for pin,color in zip(LDR_PINS, COLORS)}

"""
Wiring: 
LDR - GPIO (LDR_PIN) to 3.3V (direction doesn't matter)
CAPACITOR - GPIO (LDR_PIN) (long leg), GND (short leg)
BUZZER - GPIO (OUTPUT_PIN) (long leg), GND (short leg)
"""

RED = (1,0,0)
GREEN = (0,1,0)
BLUE = (0,0,1)
WHITE = (1,1,1)
PURPLE = (1,0,1)
YELLOW = (1,1,0)

START_TOP_ROW = (0, 0)
START_BOTTOM_ROW = (0, 1)

TIMING_UPDATE_DELAY = 0.1
NEW_RECORD_DELAY = 0.25
LDR_QUERY_DELAY = 0.005

RESULTS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'times.csv')

class ProgramState(Enum):
    IDLE = 0
    NAME_ENTRY = 1
    READY_TO_GO = 2
    TIMING = 3
    JUST_FINISHED = 4
    NEW_RECORD = 5

def ldr_loop():
    global ldrs
    global prev_vals
    
    threading.Timer(LDR_QUERY_DELAY, ldr_loop).start()
    vals = [ldr.value <= LDR_THRESHOLD for ldr in ldrs]
    prev_vals = vals       
        
def update_lcd():
    global runner_name
    global record_time
    global program_state
    global start_time
    global last_duration
    global winner_toggle
    
    if program_state == ProgramState.IDLE:
        lcd.set_color(*WHITE)
    
    if program_state == ProgramState.NEW_RECORD:
        threading.Timer(NEW_RECORD_DELAY, update_lcd).start()
        lcd.set_cursor(10, 0)
        lcd.message('NEW')
        lcd.set_cursor(10, 1)
        lcd.message('RECORD')
        
        if winner_toggle:
            lcd.set_color(*PURPLE)
        else:
            lcd.set_color(*BLUE)
        
        winner_toggle = not winner_toggle
        
    
    elif program_state == ProgramState.NAME_ENTRY:
        time.sleep(NEW_RECORD_DELAY + 0.01)
        lcd.clear()
        lcd.set_color(*WHITE)
        lcd.message("NAME?\n")
        last_key = None
        runner_name = ''
        while True:
            last_key = getch()
            
            if last_key == '\r':
                break
            
            if last_key == '\x03':
                break
                
            if last_key == '\x7f':
                cursor_spot = max(len(runner_name)-1, 0)
                lcd.set_cursor(cursor_spot, 1)
                lcd.message(' ')
                lcd.set_cursor(cursor_spot, 1)
                if runner_name:
                    runner_name = runner_name[:-1]
            else:
                lcd.message(last_key)
                runner_name += last_key
    
    elif program_state == ProgramState.READY_TO_GO:
        lcd.clear()
        lcd.set_color(*YELLOW)
        lcd.message('\n' + runner_name)
        lcd.set_cursor(*START_TOP_ROW)
        lcd.message(format_time(0))
    
    elif program_state == ProgramState.JUST_FINISHED:
        lcd.clear()
        lcd.message('\n' + runner_name)
        lcd.set_cursor(*START_TOP_ROW)
        lcd.message(format_time(last_duration))

        if record_time is None or last_duration < record_time:
            program_state = ProgramState.NEW_RECORD
            record_time = last_duration
        else:
            program_state = ProgramState.IDLE
        
        write_attempt_to_file()
        update_lcd()
    
    elif program_state == ProgramState.TIMING:
        threading.Timer(TIMING_UPDATE_DELAY, update_lcd).start()
        lcd.set_color(*GREEN)
        lcd.set_cursor(*START_TOP_ROW)
        lcd.message(format_time(time.time() - start_time))


def format_time(duration: float):
    return str(datetime.timedelta(seconds=duration))[2:9]
    
        
def name_entry_press(_):
    global program_state
    
    if program_state == ProgramState.IDLE or \
       program_state == ProgramState.NEW_RECORD:
        program_state = ProgramState.NAME_ENTRY
        update_lcd()
        program_state = ProgramState.READY_TO_GO
        update_lcd()
        
def timer_button_press(_):
    global runner_name
    global program_state
    global start_time
    global last_duration
    
    if program_state == ProgramState.READY_TO_GO:
        start_time = time.time()
        last_duration = None
        program_state = ProgramState.TIMING
        update_lcd()

    elif program_state == ProgramState.TIMING:
        last_duration = time.time() - start_time
        program_state = ProgramState.JUST_FINISHED

def write_attempt_to_file():
    global runner_name
    global start_time
    global last_duration
    
    with open(RESULTS_FILE, 'a') as times_file:
        run_writer = csv.writer(times_file)
        run_writer.writerow(
            [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             runner_name,
             last_duration])
              
def get_best_record():
    try:
        with open(RESULTS_FILE, 'r') as times_file:
            run_reader = csv.reader(times_file)
            times = [row[-1] for row in run_reader]
        return float(min(times)) if times else None

    except FileNotFoundError:
        return None

if __name__=="__main__":
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(TIMER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(NAME_ENTRY_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

    GPIO.add_event_detect(TIMER_BUTTON_PIN, GPIO.BOTH, callback=timer_button_press, bouncetime=250)
    GPIO.add_event_detect(NAME_ENTRY_BUTTON_PIN, GPIO.FALLING, callback=name_entry_press, bouncetime=250)
    
    lcd = LCD.Adafruit_CharLCDPlate()
    program_state = ProgramState.IDLE
    runner_name = ""
    start_time = None
    last_duration = None
    winner_toggle = True
    record_time = get_best_record()
    
    #ldrs = [LightSensor(pin) for pin in LDR_PINS]
    #prev_vals = [False for _ in LDR_PINS]
    
    #threading.Timer(LDR_QUERY_DELAY, ldr_loop).start()

    try:
        lcd.message("READY FOR RUNNER")
        update_lcd()
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        GPIO.cleanup()
    
    GPIO.cleanup()
