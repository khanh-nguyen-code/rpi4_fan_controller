from typing import List

import time
import math
import gpiozero
import numpy as np

controller = gpiozero.OutputDevice(18)
polling_interval = 1  # intervals between polling
projecting_duration = 10  # predict for the next 10s
threshold_temp = 70  # temperature to start fan
fan_state = 0
fan_state_resilient = 4
max_num_readings = 5


def poll_cpu_temperature() -> float:
    return gpiozero.CPUTemperature().temperature


def control_fan_state(state: int, control: int) -> int:
    next_state = state + control
    next_state = min(+fan_state_resilient, next_state)
    next_state = max(-fan_state_resilient, next_state)
    if next_state > 0:
        print("fan on")
        controller.off()  # pnp transistor
    else:
        print("fan off")
        controller.on()  # pnp transistor
    return next_state


def project(y: List[float], projecting_duration: float) -> List[float]:
    n = len(y)
    x = np.arange(n) - (n - 1)
    p = np.poly1d(np.polyfit(x=x, y=y, deg=1))
    x_pr = np.array([0, projecting_duration])
    y_pr = p(x_pr)
    # TODO : allow project to return empty list if the confidence level is small
    return [*y_pr]


if __name__ == "__main__":
    temp_list = []
    fan_state = control_fan_state(fan_state, 0)
    while True:
        temp = poll_cpu_temperature()

        if len(temp_list) < max_num_readings:
            temp_list = temp_list + [temp, ]
        else:
            temp_list = temp_list[-max_num_readings:] + [temp, ]

        if len(temp_list) >= max_num_readings:
            projected_temp_list = project(y=temp_list, projecting_duration=projecting_duration)
            print(f"temp: {temp_list}: projection {projected_temp_list}")
            projected_max_temp = max(*temp_list, *projected_temp_list)

            control = 1 if projected_max_temp >= threshold_temp else -1
            fan_state = control_fan_state(fan_state, control)

        time.sleep(polling_interval)
