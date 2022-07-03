from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class atmega128(avr.avr):
    id = b'\x1e' + b'\x97' + b'\x02'
    flash_size = 128 * 1024
    flash_page_size = 256
    eeprom_size = 4 * 1024
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = atmega128()
prog.process()

