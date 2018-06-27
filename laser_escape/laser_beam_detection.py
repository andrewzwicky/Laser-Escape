import time

LDR_THRESHOLD = 0.2
LASER_BREAK_BOUNCE_TIME = 5


def laser_beam_penalties(laser_times, light_sensors, penalties):
    beams_broken = [sensor.value <= LDR_THRESHOLD for sensor in light_sensors]

    lasers_tripped = 0

    for i, (broken, bounce_timer) in enumerate(zip(beams_broken, laser_times)):
        if broken and bounce_timer <= 0:
            lasers_tripped += 1
            laser_times[i] = LASER_BREAK_BOUNCE_TIME
        else:
            # laser_times[i] -= LDR_QUERY_DELAY
            laser_times[i] = min(0, laser_times[i])

    penalties += lasers_tripped

    return beams_broken, penalties
