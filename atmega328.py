from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class atmega328(avr.avr):
    id = b'\x1e' + b'\x95' + b'\x14'
    flash_size = 32 * 1024
    flash_page_size = 128
    eeprom_size = 1024
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = atmega328()
prog.process()

