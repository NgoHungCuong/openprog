from nhcusb import nhcusb
import spi
import time
import argparse
import at89s5x

class at89s52(at89s5x.at89s5x):
    id = b'\x1e' + b'\x52' + b'\x06'
    flash_size = 8 * 1024

prog = at89s52()
prog.process()
