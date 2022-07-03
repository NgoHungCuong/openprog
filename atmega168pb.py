from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class atmega168pb(avr.avr):
    id = b'\x1e' + b'\x94' + b'\x15'
    flash_size = 16 * 1024
    flash_page_size = 128
    eeprom_size = 512
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = atmega168pb()
prog.process()

