from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import argparse
from intelhex import IntelHex
import rl78g10

class r5f10y14(rl78g10.rl78g10):
    flash_size = 1 * 1024

rl78 = r5f10y14()
rl78.process()

