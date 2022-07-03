from distutils.command.build import build
import nhcusb
import struct

class bootloader:

    CHECK_MCU_ID = b'\x00'
    FLASH_PAGE_ERASE = b'\x03'
    FLASH_READ_CMD = b'\x04'
    FLASH_WRITE_CMD = b'\x05'
    RESET_TO_AP = b'\x02'
    WRITE_TO_BUFF = b'\x10'
    READ_FROM_BUFF = b'\x11'
    GET_VER = b'\x01'

    usb = nhcusb.nhcusb()

    def open(self):
        return self.usb.open(0x0416, 0x0002)

    def close(self):
        self.usb.close()

    def get_ver(self):
        ver = ""
        tmp = self.GET_VER + b'\x00' * 63
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

    def check_mcu_id(self):
        tmp = self.CHECK_MCU_ID + b'\x00' * 63
        if self.usb.write(tmp):
            (res, tmp) = self.usb.read()
            if res:
                (u32Id, ) = struct.unpack('<I', tmp[:4])
                if u32Id == 0x00F252B0:
                    return 1
                else:
                    return 0
            else:
                return 0
        return 0

    def flash_erase_page(self, address):
        tmp = self.FLASH_PAGE_ERASE + struct.pack('<L', address) + b'\x00' * 59
        if (self.usb.write(tmp)):
            (res, tmp) = self.usb.read()
            if res:
                if tmp[0]:
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def flash_read(self, address, num):
        tmp = self.FLASH_READ_CMD + struct.pack('<L', address) + struct.pack('<L', num) + b'\x00' * 55
        if (self.usb.write(tmp)):
            (res, tmp) = self.usb.read()
            if res:
                tmp = self.READ_FROM_BUFF + struct.pack('<L', num // 64) + b'\x00' * 59
                if (self.usb.write(tmp)):
                    return self.usb.read(num)
                else:
                    return (0, tmp)
            else:
                return (0, tmp)
        else:
            return (0, tmp)

    def flash_write(self, address, num, data):
        tmp = self.WRITE_TO_BUFF + struct.pack('<L', num // 64) + b'\x00' * 59
        if self.usb.write(tmp):
            if self.usb.write(data, num):
                tmp = self.FLASH_WRITE_CMD + struct.pack('<L', address) + struct.pack('<L', num) + b'\x00' * 55
                if self.usb.write(tmp):
                    (res, tmp) = self.usb.read()
                    return res
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    
    def reset_to_ap(self):
        tmp = self.RESET_TO_AP + b'\x00' * 63
        return self.usb.write(tmp)

