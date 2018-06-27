import pytest

from laser_escape.laser_beam_detection import laser_beam_penalties, LASER_BREAK_BOUNCE_TIME


class MockLS:
    def __init__(self, value):
        self.value = value


TEST_NUM = 4

def test_beam_penalties_nothing_happening():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.85)]
    laser_times = [10, 10, 10]
    penalties = 0

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                11)

    assert penalties == 0
    assert laser_times == [10, 10, 10]
    assert beams_broken == [False, False, False]


def test_timers_reset_on_broken():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.15)]
    laser_times = [10, 10, 10]
    penalties = 0

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                17)

    assert penalties == 1
    assert laser_times == [10, 10, 17]
    assert beams_broken == [False, False, True]


def test_timers_decrease_after_set():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.15)]
    laser_times = [10, 10, 17]
    penalties = 1

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                18)

    assert penalties == 1
    assert laser_times == [10, 10, 17]
    assert beams_broken == [False, False, True]


def test_timers_decrease_after_set_2():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.15)]
    laser_times = [10, 10, 17]
    penalties = 1

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                19)

    assert penalties == 1
    assert laser_times == [10, 10, 17]
    assert beams_broken == [False, False, True]


def test_timers_decrease_after_set_3():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.15)]
    laser_times = [10, 10, 17]
    penalties = 1

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                20)

    assert penalties == 1
    assert laser_times == [10, 10, 17]
    assert beams_broken == [False, False, True]


def test_timers_decrease_after_set_4():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.85)]
    laser_times = [10, 10, 17]
    penalties = 1

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                21)

    assert penalties == 1
    assert laser_times == [10, 10, 17]
    assert beams_broken == [False, False, False]


def test_timers_decrease_after_set_5():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.85)]
    laser_times = [10, 10, 17]
    penalties = 1

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,
                                                                mock_light_sensors,
                                                                penalties,
                                                                26)

    assert penalties == 1
    assert laser_times == [10, 10, 17]
    assert beams_broken == [False, False, False]


def test_timers_sequence():
    mock_light_sensors = [MockLS(0.85), MockLS(0.85), MockLS(0.85)]
    laser_times = [0, 0, 0]
    penalties = 0
    mock_time = 10

    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times,mock_light_sensors,penalties,mock_time)

    assert penalties == 0
    assert laser_times == [0, 0, 0]
    assert beams_broken == [False, False, False]

    mock_light_sensors[0].value = 0
    mock_time = 10.5
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [True, False, False]

    mock_light_sensors[0].value = 0
    mock_time = 11
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [True, False, False]

    mock_light_sensors[0].value = 0
    mock_time = 11.5
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [True, False, False]

    mock_light_sensors[0].value = 0.9
    mock_time = 12
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [False, False, False]

    mock_light_sensors[0].value = 0.05
    mock_time = 12.5
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [True, False, False]

    mock_light_sensors[0].value = 0.8
    mock_time = 13
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [False, False, False]

    mock_light_sensors[0].value = 0.8
    mock_time = 17
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 1
    assert laser_times == [10.5, 0, 0]
    assert beams_broken == [False, False, False]

    mock_light_sensors[2].value = 0.1
    mock_time = 17.5
    beams_broken, penalties, laser_times = laser_beam_penalties(laser_times, mock_light_sensors,
                                                                penalties, mock_time)

    assert penalties == 2
    assert laser_times == [10.5, 0, 17.5]
    assert beams_broken == [False, False, True]