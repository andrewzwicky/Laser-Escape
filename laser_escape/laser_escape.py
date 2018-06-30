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

# Pins
from laser_beam_detection import laser_beam_penalties

BUZZER_PIN = 22
LDR_PINS = [18, 24, 12, 19, 5, 16, 23, 26, 13]
TIMER_BUTTON_PIN = 20
NAME_ENTRY_BUTTON_PIN = 21

LDR_WIRE_COLORS = ['WHITE', 'BROWN', 'GRAY', 'GREEN', 'RED', 'YELLOW', 'PURPLE', 'BLUE', 'ORANGE']
LDR_COLOR_DICT = {pin: color for pin, color in zip(LDR_PINS, LDR_WIRE_COLORS)}

"""
Wiring:
LDR - GPIO (LDR_PIN) to 3.3V (direction doesn't matter)
CAPACITOR - GPIO (LDR_PIN) (long leg), GND (short leg)
BUZZER - GPIO (OUTPUT_PIN) (long leg), GND (short leg)
"""

# LCD Colors
RED = (1, 0, 0)
GREEN = (0, 1, 0)
BLUE = (0, 0, 1)
WHITE = (1, 1, 1)
PURPLE = (1, 0, 1)
YELLOW = (1, 1, 0)

# LCD Positions
START_TOP_ROW = (0, 0)
START_BOTTOM_ROW = (0, 1)

# Thresholds & Timers
TRIP_TIME_PENALTY = 5
LDR_QUERY_DELAY = 0.005

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


def timer_button_press_loop(_):
    global TIMER_BUTTON_PRESSED
    TIMER_BUTTON_PRESSED = True


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TIMER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(NAME_ENTRY_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

    GPIO.add_event_detect(TIMER_BUTTON_PIN,
                          GPIO.BOTH,
                          callback=timer_button_press_loop,
                          bouncetime=250)

    GPIO.add_event_detect(NAME_ENTRY_BUTTON_PIN,
                          GPIO.FALLING,
                          callback=name_entry_press_loop,
                          bouncetime=250)

    light_sensors = [LightSensor(pin) for pin in LDR_PINS]

    return light_sensors


def get_best_record():
    try:
        with open(RESULTS_FILE, 'r') as times_file:
            run_reader = csv.reader(times_file)
            times = [row[-1] for row in run_reader]
        return float(min(times)) if times else None

    except FileNotFoundError:
        return None


def high_level_loop():
    try:
        # logic is done in a thread so that
        # the buttons can be added on interrupts
        threading.Thread(target=logic_loop).start()
        while True:
            time.sleep(100)
    finally:
        GPIO.cleanup()


def name_entry(lcd):
    lcd.clear()
    lcd.set_color(*WHITE)
    lcd.message("NAME?")
    lcd.set_cursor(*START_BOTTOM_ROW)

    runner_name = ''

    while True:
        last_key = getch()

        if last_key == '\r' or last_key == '\x03':
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


def set_name_and_time(lcd, color, runner_name, display_time):
    lcd.clear()
    lcd.set_color(*color)
    lcd.set_cursor(*START_TOP_ROW)
    lcd.message(format_time(display_time))
    lcd.set_cursor(*START_BOTTOM_ROW)
    lcd.message(runner_name)


def logic_loop():
    global TIMER_BUTTON_PRESSED
    global NAME_BUTTON_PRESSED

    light_sensors = setup()

    lcd = Adafruit_CharLCDPlate()
    lcd.create_char(1, [0, 31, 31, 31, 31, 31, 0, 0])

    program_state = ProgramState.READY_TO_GO
    next_state = ProgramState.READY_TO_GO
    previous_state = ProgramState.NAME_ENTRY

    runner_name = ''
    start_time = None

    penalties = 0
    laser_times = [0 for _ in range(len(light_sensors))]

    while True:
        if program_state != previous_state:
            print("{0}->{1}".format(previous_state, program_state))
        if program_state == ProgramState.IDLE:
            if previous_state != ProgramState.IDLE:
                lcd.set_color(*WHITE)
                lcd.set_cursor(*START_TOP_ROW)
                lcd.message("READY FOR")
                lcd.set_cursor(*START_BOTTOM_ROW)
                lcd.message("FIRST RUNNER!")

            if NAME_BUTTON_PRESSED:
                next_state = ProgramState.NAME_ENTRY

        elif program_state == ProgramState.NAME_ENTRY:
            runner_name = name_entry(lcd)
            next_state = ProgramState.READY_TO_GO

        elif program_state == ProgramState.READY_TO_GO:
            if previous_state != ProgramState.READY_TO_GO:
                set_name_and_time(lcd, YELLOW, runner_name, 0)

            # start executing lasers early, so there's not a big time penalty at the beginning
            beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                        light_sensors,
                                                                        penalties,
                                                                        time.time())

            if TIMER_BUTTON_PRESSED:
                next_state = ProgramState.TIMING

        elif program_state == ProgramState.TIMING:
            if previous_state != ProgramState.TIMING:
                lcd.set_color(*GREEN)
                start_time = time.time()
                laser_times = [start_time for _ in range(len(light_sensors))]
                penalties = 0

            beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                        light_sensors,
                                                                        penalties,
                                                                        time.time())

            if any(beams_broken):
                lcd.set_color(*RED)
                GPIO.output(BUZZER_PIN, True)
            else:
                lcd.set_color(*GREEN)
                GPIO.output(BUZZER_PIN, False)

            duration = time.time() - start_time + (penalties * TRIP_TIME_PENALTY)

            lcd.set_cursor(*START_TOP_ROW)
            lcd.message(format_time(duration))

            if TIMER_BUTTON_PRESSED:
                last_duration = duration
                next_state = ProgramState.JUST_FINISHED
            else:
                time.sleep(LDR_QUERY_DELAY)

        elif program_state == ProgramState.JUST_FINISHED:
            if previous_state != ProgramState.JUST_FINISHED:
                set_name_and_time(lcd, WHITE, runner_name, last_duration)
                write_attempt_to_file(runner_name, last_duration, penalties, TRIP_TIME_PENALTY)

            if NAME_BUTTON_PRESSED:
                next_state = ProgramState.NAME_ENTRY

        previous_state = program_state
        program_state = next_state

        TIMER_BUTTON_PRESSED = False
        NAME_BUTTON_PRESSED = False


def format_time(duration: float):
    return str(datetime.timedelta(seconds=duration))[2:9]


def write_attempt_to_file(runner_name, last_duration, penalties, penalty_trip_time):
    with open(RESULTS_FILE, 'a') as times_file:
        run_writer = csv.writer(times_file)
        run_writer.writerow(
            [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             runner_name,
             last_duration,
             penalties,
             penalty_trip_time])


if __name__ == "__main__":
    high_level_loop()
