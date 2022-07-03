from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct

class spi:

    GET_VER = 0x01

    WRITE_TO_S_BUFF = 0x10
    READ_FROM_S_BUFF = 0x11

    SPI_INIT = 0x20
    SPI_EXIT = 0x21
    SPI_WRITE = 0x22
    SPI_READ = 0x23
    SPI_EXCH = 0x24
    SPI_WRITE_N = 0x25
    SPI_READ_N = 0x26
    SPI_EXCH_N = 0x27

    AT89S5X_WRITE = 0x28
    AT89S5X_READ = 0x29

    usb = nhcusb.nhcusb()

    def open(self):
        return self.usb.open(0x0416, 0x0002)

    def close(self):
        self.usb.close()
    
    def get_ver(self):
        ver = ""
        tmp = bytearray(64)
        tmp[0] = self.GET_VER
        tmp[1] = 0x00

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

    def spi_init(self, clock = 1000000, reset = 0):
        tmp = bytearray(64)
        tmp[0] = self.SPI_INIT
        tmp[1:5] = struct.pack('<L', clock)
        tmp[5] = reset
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res

    def spi_exit(self, reset = 0):
        tmp = bytearray(64)
        tmp[0] = self.SPI_EXIT
        tmp[1] = reset
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res

    def spi_write(self, data):
        tmp = bytearray(64)
        tmp[0] = self.SPI_WRITE
        n = len(data)
        tmp[1] = n
        for i in range(n):
            tmp[i + 2] = data[i]

        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res

    def spi_read(self, length, seed = 0x00):
        tmp = bytearray(64)
        tmp[0] = self.SPI_READ
        tmp[1] = length
        tmp[2] = seed

        if self.usb.write(tmp) == 0:
            return (0, tmp)
        return self.usb.read()

    def spi_exch(self, data):
        tmp = bytearray(64)
        tmp[0] = self.SPI_EXCH
        n = len(data)
        tmp[1] = n
        for i in range(n):
            tmp[2 + i] = data[i]
        if self.usb.write(tmp) == 0:
            return (0, tmp)
        return self.usb.read()

    def spi_write_n(self, data):
        if self.write_to_buff(data, 0) == 0:
            return 0

        n = len(data)
        tmp = bytearray(64)
        tmp[0] = self.SPI_WRITE_N
        tmp[1] = 0
        tmp[2] = n // 64

        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res

    def spi_read_n(self, length, seed = 0x00):
        tmp = bytearray(64)
        tmp[0] = self.SPI_READ_N
        tmp[1] = 0
        tmp[2] = length // 64
        tmp[3] = seed
        if self.usb.write(tmp) == 0:
            return (0, tmp)
        
        return self.read_from_buff(0, length)

    def spi_exch_n(self, dataTx):
        # first: write data to tx buffer
        if self.write_to_buff(dataTx, 0) == 0:
            return (0, tmp)
        #send cmd write spi_n
        tmp = bytearray(64)
        tmp[0] = self.SPI_EXCH_N
        tmp[1] = 32 # buffer is 64 * 64, rxBuff = 32 * 64
        tmp[2] = 0 # buffer is 64 * 64, txBuff = 32 * 64
        n = len(dataTx)
        tmp[3] = n // 64
        if self.usb.write(tmp) == 0:
            return (0, tmp)
        (res, tmp) = self.usb.read()
        if res == 0:
            return (0, tmp)
        
        return self.read_from_buff(32 * 64, n)

    def at89s5x_write(self, data, address):
        if self.write_to_buff(data, 0) == 0:
            return 0
        tmp = bytearray(64)
        tmp[0] = self.AT89S5X_WRITE
        tmp[1:5] = struct.pack('<L', address)
        tmp[5:9] = struct.pack('<L', len(data))
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]
    
    def at89s5x_read(self, address, length):        
        tmp = bytearray(64)
        tmp[0] = self.AT89S5X_READ
        tmp[1:5] = struct.pack('<L', address)
        tmp[5:9] = struct.pack('<L', length)
        if self.usb.write(tmp) == 0:
            return (0, tmp)
        (res, tmp) = self.usb.read()
        if res == 0:
            return (0, tmp)
        return self.read_from_buff(0, length)
