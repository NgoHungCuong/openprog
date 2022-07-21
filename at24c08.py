from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex
import at24c

class at24c08(at24c.at24c):

    eeprom_size = 8 * 1024 // 8
    eeprom_page_size = 4
    address_size = 1

nhci2c = at24c08()
nhci2c.process()
