#!/usr/bin/python
import csv
import datetime
import os
import time
from enum import Enum
import threading

import RPi.GPIO as GPIO
from Adafruit_CharLCD import Adafruit_CharLCDPlate
from getch import getch
from gpiozero import LightSensor

#BUZZER_PIN = 23
LDR_PINS = [18, 24, 12, 19, 5, 16, 23, 26, 13]
TIMER_BUTTON_PIN = 20
NAME_ENTRY_BUTTON_PIN = 21

LDR_THRESHOLD = 0.25

COLORS = ['WHITE', 'BROWN', 'GRAY', 'GREEN', 'RED', 'YELLOW', 'PURPLE', 'BLUE', 'ORANGE']
COLORS_DICT = {pin: color for pin, color in zip(LDR_PINS, COLORS)}

"""
Wiring:
LDR - GPIO (LDR_PIN) to 3.3V (direction doesn't matter)
CAPACITOR - GPIO (LDR_PIN) (long leg), GND (short leg)
BUZZER - GPIO (OUTPUT_PIN) (long leg), GND (short leg)
"""

RED = (1, 0, 0)
GREEN = (0, 1, 0)
BLUE = (0, 0, 1)
WHITE = (1, 1, 1)
PURPLE = (1, 0, 1)
YELLOW = (1, 1, 0)

START_TOP_ROW = (0, 0)
START_BOTTOM_ROW = (0, 1)

TIMING_UPDATE_DELAY = 0.1
NEW_RECORD_DELAY = 0.25
LDR_QUERY_DELAY = 0.05
LASER_BREAK_DEBOUNCE = 5

RESULTS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'times.csv')

class ProgramState(Enum):
    IDLE = 0
    NAME_ENTRY = 1
    READY_TO_GO = 2
    TIMING = 3
    JUST_FINISHED = 4
    NEW_RECORD = 5


TIMER_BUTTON_PRESSED = False
NAME_BUTTON_PRESSED = False


def name_entry_press_loop(_):
    global NAME_BUTTON_PRESSED
    NAME_BUTTON_PRESSED = True
    print("NAME_BUTTON_PRESSED")


