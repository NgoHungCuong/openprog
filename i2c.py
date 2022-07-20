from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex

class i2c:

    eeprom_size = 32 * 1024 // 8
    eeprom_page_size = 32
    address_size = 2

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

    def process(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--clock", help="Clock in Hz, ex: 100000", type=int)
        parser.add_argument("--write", help="EEPROM file: input.bin")
        parser.add_argument("--read", help = "EEPROM file: output.bin")
        parser.add_argument("--verify", help = "EEPROM file: input.bin")
        args = parser.parse_args()

        print("=======================================================================================")
        print("openprog by Ngo Hung Cuong")
        print("=======================================================================================")

        if self.open() == 0:
            raise("Open Prog: FAIL")

        if self.ver != self.get_ver():
            self.close()
            raise("Firmware: FAIL")
        
        if (args.clock != None) and (args.clock != 0):
            if self.i2c_init(args.clock) == 0:
                raise("Init I2C: FAIL")    
        else:
            if self.i2c_init() == 0:
                raise("Init I2C: FAIL")
        
        if args.write != None:
            print("Write:")
            ih = IntelHex()
            
            ih.fromfile(args.write, format='bin')

            writebuff = ih.tobinarray(0, self.eeprom_size - 1)
            page_size = self.eeprom_page_size
            
            numpage = self.eeprom_size // page_size

            for i in range(numpage):
                tmp = bytearray(self.address_size + page_size)
                tmp[0 : self.address_size] = struct.pack('>H', page_size * i)
                for j in range(page_size):
                    tmp[2 + j] = writebuff[i * page_size + j]
                if len(tmp) < 64:
                    if self.i2c_write(0xa0, tmp) == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Write: FAIL")
                else:
                    if self.i2c_write_n(0xa0, tmp) == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Write: FAIL")
                #polling
                for j in range(1000):
                    (res, tmp) = self.i2c_read(0xa1, 1)
                    if res == 1:
                        break
                    time.sleep(0.001)
                if j == 1000:
                    self.i2c_exit()
                    self.close()
                    raise("Write: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")

        #read
        if args.read != None:
            print("Read:")
            ih = IntelHex()
            page_size = self.eeprom_page_size
            for i in range(self.eeprom_size // page_size):
                tmp = bytearray(self.address_size)
                tmp[0 : self.address_size] = struct.pack('>H', page_size * i)
                if self.i2c_write(0xa0, tmp) == 0:
                    self.i2c_exit()
                    self.close()
                    raise("Read: FAIL")
                if self.eeprom_page_size < 64:
                    (res, tmp) = self.i2c_read(0xa1, page_size)
                    if res == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                else:
                    (res, tmp) = self.i2c_read_n(0xa1, page_size)
                    if res == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                ih.frombytes(tmp, i * page_size)
                print(".", end='', sep='', flush=True)
                ih.tobinfile(args.read)
            print("\n")

        #verify
        if args.verify != None:
            ih = IntelHex()
            ih.fromfile(args.verify, format='bin')
            writebuff = ih.tobinarray(0, self.eeprom_size - 1)
            print("Verify:")
            page_size = self.eeprom_page_size
            for i in range(self.eeprom_size // page_size):

                tmp = bytearray(self.address_size)
                tmp[0 : self.address_size] = struct.pack('>H', page_size * i)
                if self.i2c_write(0xa0, tmp) == 0:
                    self.i2c_exit()
                    self.close()
                    raise("Read: FAIL")
                if self.eeprom_page_size < 64:
                    (res, tmp) = self.i2c_read(0xa1, page_size)
                    if res == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                else:
                    (res, tmp) = self.i2c_read_n(0xa1, page_size)
                    if res == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                for j in range(page_size):
                    if tmp[j] != writebuff[i * page_size + j]:
                        self.exit_prog()
                        self.close_prog()
                        raise("Verify: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")

        self.i2c_exit()
        self.close()
        print("Done")

'''
nhci2c = i2c()
if nhci2c.open() == 0:
    raise("Open fail")
if nhci2c.i2c_init(400000) == 0:
    raise("Init fail")

tmp = bytearray(34)
tmp[0] = 0x00
tmp[1] = 0x00
for i in range(32):
    tmp[2 + i] = i

if nhci2c.i2c_write_n(0xa0, tmp) == 0:
    nhci2c.i2c_exit()
    nhci2c.close()
    raise("Write FAIL")

#polling
for i in range(100):
    tmp = bytearray(2)
    tmp[0] = 0x00
    tmp[1] = 0x00
    if nhci2c.i2c_write(0xa0, tmp) == 1:
        break
    time.sleep(0.001)

if i == 100:
    nhci2c.i2c_exit()
    nhci2c.close()
    raise("Polling FAIL")

(res, tmp) = nhci2c.i2c_read_n(0xa1, 1024)
if res == 0:
    nhci2c.i2c_exit()
    nhci2c.close()
    raise("read fail")
print(hex(tmp[0]))
print(hex(tmp[1]))
print(hex(tmp[2]))
print(hex(tmp[3]))
nhci2c.i2c_exit()
nhci2c.close()
print("Done")
'''
'''
nhci2c = i2c()
nhci2c.process()
'''
