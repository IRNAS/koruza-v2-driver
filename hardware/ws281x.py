import board
import neopixel
import time
import RPi.GPIO as GPIO
import logging

# to install:
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
# sudo python3 -m pip install --force-reinstall adafruit-blinka

class LEDDriver(object):
    def __init__(self):
        """
        Class constructor.
        """
        pin = board.D18
        self.n_pixels = 1
        # order to GRBW -- it's wrong! setting to GRBW makes it RGBW
        ORDER = neopixel.GRB
        self.pixels = neopixel.NeoPixel(pin, self.n_pixels, brightness = 1, auto_write=True)

    
    def __del__(self):
        """
        """
        self.pixels[0] = (0,0,0)
        self.pixels.show()
        self.pixels = None

    def set_color(self, color, mode):
        """
        Mode:
            0: shine
            105: blink 0.5s
        """
        if color == "blue":
            code = (0,0,255)
        
        self.pixels[0] = code
        
        if mode == 0:
            self.pixels.show()
        
        else:
            while mode == 105:
                self.pixels.show()
                time.sleep(0.5)
                self.pixels[0] = (0,0,0)
                self.pixels.show()
                time.sleep(0.5)
                self.pixels[0] = code

    def LED_link_quality(self, rx):
        """
        Color scale of RX power. 
        """
        pass

    def config_mode(self):
        """
        Blink blue in config mode.
        """
        self.pixels[0] = (0,0,255)
        self.pixels.show()
        pass

if __name__ == "__main__":
    led = LEDDriver()
    led.set_color("blue",105)