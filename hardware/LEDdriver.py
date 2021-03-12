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
        pin = board.D10
        #print(pin)
        # pin = board.MOSI
        # # print(pin)
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(10,GPIO.OUT)
        # #GPIO.setup(20,GPIO.OUT)
        # GPIO.output(10,1)
        # time.sleep(0.5)
        # GPIO.output(10,0)
        # time.sleep(0.5)
        # GPIO.output(10,1)
        # time.sleep(0.5)
        # GPIO.output(10,0)

        #print(dir(board))
        self.n_pixels = 9
        # order to GRBW -- it's wrong! setting to GRBW makes it RGBW
        ORDER = neopixel.GRB
        self.pixels = neopixel.NeoPixel(pin, self.n_pixels, brightness = 0.5, auto_write=False, pixel_order = ORDER)

        # self.pixels.fill((255, 255, 255, 255))
        # self.pixels.show(

        self.flash_block=False

    # BATTERY STATUS
    def battery_status(self, vbat):

        # Flash block TODO: implement more cleanly
        if self.flash_block:
            return
        """
        A function to show battery status through LEDs.

        QUARTS:
            - top right
            - top left
        """

        magenta = (200,0,200)
        off = (0,0,0)
        # FULL
        if vbat >= 23250:
            self.pixels[0] = magenta
            self.pixels[1] = magenta
            self.pixels[2] = magenta

        # MIDDLE STATES
        if vbat < 23250 and vbat >= 22360:
            self.pixels[2] = magenta
            self.pixels[1] = magenta
            self.pixels[0] = off

        # BAT LO
        if vbat < 22360:
            self.pixels[2] = magenta
            self.pixels[1] = off
            self.pixels[0] = off

        #self.all_on()
        self.pixels.show()
        logging.debug("Set battery status")

    def battery_status_off(self):
        """
        Set status LEDs off.
        """
        # Flash block TODO: implement more cleanly
        if self.flash_block:
            return
        off = (0,0,0)
        self.pixels[2] = off
        self.pixels[1] = off
        self.pixels[0] = off

    # CODE STATUS
    def code_status(self, code_running):
        """
        A function to show battery status through LEDs.

        QUART:
            - bottom left

        9 = GREEN  | drainbot main
        10 = GREEN | logic
        11 = GREEN | chs
        12 = ----
        """

        # Flash block TODO: implement more cleanly
        if self.flash_block:
            return

        if code_running[0]:
            self.pixels[6] = (200,200,0)

        if code_running[1]:
            self.pixels[7] = (0,200,0)

        if code_running[2]:
            self.pixels[8] = (0,200,200)

    def map_state(self, robot_state):
        """
        Maps robot state to LED ring state
        """

        #print(robot_state)
        state = None
        if robot_state == "MOVING_FORWARD" or robot_state == "MOVING_BACKWARD":
            state = 'moving'


        if robot_state == "IDLE_IN_CHS" or robot_state == "IDLE_IN_PIPE" or robot_state == "IDLE_IN_MANHOLE" or robot_state == "IDLE_ON_PIPE_ENTRY":
            state = 'idle'

        if robot_state == "ALIGNING":
            state = 'aligning'

        if robot_state == "ALIGNED":
            state = 'idle'

        if robot_state == "ERROR" or robot_state == "STUCK":
            state = 'error'

        # print("LED RING STATE: {}".format(state))
        return state

    # ROBOT STATE
    def state_status(self, robot_state):
        """
        A function to indicate current state.

        QUART:
            - bottom right

        13 = 14 = 15

        LEGEND

        state                   | color     | CODE
        ----------------------------------------
        moving                  | GREEN     | (0, 255, 0, 0)
        idle in chs             | WHITE     | (0, 0, 0, 255)
        aligning                | BLUE      | (0, 0, 255, 0)
        charging                | OFF       | (0, 0, 0, 0)
        error                   | RED       | (255, 0, 0, 0)
        """

        # Flash block TODO: implement more cleanly
        if self.flash_block:
            return

        state = self.map_state(robot_state)  # maps robot state to led ring state
        code = (0,0,0)

        if state == 'moving':
            code = (0,200,0)

        if state == 'idle':
            code = (200,200,200)

        if state == 'aligning':
            code = (0,0,200)

        if state == 'charging':
            code = (0,0,0)

        if state == 'error':
            code = (200,0,0)

        self.pixels[3] = code
        self.pixels[4] = code
        self.pixels[5] = code

    def led_status_off(self):
        """
        Set status LEDs off.
        """

        # Flash block TODO: implement more cleanly
        if self.flash_block:
            return

        code = (0,0,0)
        self.pixels[3] = code
        self.pixels[4] = code
        self.pixels[5] = code

    def code_status_off(self):
        """
        Set status LEDs off.
        """

        # Flash block TODO: implement more cleanly
        if self.flash_block:
            return

        code = (0,0,0)
        self.pixels[6] = code
        self.pixels[7] = code
        self.pixels[8] = code

    # CAMERA FLASH
    def camera_flash(self,enable):
        """
        This function sets all leds to white. To be used when making a camera snapshot.
        """
        if enable:
            self.pixels.fill((255,255,255))
            self.led_pixels_show()
            self.flash_block = True
        else:
            self.flash_block = False
            self.pixels.fill((0,0,0))
            self.led_pixels_show()

    def all_off(self):
        """
        Turn all LEDs OFF.
        """
        logging.debug("Turning all LEDs off")

        # Flash block TODO: implement more cleanly
        #if self.flash_block:
        #    return

        code = (0,0,0)
        self.pixels.fill(code)
        self.pixels.show()


    def all_on(self):
        logging.debug("Turning all LEDs on")
        code = (255, 255, 255)
        self.pixels.fill(code)
        self.pixels.show()
        #self.led_pixels_show()

    def test_led_ring(self):
        code = ((0, 0, 255))
        for pixel_index in range(0, self.n_pixels):
        #for pixel in self.pixels:
            print("index: {}".format(pixel_index))

            print(self.pixels[pixel_index])
            print(self.pixels)
            self.pixels.show()
            time.sleep(1)
            self.all_off()
            time.sleep(1)
            self.all_on()
            time.sleep(1)
            self.all_off()


    def cycle(self):
        code = ((109, 0, 0))
        for pixel in range(0, self.n_pixels):
            self.pixels[pixel] = code
            self.pixels.show()
            #self.pixels.show()
            time.sleep(0.1)
            self.pixels[pixel] = ((0, 0, 0))
            self.pixels.show()
            #self.pixels.show()
            time.sleep(0.1)

    def set_color(self):
        code = (90, 0, 0)  # NOTE CHANGING COLOR FROM 109 TO 110 CHANGES LED COLOR FROM RED TO BLUEish
        self.pixels.fill(code)
        self.pixels.show()
        time.sleep(2)
        self.pixels.deinit()

    def led_pixels_show(self):
        # give absolute priority to flash
        self.pixels.show()

# leddriver = LEDDriver()
# #leddriver.all_on()
# leddriver.all_off()

# leddriver = LEDDriver()
# leddriver.test_led_ring()