def timer_button_press_loop(_):
    global TIMER_BUTTON_PRESSED
    TIMER_BUTTON_PRESSED = True
    print("TIMER_BUTTON_PRESSED")


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TIMER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(NAME_ENTRY_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #GPIO.setup(BUZZER_PIN, GPIO.OUT)

    GPIO.add_event_detect(TIMER_BUTTON_PIN,
                          GPIO.BOTH,
                          callback=timer_button_press_loop,
                          bouncetime=250)

    GPIO.add_event_detect(NAME_ENTRY_BUTTON_PIN,
                          GPIO.FALLING,
                          callback=name_entry_press_loop,
                          bouncetime=250)


def laser_loop(light_sensors):
    while True:
        vals = [sensor.value for sensor in light_sensors]
        print(['{0:<.3f}'.format(v) for v in vals])
        time.sleep(LDR_QUERY_DELAY)


def get_best_record():
    try:
        with open(RESULTS_FILE, 'r') as times_file:
            run_reader = csv.reader(times_file)
            times = [row[-1] for row in run_reader]
        return float(min(times)) if times else None

    except FileNotFoundError:
        return None


def high_level_loop(light_sensors):
    try:
        threading.Thread(args=[light_sensors],target=laser_loop).start()
        threading.Thread(target=logic_loop).start()
        while True:
            time.sleep(100)
    finally:
        print("finally")
        GPIO.cleanup()


def name_entry(lcd):
    lcd.clear()
    lcd.set_color(*WHITE)
    lcd.message("NAME?\n")

    runner_name = 'test'
    return runner_name

    while True:
        last_key = getch()

        if last_key == '\r':
            break

        if last_key == '\x03':
            break

        if last_key == '\x7f':
            cursor_spot = max(len(runner_name) - 1, 0)
            lcd.set_cursor(cursor_spot, 1)
            lcd.message(' ')
            lcd.set_cursor(cursor_spot, 1)
            if runner_name:
                runner_name = runner_name[:-1]
        else:
            lcd.message(last_key)
            runner_name += last_key

    return runner_name


def ready_to_go_init(lcd, runner_name):
    lcd.clear()
    lcd.set_color(*YELLOW)
    lcd.message('\n' + runner_name)
    lcd.set_cursor(*START_TOP_ROW)
    lcd.message(format_time(0))


def just_finished_init(last_duration, lcd, runner_name):
    lcd.clear()
    lcd.message('\n' + runner_name)
    lcd.set_cursor(*START_TOP_ROW)
    lcd.message(format_time(last_duration))


def logic_loop():
    global TIMER_BUTTON_PRESSED
    global NAME_BUTTON_PRESSED

    setup()

    lcd = Adafruit_CharLCDPlate()
    lcd.create_char(1, [0,31,31,31,31,31,0,0])
    program_state = ProgramState.TIMING
    next_state = ProgramState.TIMING
    previous_state = ProgramState.READY_TO_GO
    runner_name = ""
    start_time = None
    laser_times = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    while True:
        if program_state != previous_state:
            print("{0}->{1}".format(previous_state, program_state))
        if program_state == ProgramState.IDLE:
            if previous_state != ProgramState.IDLE:
                lcd.set_color(*WHITE)
                lcd.message("READY FOR")
                lcd.message("\nFIRST RUNNER")

            if NAME_BUTTON_PRESSED:
                next_state = ProgramState.NAME_ENTRY

        elif program_state == ProgramState.NAME_ENTRY:
            runner_name = name_entry(lcd)
            next_state = ProgramState.READY_TO_GO

        elif program_state == ProgramState.READY_TO_GO:
            if previous_state != ProgramState.READY_TO_GO:
                ready_to_go_init(lcd, runner_name)

            if TIMER_BUTTON_PRESSED:
                next_state = ProgramState.TIMING

        elif program_state == ProgramState.TIMING:
            if previous_state != ProgramState.TIMING:
                lcd.set_color(*GREEN)
                start_time = time.time()

            vals = [sensor.value for sensor in light_sensors]
            beams_broken = [val <= LDR_THRESHOLD for val in vals]
#            for i, (broken, laser_time) in enumerate(zip(beams_broken, laser_times)):
#                if broken and laser_time <= 0:
#                    laser_times[i] = LASER_BREAK_DEBOUNCE
#                else:
#                    laser_times[i] -= LDR_QUERY_DELAY
#                    laser_times[i] = min(0, laser_times[i])
#            print({c:'{0:<.2f}'.format(v) for c,v in zip(COLORS, vals)})
            time.sleep(LDR_QUERY_DELAY)

            lcd.set_cursor(*START_TOP_ROW)
            lcd.message(format_time(time.time() - start_time))
            for broken in beams_broken:
                if broken:
                    lcd.message('\x01')
                else:
                    lcd.message(' ')

            if TIMER_BUTTON_PRESSED:
                last_duration = time.time() - start_time
                next_state = ProgramState.JUST_FINISHED

        elif program_state == ProgramState.JUST_FINISHED:
            if previous_state != ProgramState.JUST_FINISHED:
                just_finished_init(last_duration, lcd, runner_name)
                write_attempt_to_file(runner_name, last_duration)

            if NAME_BUTTON_PRESSED:
                next_state = ProgramState.NAME_ENTRY

        previous_state = program_state
        program_state = next_state

        TIMER_BUTTON_PRESSED = False
        NAME_BUTTON_PRESSED = False


def format_time(duration: float):
    return str(datetime.timedelta(seconds=duration))[2:9]


def write_attempt_to_file(runner_name, last_duration):
    with open(RESULTS_FILE, 'a') as times_file:
        run_writer = csv.writer(times_file)
        run_writer.writerow(
            [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             runner_name,
             last_duration])


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    light_sensors = [LightSensor(pin) for pin in LDR_PINS]
    high_level_loop(light_sensors)
