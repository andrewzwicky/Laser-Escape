import time

LDR_THRESHOLD = 0.2
LASER_BREAK_BOUNCE_TIME = 5


def laser_beam_penalties(laser_times, light_sensors, penalties, current_time):
    """
    This method is responsible for determining when beams have been broken, and how many penalties
    will be assessed for breaking lasers.

    :param laser_times:
    :param light_sensors:
    :param penalties:
    :param current_time:
    :return:
    """
    beams_broken = [sensor.value <= LDR_THRESHOLD for sensor in light_sensors]

    lasers_tripped = 0

    for i, (broken, set_time) in enumerate(zip(beams_broken, laser_times)):
        if broken and (current_time - set_time) >= LASER_BREAK_BOUNCE_TIME:
            lasers_tripped += 1
            laser_times[i] = current_time

    penalties += lasers_tripped

    return beams_broken, penalties, laser_times
