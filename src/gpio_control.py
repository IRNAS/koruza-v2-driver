import time
import RPi.GPIO as GPIO

TX_1_DISABLE = 9  # GPIO9
TX_2_DISABLE = 8  # GPIO8

RESET = 18

class GpioControl():
    def __init__(self):
        """Init class and configure pin mode"""
        GPIO.setmode(GPIO.BCM)  # set BCM mode

    def koruza_reset(self):
        """Hardware resets MCU (motor driver)"""
        GPIO.setup(RESET, GPIO.OUT)  # set pin as output

        GPIO.output(RESET, GPIO.LOW)  # TX_1 pin low
        time.sleep(0.3)
        GPIO.output(RESET, GPIO.HIGH)  # TX_1 pin low

    def sfp_config(self):
        """Configure sfp tx disable pins"""
        GPIO.setup(TX_1_DISABLE, GPIO.OUT)  # set pin as output
        GPIO.setup(TX_2_DISABLE, GPIO.OUT)  # set pin as output
        
        GPIO.output(TX_1_DISABLE, GPIO.LOW)  # TX_1 pin low
        GPIO.output(TX_2_DISABLE, GPIO.LOW)  # TX_1 pin low