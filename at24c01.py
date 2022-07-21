from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex
import at24c

class at24c01(at24c.at24c):

    eeprom_size = 1 * 1024 // 8
    eeprom_page_size = 1
    address_size = 1

nhci2c = at24c01()
nhci2c.process()
