from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex
import at24c

class at24c04(at24c.at24c):

    eeprom_size = 4 * 1024 // 8
    eeprom_page_size = 2
    address_size = 1

nhci2c = at24c04()
nhci2c.process()
