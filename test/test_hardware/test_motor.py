import time
import struct
import serial

from threading import Lock

from ...src.data_manager import DataManager
from ...src.motor_control import MotorControl

"""
Run tests with `sudo python3 -m koruza_v2.koruza_v2_driver.test.test_hardware.test_motor`
"""

lock = Lock()
data_manager = DataManager()
ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
motor_driver = MotorControl(ser, lock, data_manager)

print("=== STARTING MOTOR TEST ===")
print("Observe the rotational axis of the motors when performing this test and follow instructions presented below.")
print(f"Homing motors to 0, 0")
motor_driver.home()
input("Press Enter when motors stop moving")

print("Moving x axis for 720°")
motor_driver.move_motor(8192, 0, 0)
input("Press Enter when motor rotates for 360°")

print("Moving x axis for -360°")
motor_driver.move_motor(-4096, 0, 0)
input("Press Enter when motor rotates for -360°")

print("Moving y axis for 720°")
motor_driver.move_motor(0, 8192, 0)
input("Press Enter when motor rotates for 360°")

print("Moving y axis for -360°")
motor_driver.move_motor(0, -4096, 0)
input("Press Enter when motor rotates for -360°")

print(f"Homing motors to 0, 0")
motor_driver.home()
input("Press Enter when motors stop moving")