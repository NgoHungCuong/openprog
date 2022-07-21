from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex
import at24c

class at24c512(at24c.at24c):

    eeprom_size = 512 * 1024 // 8
    eeprom_page_size = 128
    address_size = 2


nhci2c = at24c512()
nhci2c.process()

