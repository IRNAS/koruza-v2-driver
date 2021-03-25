import time
import board
import logging
import neopixel
import RPi.GPIO as GPIO

# to install:
# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
# sudo python3 -m pip install --force-reinstall adafruit-blinka

class LedDriver():
    def __init__(self):
        """
        Class constructor.
        """
        pin = board.D12  # rgb led is on GPIO 12
        self.n_pixels = 1
        # order to GRBW -- it's wrong! setting to GRBW makes it RGBW
        ORDER = neopixel.GRB
        self.pixels = neopixel.NeoPixel(pin, self.n_pixels, brightness = 1, auto_write=True)

    
    def __del__(self):
        """
        """
        self.mode = 0
        self.pixels[0] = (0,0,0)
        self.pixels.show()
        # time.sleep(2)
        self.pixels = None
        # print("DELETING LED DRIVER")
        # time.sleep(1)

    def turn_off(self):
        """Turn LED off"""
        self.mode = 0
        self.pixels[0] = (0,0,0)
        self.pixels.show()
        # time.sleep(2)
        # self.pixels = None
        # time.sleep(1)

    def set_color(self, color, mode):
        """
        Mode:
            0: shine
            105: blink 0.5s
        """
        self.mode = mode

        color_split = color[1:]
        r = int(color_split[0:2], 16)
        g = int(color_split[2:4], 16)
        b = int(color_split[4:6], 16)

        # print(f"R:  {r} G: {g} B: {b}")

        # b = 0
        code = (r, g, b)

        # if color == "blue":
        #     code = (0,0,255)
        
        self.pixels[0] = code
        
        if self.mode == 0:
            self.pixels.show()
        
        else:
            while self.mode == 105:
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

# if __name__ == "__main__":
#     led = LedDriver()
#     led.set_color("blue",105)