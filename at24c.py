from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex
import i2c

class at24c(i2c.i2c):

    eeprom_size = 32 * 1024 // 8
    eeprom_page_size = 32
    address_size = 2

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
                
                if self.address_size == 1:
                    tmp[0 : self.address_size] = struct.pack('>B', page_size * i % 256)
                else:
                    tmp[0 : self.address_size] = struct.pack('>H', page_size * i % 65536)
                
                for j in range(page_size):
                    tmp[self.address_size + j] = writebuff[i * page_size + j]

                if len(tmp) < 64:
                    if self.address_size == 1:
                        if self.i2c_write(0xa0 + ((page_size * i) // 256 * 2), tmp) == 0:
                            self.i2c_exit()
                            self.close()
                            raise("Write: FAIL")
                    else:
                        if self.i2c_write(0xa0 + ((page_size * i) // 65536 * 2), tmp) == 0:
                            self.i2c_exit()
                            self.close()
                            raise("Write: FAIL")
                else:
                    if self.address_size == 1:
                        if self.i2c_write_n(0xa0 + ((page_size * i) // 256 * 2), tmp) == 0:
                            self.i2c_exit()
                            self.close()
                            raise("Write: FAIL")
                    else:
                        if self.i2c_write_n(0xa0 + ((page_size * i) // 65536 * 2), tmp) == 0:
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
                if self.address_size == 1:
                    tmp[0 : self.address_size] = struct.pack('>B', page_size * i % 256)
                else:
                    tmp[0 : self.address_size] = struct.pack('>H', page_size * i % 65536)

                if self.address_size == 1:
                    if self.i2c_write(0xa0 + ((page_size * i) // 256 * 2), tmp) == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                else:
                    if self.i2c_write(0xa0 + ((page_size * i) // 65536 * 2), tmp) == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                if self.eeprom_page_size < 64:
                    if self.address_size == 1:
                        (res, tmp) = self.i2c_read(0xa1 + ((page_size * i) // 256 * 2), page_size)
                    else:
                        (res, tmp) = self.i2c_read(0xa1 + ((page_size * i) // 65536 * 2), page_size)
                    if res == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                else:
                    if self.address_size == 1:
                        (res, tmp) = self.i2c_read_n(0xa1 + ((page_size * i) // 256 * 2), page_size)
                    else:
                        (res, tmp) = self.i2c_read_n(0xa1 + ((page_size * i) // 65536 * 2), page_size)
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
                if self.address_size == 1:
                    tmp[0 : self.address_size] = struct.pack('>B', page_size * i % 256)
                else:
                    tmp[0 : self.address_size] = struct.pack('>H', page_size * i % 65536)

                if self.address_size == 1:
                    if self.i2c_write(0xa0 + ((page_size * i) // 256 * 2), tmp) == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                else:
                    if self.i2c_write(0xa0 + ((page_size * i) // 65536 * 2), tmp) == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                if self.eeprom_page_size < 64:
                    if self.address_size == 1:
                        (res, tmp) = self.i2c_read(0xa1 + ((page_size * i) // 256 * 2), page_size)
                    else:
                        (res, tmp) = self.i2c_read(0xa1 + ((page_size * i) // 65536 * 2), page_size)
                    if res == 0:
                        self.i2c_exit()
                        self.close()
                        raise("Read: FAIL")
                else:
                    if self.address_size == 1:
                        (res, tmp) = self.i2c_read_n(0xa1 + ((page_size * i) // 256 * 2), page_size)
                    else:
                        (res, tmp) = self.i2c_read_n(0xa1 + ((page_size * i) // 65536 * 2), page_size)
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
