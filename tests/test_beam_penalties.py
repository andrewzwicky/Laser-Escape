import pytest

from laser_escape.laser_beam_detection import laser_beam_penalties


class MockLightSensor:
    def __init__(self, value):
        self.value = value


TEST_NUM = 4


def test_beam_penalties():
    mock_light_sensors = [MockLightSensor(0.85) for _ in range(TEST_NUM)]
    laser_times = [0 for _ in range(TEST_NUM)]
    penalties = 0

    beams_broken, penalties = laser_beam_penalties(laser_times, mock_light_sensors, penalties)

    assert penalties == 0
    assert not beams_broken
