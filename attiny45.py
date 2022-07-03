from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class attiny13(avr.avr):
    id = b'\x1e' + b'\x92' + b'\x06'
    flash_size = 4 * 1024
    flash_page_size = 64
    eeprom_size = 256
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = attiny13()
prog.process()

