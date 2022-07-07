from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import argparse
from intelhex import IntelHex

class rl78g10:
    flash_size = 8 * 1024
    flash_page_size = 32

    GET_VER = 0x01

    INIT = 0x30
    EXIT = 0x31
    ERASE_WRITE_FIRST = 0x32
    ERASE_WRITE = 0x33
    ERASE_WRITE_LAST = 0x34
    READ_CRC16 = 0x35
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
    
    def erase_write_fisrt(self, data):
        tmp = bytearray(64)
        tmp[0] = self.ERASE_WRITE_FIRST
        tmp[1] = self.get_flash_size_code()
        tmp[2] = len(data)
        n = len(data)
        for i in range(n):
            tmp[3 + i] = data[i]
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]
    
    def erase_write(self, data):
        tmp = bytearray(64)
        tmp[0] = self.ERASE_WRITE
        tmp[1] = len(data)
        n = len(data)
        for i in range(n):
            tmp[2 + i] = data[i]
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]
    
    def erase_write_last(self, data):
        tmp = bytearray(64)
        tmp[0] = self.ERASE_WRITE_LAST
        tmp[1] = len(data)
        n = len(data)
        for i in range(n):
            tmp[2 + i] = data[i]
        if self.usb.write(tmp) == 0:
            return 0
        (res, tmp) = self.usb.read()
        if res == 0:
            return 0
        return tmp[0]
    
    def read_crc16(self):
        tmp = bytearray(64)
        tmp[0] = self.READ_CRC16
        tmp[1] = self.get_flash_size_code()
        if self.usb.write(tmp) == 0:
            return (0, 0)
        (res, tmp) = self.usb.read()
        if res == 0:
            return (0, 0)
        if tmp[0] == 0:
            return (0, 0)
        return (1, tmp[2] * 256 + tmp[1])
    
    def crc16(self, dataIn: bytes):
        table = [
            0x0000,0x1021,0x2042,0x3063,0x4084,0x50A5,0x60C6,0x70E7,
            0x8108,0x9129,0xA14A,0xB16B,0xC18C,0xD1AD,0xE1CE,0xF1EF,
            0x1231,0x0210,0x3273,0x2252,0x52B5,0x4294,0x72F7,0x62D6,
            0x9339,0x8318,0xB37B,0xA35A,0xD3BD,0xC39C,0xF3FF,0xE3DE,
            0x2462,0x3443,0x0420,0x1401,0x64E6,0x74C7,0x44A4,0x5485,
            0xA56A,0xB54B,0x8528,0x9509,0xE5EE,0xF5CF,0xC5AC,0xD58D,
            0x3653,0x2672,0x1611,0x0630,0x76D7,0x66F6,0x5695,0x46B4,
            0xB75B,0xA77A,0x9719,0x8738,0xF7DF,0xE7FE,0xD79D,0xC7BC,
            0x48C4,0x58E5,0x6886,0x78A7,0x0840,0x1861,0x2802,0x3823,
            0xC9CC,0xD9ED,0xE98E,0xF9AF,0x8948,0x9969,0xA90A,0xB92B,
            0x5AF5,0x4AD4,0x7AB7,0x6A96,0x1A71,0x0A50,0x3A33,0x2A12,
            0xDBFD,0xCBDC,0xFBBF,0xEB9E,0x9B79,0x8B58,0xBB3B,0xAB1A,
            0x6CA6,0x7C87,0x4CE4,0x5CC5,0x2C22,0x3C03,0x0C60,0x1C41,
            0xEDAE,0xFD8F,0xCDEC,0xDDCD,0xAD2A,0xBD0B,0x8D68,0x9D49,
            0x7E97,0x6EB6,0x5ED5,0x4EF4,0x3E13,0x2E32,0x1E51,0x0E70,
            0xFF9F,0xEFBE,0xDFDD,0xCFFC,0xBF1B,0xAF3A,0x9F59,0x8F78,
            0x9188,0x81A9,0xB1CA,0xA1EB,0xD10C,0xC12D,0xF14E,0xE16F,
            0x1080,0x00A1,0x30C2,0x20E3,0x5004,0x4025,0x7046,0x6067,
            0x83B9,0x9398,0xA3FB,0xB3DA,0xC33D,0xD31C,0xE37F,0xF35E,
            0x02B1,0x1290,0x22F3,0x32D2,0x4235,0x5214,0x6277,0x7256,
            0xB5EA,0xA5CB,0x95A8,0x8589,0xF56E,0xE54F,0xD52C,0xC50D,
            0x34E2,0x24C3,0x14A0,0x0481,0x7466,0x6447,0x5424,0x4405,
            0xA7DB,0xB7FA,0x8799,0x97B8,0xE75F,0xF77E,0xC71D,0xD73C,
            0x26D3,0x36F2,0x0691,0x16B0,0x6657,0x7676,0x4615,0x5634,
            0xD94C,0xC96D,0xF90E,0xE92F,0x99C8,0x89E9,0xB98A,0xA9AB,
            0x5844,0x4865,0x7806,0x6827,0x18C0,0x08E1,0x3882,0x28A3,
            0xCB7D,0xDB5C,0xEB3F,0xFB1E,0x8BF9,0x9BD8,0xABBB,0xBB9A,
            0x4A75,0x5A54,0x6A37,0x7A16,0x0AF1,0x1AD0,0x2AB3,0x3A92,
            0xFD2E,0xED0F,0xDD6C,0xCD4D,0xBDAA,0xAD8B,0x9DE8,0x8DC9,
            0x7C26,0x6C07,0x5C64,0x4C45,0x3CA2,0x2C83,0x1CE0,0x0CC1,
            0xEF1F,0xFF3E,0xCF5D,0xDF7C,0xAF9B,0xBFBA,0x8FD9,0x9FF8,
            0x6E17,0x7E36,0x4E55,0x5E74,0x2E93,0x3EB2,0x0ED1,0x1EF0
        ]
        
        rd_ptr = 0
        crc = 0x0000
        byte = 0
        data = bytearray(4)
        pos_s = 0
        for i in range(len(dataIn)):
            if rd_ptr == 0:
                data[0:4] = dataIn[pos_s:pos_s + 4]
                rd_ptr = 4
                pos_s += 4
            rd_ptr -= 1
            byte = (crc >> 8) ^ data[rd_ptr]
            crc = (crc << 8) ^ table[byte]
            crc &= 0xFFFF
        return crc

    def get_flash_size_code(self):
        size = [
            16 * 1024,
            8 * 1024,
            4 * 1024,
            2 * 1024,
            1 * 1024,
            512
        ]
        code = [
            0x3f,
            0x1f,
            0x0f,
            0x07,
            0x03,
            0x01
        ]
        for i in range(6):
            if self.flash_size == size[i]:
                return code[i]
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
            if self.erase_write_fisrt(writebuff[0:self.flash_page_size]) == 0:
                self.exit()
                self.close_prog()
                raise("Write flash: FAIL")
            print(".", end='', sep='', flush=True)

            for i in range(1, numpage - 1):
                if self.erase_write(writebuff[i * self.flash_page_size : (i + 1) * self.flash_page_size]) == 0:
                    self.exit()
                    self.close_prog()
                    raise("Write flash: FAIL")
                print(".", end='', sep='', flush=True)

            if self.erase_write_last(writebuff[i * self.flash_page_size : (i + 1) * self.flash_page_size]) == 0:
                self.exit()
                self.close_prog()
                raise("Write flash: FAIL")
            print(".", end='', sep='', flush=True)
            print("\n")

            #tinh crc
            crc16 = self.crc16(writebuff)

            (res, crc) = self.read_crc16()
            if res == 0:
                self.exit()
                self.close_prog()
                raise("Read CRC16: FAIL")
            
            if crc16 != crc:
                self.exit()
                self.close_prog()
                raise("CRC16: FAIL")
            self.exit()
            self.close_prog()
            print("Done")
'''
rl78 = rl78g10()
rl78.process()
'''
