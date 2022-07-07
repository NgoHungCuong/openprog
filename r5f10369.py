from distutils.command.build import build
from distutils.util import subst_vars
import nhcusb
import sys
import struct
import argparse
from intelhex import IntelHex
import rl78g12

class r5f10369(rl78g12.rl78g12):
    flash_size = 12 * 1024
            
rl78 = r5f10369()
rl78.process()
