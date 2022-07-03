from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class atmega8u2(avr.avr):
    id = b'\x1e' + b'\x93' + b'\x89'
    flash_size = 8 * 1024
    flash_page_size = 64
    eeprom_size = 256
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = atmega8u2()
prog.process()

