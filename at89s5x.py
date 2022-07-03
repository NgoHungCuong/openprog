from nhcusb import nhcusb
import spi
import time
import argparse

class at89s5x:
    id = b'\x1e' + b'\x51' + b'\x06'
    flash_size = 4 * 1024
    ver = "NHC_PROG SPI v220601"

    nhcspi = spi.spi()

    def open_prog(self):
        return self.nhcspi.open()

    def close_prog(self):
        self.nhcspi.close()
    
    def get_hw_ver(self):
        return self.nhcspi.get_ver()

    def init_prog(self, clock = 100000):
        return self.nhcspi.spi_init(clock, 1)

    def exit_prog(self):
        return self.nhcspi.spi_exit(0)

    def prog_mode(self):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0x53
        tmp[2] = 0x00
        tmp[3] = 0x00

        (res, tmp) = self.nhcspi.spi_exch(tmp)

        if res == 0:
            return 0
        return tmp[3] == 0x69

    def check_id(self):
        tmp = bytearray(12)
        tmp[0] = 0x28
        tmp[1] = 0x00
        tmp[2] = 0x00
        tmp[3] = 0x00
        tmp[4] = 0x28
        tmp[5] = 0x01
        tmp[6] = 0x00
        tmp[7] = 0x00
        tmp[8] = 0x28
        tmp[9] = 0x02
        tmp[10] = 0x00
        tmp[11] = 0x00

        (res, tmp) = self.nhcspi.spi_exch(tmp)

        if res == 0:
            return 0
        return (tmp[3] == self.id[0]) and (tmp[7] == self.id[1]) and (tmp[11] == self.id[2])

    def erase(self):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0x80
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return 0
        time.sleep(0.5)
        return 1

    def read_flash(self, address, length):
        if length % 16 == 0:
            #truong hop doc chan byte
            n = length // 16
            n *= 64
            tmp = bytearray(n)
            for i in range(length):
                tmp[i * 4] = 0x20
                tmp[i * 4 + 1] = (address + i) // 256
                tmp[i * 4 + 2] = (address + i) % 256
                tmp[i * 4 + 3] = 0x00
            (res, tmp) = self.nhcspi.spi_exch_n(tmp)
            if res == 0:
                return (0, tmp)
            res = bytearray(length)
            for i in range(length):
                res[i] = tmp[i * 4 + 3]
            return (1, res)
        else:
            #truong hop doc le byte
            return self.nhcspi.at89s5x_read(address, length)

    def write_flash(self, data, address):
        return self.nhcspi.at89s5x_write(data, address)

    def read_lock(self):
        tmp = bytearray(4)
        tmp[0] = 0x24
        tmp[1] = 0x00
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return (0, 0)
        return (1, (tmp[3] // 4) % 8)

    def write_lock(self, lock):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0xe0 + lock
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        time.sleep(0.01)
        return res
    
    def process(self):
        #main program
        parser = argparse.ArgumentParser()
        parser.add_argument("--clock", help="Clock in Hz, ex: 100000", type=int)
        parser.add_argument("--check_id", help="check MCU ID (y/n)")
        parser.add_argument("--erase", help="erase Flash (y/n)")
        parser.add_argument("--blank_check", help="blank check Flash (y/n)")
        parser.add_argument("--write_flash", help="Flash file: input.hex, input.bin")
        parser.add_argument("--read_flash", help = "Flash file: output.hex, output.bin")
        parser.add_argument("--verify_flash", help = "Flash file: input.hex, input.bin")
        parser.add_argument("--read_lock", help = "Read lock bits (y/n)")
        parser.add_argument("--write_lock", help = "Write lock bits (y/n)")
        args = parser.parse_args()
        print("=======================================================================================")
        print("openprog by Ngo Hung Cuong")
        print("=======================================================================================")

        if self.open_prog() == 0:
            raise("Open Prog: FAIL")

        if self.ver != self.get_hw_ver():
            self.close_prog()
            raise("Firmware: FAIL")

        if (args.clock != None) and (args.clock != 0):
            if self.init_prog(args.clock) == 0:
                raise("Init Prog: FAIL")    
        else:
            if self.init_prog() == 0:
                raise("Init Prog: FAIL")

        if self.prog_mode() == 0:
            self.exit_prog()
            self.close_prog()
            raise("Programming mode: FAIL")

        #check ID
        if args.check_id == 'y':
            if self.check_id() == 0:
                self.exit_prog()
                self.close_prog()
                raise("Check ID: FAIL")

        #erase
        if args.erase == 'y':
            if self.erase() == 0:
                self.exit_prog()
                self.close_prog()
                raise("Erase: FAIL")
            print("Erase: Done")

        #blank check
        if args.blank_check == 'y':
            print("Blank check:")
            page_size = 512
            for i in range(self.flash_size // page_size):
                (res, tmp) = self.read_flash(i * page_size, page_size)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Read flash: FAIL")
                for j in range(page_size):
                    if tmp[j] != 0xff:
                        self.exit_prog()
                        self.close_prog()
                        raise("Blank check: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")

        #write flash
        if args.write_flash != None:
            print("Write:")
            f = open(args.write_flash, "rb")
            writebuff = f.read()
            f.close()
            n = len(writebuff)
            writebuff += b'\xff' * (self.flash_size - n)
            page_size = 512
            for i in range(self.flash_size // page_size):
                res = self.write_flash(writebuff[(i * page_size): (i * page_size + page_size)], i * page_size)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Write flash: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")

        #read flash
        if args.read_flash != None:
            print("Read:")
            f = open(args.read_flash, "wb")
            page_size = 512
            for i in range(self.flash_size // page_size):
                (res, tmp) = self.read_flash(i * page_size, page_size)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Read flash: FAIL")
                f.write(tmp)
                print(".", end='', sep='', flush=True)
            f.close()
            print("\n")

        #verify flash
        if args.verify_flash != None:
            f = open(args.verify_flash, "rb")
            writebuff = f.read()
            f.close()
            n = len(writebuff)
            writebuff += b'\xff' * (self.flash_size - n)
            print("Verify:")
            page_size = 512
            for i in range(self.flash_size // page_size):
                (res, tmp) = self.read_flash(i * page_size, page_size)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Read flash: FAIL")
                for j in range(page_size):
                    if tmp[j] != writebuff[i * page_size + j]:
                        self.exit_prog()
                        self.close_prog()
                        raise("Verify flash: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")

        #read lock bits
        if args.read_lock == 'y':
            print("Read lock bits:")
            (res, lock) = self.read_lock()
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Read lock bits: FAIL")
            print(hex(lock))

        #write lock bits
        if args.write_lock == 'y':
            print("Write lock bits:")
            res = self.write_lock(1)
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("write lock bits: FAIL")
            res = self.write_lock(2)
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("write lock bits: FAIL")
            res = self.write_lock(3)
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("write lock bits: FAIL")

        self.exit_prog()
        self.close_prog()
        print("Done")

"""
prog = at89s5x()
prog.process()
"""
