from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import time
import argparse
from intelhex import IntelHex
import at24c

class at24c256(at24c.at24c):

    eeprom_size = 256 * 1024 // 8
    eeprom_page_size = 64
    address_size = 2


nhci2c = at24c256()
nhci2c.process()

