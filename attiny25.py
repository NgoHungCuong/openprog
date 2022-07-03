from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class attiny13(avr.avr):
    id = b'\x1e' + b'\x91' + b'\x08'
    flash_size = 2 * 1024
    flash_page_size = 32
    eeprom_size = 128
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = attiny13()
prog.process()

