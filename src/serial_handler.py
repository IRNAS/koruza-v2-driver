#!/usr/bin/env python3
import serial
import time

class SerialHandler:

    def __init__(self, serial_port, baudrate, timeout=2):
        self.ser = serial.Serial(serial_port, baudrate, timeout=timeout)

    def __del__(self):
        try:
            if self.ser:
                self.ser.close()
                self.ser = None
        except Exception as e:
            raise e

    def read(self):
        #print(f"Receiving on {self.ser}")
        received = self.ser.readline()
        # print("RS: ", received)
        return received.decode("utf-8").strip()

    def write(self, data):
        data += "\n"
        #print(f"Writing on {self.ser}")
        # print("WS: ", data)
        self.ser.write(data.encode())

    def read_until(self, s):
        to = 0
        while True:
            rx = self.read()
            if rx == s:
                return
            if rx == "":
                to += 1
                if to > 10:
                    raise Exception("Serial timed out")

    def read_until_starts_with(self, s, timeout=10):
        to = 0
        start_time = time.time()
        while True:
            rx = self.read()
            #print(rx)
            # print(s)
            if len(rx) >= len(s) and rx[0:len(s)] == s:
                return rx
            if rx == "":
                to += 1
                if to > 10:
                    raise Exception("Serial timed out")
            if time.time() - start_time > timeout:
                raise Exception("Serial timed out")

    def read_until_contains(self, s, timeout=10):
        to = 0
        start_time = time.time()
        while True:
            rx = self.read()
            #print(rx)
            # print(s)
            if len(rx) >= len(s) and s in rx:
                return rx
            if rx == "":
                to += 1
                if to > 10:
                    raise Exception("Serial timed out")
            if time.time() - start_time > timeout:
                raise Exception("Serial timed out")

    def read_until_starts_with_either(self, a, b, timeout=10):
        to = 0
        start_time = time.time()
        while True:
            rx = self.read()
            #print(f"Read: {rx}")
            if len(rx) >= len(a) and rx[0:len(a)] == a or len(rx) >= len(b) and rx[0:len(b)] == b:
                return rx
            if rx == "":
                to += 1
                if to > 10:
                    raise Exception("Serial timed out. Did you flash code with debug enabled?")
            if time.time() - start_time > timeout:
                raise Exception("Serial timed out")

    def read_until_starts_with_one_of(self, vars, timeout=10):
        to = 0
        start_time = time.time()
        while True:
            rx = self.read()
            #print(f"Read: {rx}")
            for var in vars:
                if len(rx) >= len(var) and rx[0:len(var)] == var:
                    return rx
            if rx == "":
                to += 1
                if to > 10:
                    raise Exception("Serial timed out. Did you flash code with debug enabled?")
            if time.time() - start_time > timeout:
                raise Exception("Serial timed out")