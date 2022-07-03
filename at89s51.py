from nhcusb import nhcusb
import spi
import time
import argparse
import at89s5x

class at89s51(at89s5x.at89s5x):
    id = b'\x1e' + b'\x51' + b'\x06'
    flash_size = 4 * 1024

prog = at89s51()
prog.process()
