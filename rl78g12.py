from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import argparse
from intelhex import IntelHex

class rl78g12:
    flash_size = 16 * 1024
    flash_page_size = 1024

    GET_VER = 0x01

    INIT = 0x36
    EXIT = 0x31
    BLOCK_ERASE = 0x37
    WRITE_BUFF = 0x38
    WRITE_AND_VERIFY = 0x39

    ver = "RL78G10 v220708"

    usb = nhcusb.nhcusb()

    def open_prog(self):
        return self.usb.open(0x0416, 0x0002)

    def close_prog(self):
        self.usb.close()
    
    def get_ver(self):
        ver = ""
        tmp = bytearray(64)
        tmp[0] = self.GET_VER
        tmp[1] = 0x01

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

    def init(self):
        tmp = bytearray(64)
        tmp[0] = self.INIT
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]

    def exit(self):
        tmp = bytearray(64)
        tmp[0] = self.EXIT
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        return res
    
    def erase(self, address):
        tmp = bytearray(64)
        tmp[0] = self.BLOCK_ERASE
        tmp[1] = address & 0xff
        tmp[2] = (address >> 8) & 0xff
        tmp[3] = (address >> 16) & 0xff
        
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]
    
    def write_buff(self, data, pos, length):
        tmp = bytearray(64)
        tmp[0] = self.WRITE_BUFF
        tmp[1] = pos & 0xff
        tmp[2] = (pos >> 8) & 0xff
        tmp[3] = length
        for i in range(length):
            tmp[4 + i] = data[i]
        return self.usb.write(tmp)
    
    def write_and_verify(self, address):
        tmp = bytearray(64)
        tmp[0] = self.WRITE_AND_VERIFY
        tmp[1] = address & 0xff
        tmp[2] = (address >> 8) & 0xff
        tmp[3] = (address >> 16) & 0xff
        tmp[4] = (address >> 24) & 0xff
        
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]

    def need_write(self, data):
        n = len(data)
        for i in range(n):
            if data[i] != 0xff:
                return 1
        return 0
    
    def process(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--write_flash", help="Flash file: input.hex, input.bin")
        args = parser.parse_args()

        print("=======================================================================================")
        print("openprog by Ngo Hung Cuong")
        print("=======================================================================================")

        if self.open_prog() == 0:
            raise("Open Prog: FAIL")

        if self.ver != self.get_ver():
            self.close_prog()
            raise("Firmware: FAIL")
        
        if args.write_flash != None:
            print("Write flash:")
            ih = IntelHex()
            
            ih.fromfile(args.write_flash, format='bin')

            writebuff = ih.tobinarray(0, self.flash_size - 1)
            page_size = self.flash_page_size
            
            if self.init() == 0:
                self.exit()
                self.close_prog()
                raise("Check MCU: FAIL")
            
            numpage = self.flash_size // self.flash_page_size

            #erase
            print("Erase:")
            for i in range(numpage):
                if self.need_write(writebuff[i * self.flash_page_size : (i + 1) * self.flash_page_size]) == 1:
                    if self.erase(i * self.flash_page_size) == 0:
                        self.exit()
                        self.close_prog()
                        raise("Erase: FAIL")
                    print(".", end='', sep='', flush=True)
            print("\n")
            
            #write
            print("Write")
            for i in range(numpage):
                if self.need_write(writebuff[i * self.flash_page_size : (i + 1) * self.flash_page_size]) == 1:
                    num = self.flash_page_size // 32
                    for j in range(num):
                        if self.write_buff(writebuff[i * self.flash_page_size + j * 32 : i * self.flash_page_size + (j + 1) * 32], j * 32, 32) == 0:
                            self.exit()
                            self.close_prog()
                            raise("Write: FAIL")
                    
                    if self.write_and_verify(i * self.flash_page_size) == 0:
                        self.exit()
                        self.close_prog()
                        raise("Write: FAIL")
                    
                    print(".", end='', sep='', flush=True)
            print("\n")
            
            self.exit()
            self.close_prog()
            print("Done")
            
'''
rl78 = rl78g12()
rl78.process()
'''
