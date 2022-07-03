from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class atmega88pa(avr.avr):
    id = b'\x1e' + b'\x93' + b'\x0f'
    flash_size = 8 * 1024
    flash_page_size = 64
    eeprom_size = 512
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

prog = atmega88pa()
prog.process()

