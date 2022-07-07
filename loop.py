from typing import List

import time
import math
import gpiozero
import numpy as np

controller = gpiozero.OutputDevice(18)
polling_interval = 1 # intervals between polling
projected_duration = 10 # predict for the next 10s
fan_start_temp = 70 # temperature to start fan
fan_state = 0
fan_state_resilient = 7
max_num_readings = 5

def poll_cpu_temperature() -> float:
    return gpiozero.CPUTemperature().temperature


def next_fan_state(state: int, control: int) -> int:
    next_state = state + control
    next_state = min(+fan_state_resilient, next_state)
    next_state = max(-fan_state_resilient, next_state)
    return next_state

def set_fan_off():
    controller.on()

def set_fan_on():
    controller.off()

def control_fan_state(state: int):
    if state > 0:
        print("set fan on")
        set_fan_on()
    else:
        print("set fan off")
        set_fan_off()

def project_max_temp(y: List[float], projected_duration: float) -> float:
    n = len(y)
    x = np.arange(n) - (n - 1)
    p = np.poly1d(np.polyfit(x=x, y=y, deg=1))
    m = math.ceil(projected_duration)
    x_pr = np.arange(m+1)
    y_pr = p(x_pr)
    return max(*y, *y_pr)    


if __name__ == "__main__":
    readings = []
    control_fan_state(fan_state)
    while True:
        temp = poll_cpu_temperature()
        print(f"current temp: {temp}")

        if len(readings) < max_num_readings:
            readings = readings + [temp,]
        else:
            readings = readings[-max_num_readings:] + [temp,]
        
        if len(readings) >= max_num_readings:
            projected_max_temp = project_max_temp(y=readings, projected_duration=projected_duration)
            print(f"projected max temp in the next {projected_duration} seconds: {projected_max_temp}")
            if projected_max_temp >= fan_start_temp:
                fan_state = next_fan_state(fan_state, +1)
            else:
                fan_state = next_fan_state(fan_state, -1)
            control_fan_state(fan_state)
        
        time.sleep(polling_interval)