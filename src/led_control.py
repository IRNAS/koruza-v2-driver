import time
import board
import logging
import neopixel
import RPi.GPIO as GPIO

from ...src.colors import Color

# to install:
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
# sudo python3 -m pip install --force-reinstall adafruit-blinka

log = logging.getLogger()

class LedControl():
    def __init__(self, config_manager):
        """
        Class constructor.
        """
        self.config_manager = config_manager

        self.pixels = None

        # init this
        try:
            self.init()
        except Exception as e:
            log.error(e)

        self.current_color = Color.NO_SIGNAL
        self.prev_color = Color.NO_SIGNAL
        self.state = None
        # toggle led according to config file
        if self.config_manager.config["camera"]["led"]:
            self.set_color(Color.NO_SIGNAL)  # default is red LED
            self.turn_on()
        else:
            self.turn_off()

    
    def __del__(self):
        """
        """
        self.mode = 0
        self.pixels[0] = (0,0,0)
        self.pixels.show()
        self.pixels = None

    def init(self):
        """Init LedControl"""
        pin = board.D12  # rgb led is on GPIO 12  TODO get from constants
        # order to GRBW -- it's wrong! setting to GRBW makes it RGBW
        ORDER = neopixel.GRB
        self.pixels = neopixel.NeoPixel(pin, 1, brightness = 1, auto_write=True)

    def toggle_led(self):
        """Toggle led"""
        if self.state == "OFF":
            self.set_color(self.prev_color)
            self.turn_on()
        elif self.state == "ON":
            self.turn_off()

    def turn_off(self):
        """Turn LED off"""
        self.state = "OFF"
        self.pixels[0] = (0,0,0)
        self.pixels.show()
        self.config_manager.update_camera_config([("led", False)])

    def turn_on(self):
        """

        """
        self.state = "ON"
        color_split = self.current_color[1:]
        r = int(color_split[0:2], 16)
        g = int(color_split[2:4], 16)
        b = int(color_split[4:6], 16)

        code = (r, g, b)
        self.pixels[0] = code
        self.pixels.show()

        self.config_manager.update_camera_config([("led", True)])

    def set_color(self, color):
        """
        Set led to selected color
        """

        self.prev_color = self.current_color
        self.current_color = color