from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex

class i2c:

    GET_VER = 0x01

    WRITE_TO_S_BUFF = 0x10
    READ_FROM_S_BUFF = 0x11

    I2C_INIT = 0x40
    I2C_EXIT = 0x41
    I2C_WRITE = 0x42
    I2C_READ = 0x43
    I2C_WRITE_N = 0x44
    I2C_READ_N = 0x45

    ver = "I2C v220718"

    usb = nhcusb.nhcusb()

    def open(self):
        return self.usb.open(0x0416, 0x0002)

    def close(self):
        self.usb.close()
    
    def get_ver(self):
        ver = ""
        tmp = bytearray(64)
        tmp[0] = self.GET_VER
        tmp[1] = 0x02
        if self.usb.write(tmp):
            (res, tmp) = self.usb.read()
            if res:
                for i in range(64):
                    if tmp[i] == 0x00:
                        break
                    ver += chr(tmp[i])
                return ver
            else:
                return ver
        return ver

    def write_to_buff(self, data, pos):
        tmp = bytearray(64)
        tmp[0] = self.WRITE_TO_S_BUFF
        n = len(data)
        tmp[1] = n // 64
        tmp[2] = pos // 64
        if self.usb.write(tmp) == 0:
            return 0
        return self.usb.write(data, n)

    def read_from_buff(self, pos, length):
        tmp = bytearray(64)
        tmp[0] = self.READ_FROM_S_BUFF
        tmp[1] = length // 64
        tmp[2] = pos // 64
        if self.usb.write(tmp) == 0:
            return (0, tmp)
        return self.usb.read(length)

    def i2c_init(self, clock = 100000):
        tmp = bytearray(64)
        tmp[0] = self.I2C_INIT
        tmp[1:5] = struct.pack('<L', clock)
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res

    def i2c_exit(self):
        tmp = bytearray(64)
        tmp[0] = self.I2C_EXIT
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res

    def i2c_write(self, address, data):
        tmp = bytearray(64)
        tmp[0] = self.I2C_WRITE
        n = len(data)
        tmp[1] = address
        tmp[2] = n
        for i in range(n):
            tmp[i + 3] = data[i]
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]

    def i2c_read(self, address, length):
        tmp = bytearray(64)
        tmp[0] = self.I2C_READ
        tmp[1] = address
        tmp[2] = length

        if self.usb.write(tmp) == 0:
            return (0, tmp)
        (res, tmp) = self.usb.read()
        if res == 0:
            return (0, tmp)
        if tmp[0] == 0:
            return (0, tmp)
        return (1, tmp[1 : length + 1])

    def i2c_write_n(self, address, data):
        n = len(data)
        tmp = bytearray(n + 63)
        for i in range(n):
            tmp[i] = data[i]

        if self.write_to_buff(tmp, 0) == 0:
            return 0

        n = len(data)
        tmp = bytearray(64)
        tmp[0] = self.I2C_WRITE_N
        tmp[1] = address
        tmp[2 : 6] = struct.pack('<L', n)

        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]

    def i2c_read_n(self, address, length):
        tmp = bytearray(64)
        tmp[0] = self.I2C_READ_N
        tmp[1] = address
        tmp[2 : 6] = struct.pack('<L', length)
        if self.usb.write(tmp) == 0:
            return (0, tmp)
        (res, tmp) = self.usb.read()
        if res == 0:
            return (0, tmp)
        if tmp[0] == 0:
            return (0, tmp)
        return self.read_from_buff(0, length)

