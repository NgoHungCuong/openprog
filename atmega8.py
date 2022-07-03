from nhcusb import nhcusb
import spi
import time
import argparse
import avr

class atmega8(avr.avr):
    id = b'\x1e' + b'\x93' + b'\x07'
    flash_size = 8 * 1024
    flash_page_size = 64
    eeprom_size = 512
    eeprom_page_size = 1
    chip_erase_time = 10 #10ms
    page_write_time = 5 #5ms
    eeprom_write_time = 9 #9ms
    fuse_write_time = 5 #5ms

    ver = "NHC_PROG SPI v220601"

    nhcspi = spi.spi()

    def hex_parse(self, input):
        return int(input, 0)

    def open_prog(self):
        return self.nhcspi.open()

    def close_prog(self):
        self.nhcspi.close()
    
    def get_hw_ver(self):
        return self.nhcspi.get_ver()

    def init_prog(self, clock = 100000):
        return self.nhcspi.spi_init(clock, 0)

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
        return tmp[2] == 0x53

    def check_id(self):
        tmp = bytearray(12)
        tmp[0] = 0x30
        tmp[1] = 0x00
        tmp[2] = 0x00
        tmp[3] = 0x00
        tmp[4] = 0x30
        tmp[5] = 0x00
        tmp[6] = 0x01
        tmp[7] = 0x00
        tmp[8] = 0x30
        tmp[9] = 0x00
        tmp[10] = 0x02
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
        time.sleep(self.chip_erase_time * 0.001)
        return 1

    def read_flash(self, address, length):
        if length < 16:
            #truong hop doc nho hon 16 byte
            n = length
            n *= 4
            tmp = bytearray(n)
            address //= 2
            length //= 2
            for i in range(length):
                tmp[i * 8] = 0x20
                tmp[i * 8 + 1] = (address + i) // 256
                tmp[i * 8 + 2] = (address + i) % 256
                tmp[i * 8 + 3] = 0x00
                tmp[i * 8 + 4] = 0x28
                tmp[i * 8 + 5] = (address + i) // 256
                tmp[i * 8 + 6] = (address + i) % 256
                tmp[i * 8 + 7] = 0x00
            (res, tmp) = self.nhcspi.spi_exch(tmp)
            if res == 0:
                return (0, tmp)
            length *= 2
            res = bytearray(length)
            for i in range(length):
                res[i] = tmp[i * 4 + 3]
            return (1, res)
        else:
            #truong hop doc lon hon 16 byte
            n = length
            n *= 4
            tmp = bytearray(n)
            address //= 2
            length //= 2
            for i in range(length):
                tmp[i * 8] = 0x20
                tmp[i * 8 + 1] = (address + i) // 256
                tmp[i * 8 + 2] = (address + i) % 256
                tmp[i * 8 + 3] = 0x00
                tmp[i * 8 + 4] = 0x28
                tmp[i * 8 + 5] = (address + i) // 256
                tmp[i * 8 + 6] = (address + i) % 256
                tmp[i * 8 + 7] = 0x00
            (res, tmp) = self.nhcspi.spi_exch_n(tmp)
            if res == 0:
                return (0, tmp)
            length *= 2
            res = bytearray(length)
            for i in range(length):
                res[i] = tmp[i * 4 + 3]
            return (1, res)

    def write_flash(self, data, address):
        need = 0
        pos = 0
        n = len(data)
        for i in range(n):
            if data[i] != 0xff:
                need = 1
                pos = i
                break
        if need == 0:
            return 1
        if n < 16:
            tmp = bytearray(n * 4)
            n //= 2
            for i in range(n):
                tmp[i * 8] = 0x40
                tmp[i * 8 + 1] = 0x00
                tmp[i * 8 + 2] = i
                tmp[i * 8 + 3] = data[i * 2]
                tmp[i * 8 + 4] = 0x48
                tmp[i * 8 + 5] = 0x00
                tmp[i * 8 + 6] = i
                tmp[i * 8 + 7] = data[i * 2 + 1]
            (res, tmp) = self.nhcspi.spi_exch(tmp)
            if res == 0:
                return 0
            
            tmp = bytearray(4)
            tmp[0] = 0x4c
            tmp[1] = (address // 2) // 256
            tmp[2] = (address // 2) % 256
            tmp[3] = 0
            (res, tmp) = self.nhcspi.spi_exch(tmp)
            if res == 0:
                return 0

            #polling
            poll = 0
            for i in range (self.page_write_time):
                tmp = bytearray(4)
                if pos % 2:
                    tmp[0] = 0x28
                else:
                    tmp[0] = 0x20
                tmp[1] = ((address) // 2) // 256
                tmp[2] = ((address) // 2) % 256
                tmp[3] = 0x00
                (res, tmp) = self.nhcspi.spi_exch(tmp)
                if res == 0:
                    return 0
                if tmp[3] == data[pos]:
                    poll = 1
                    break
                time.sleep(0.001)
            if poll == 0:
                return 0

        else:
            tmp = bytearray(n * 4)
            n //= 2
            for i in range(n):
                tmp[i * 8] = 0x40
                tmp[i * 8 + 1] = 0x00
                tmp[i * 8 + 2] = i
                tmp[i * 8 + 3] = data[i * 2]
                tmp[i * 8 + 4] = 0x48
                tmp[i * 8 + 5] = 0x00
                tmp[i * 8 + 6] = i
                tmp[i * 8 + 7] = data[i * 2 + 1]
            (res, tmp) = self.nhcspi.spi_exch_n(tmp)
            if res == 0:
                return 0
            
            tmp = bytearray(4)
            tmp[0] = 0x4c
            tmp[1] = (address // 2) // 256
            tmp[2] = (address // 2) % 256
            tmp[3] = 0
            (res, tmp) = self.nhcspi.spi_exch(tmp)
            if res == 0:
                return 0

            #polling
            poll = 0
            for i in range (self.page_write_time):
                tmp = bytearray(4)
                if pos % 2:
                    tmp[0] = 0x28
                else:
                    tmp[0] = 0x20
                tmp[1] = ((address) // 2) // 256
                tmp[2] = ((address) // 2) % 256
                tmp[3] = 0x00
                (res, tmp) = self.nhcspi.spi_exch(tmp)
                if res == 0:
                    return 0
                if tmp[3] == data[pos]:
                    poll = 1
                    break
                time.sleep(0.001)
            if poll == 0:
                return 0

        return 1

    def write_eeprom(self, data, address):
        if data == 0xff:
            return 1
        
        tmp = bytearray(4)
        tmp[0] = 0xc0
        tmp[1] = address // 256
        tmp[2] = address % 256
        tmp[3] = data
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return 0

        #polling
        poll = 0
        for i in range (self.eeprom_write_time):
            tmp = bytearray(4)
            tmp[0] = 0xa0
            tmp[1] = address // 256
            tmp[2] = address % 256
            tmp[3] = 0x00
            (res, tmp) = self.nhcspi.spi_exch(tmp)
            if res == 0:
                return 0
            if tmp[3] == data:
                poll = 1
                break
            time.sleep(0.001)
        if poll == 0:
            return 0

        return 1

    def read_eeprom(self, address, length):
        if length < 16:
            #truong hop doc nho hon 16 byte
            n = length
            n *= 4
            tmp = bytearray(n)
            
            for i in range(n):
                tmp[0] = 0xa0
                tmp[1] = (address + i) // 256
                tmp[2] = (address + i) % 256
                tmp[3] = 0x00
            (res, tmp) = self.nhcspi.spi_exch(tmp)
            if res == 0:
                return (0, tmp)

            res = bytearray(length)
            for i in range(length):
                res[i] = tmp[i * 4 + 3]
            return (1, res)
        else:
            #truong hop doc lon hon 16 byte
            n = length
            n *= 4
            tmp = bytearray(n)
            
            for i in range(length):
                tmp[i * 4] = 0xa0
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

    #write fuse E
    def write_fuse_e(self, fuseVal):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0xa4
        tmp[2] = 0x00
        tmp[3] = fuseVal
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        time.sleep(self.fuse_write_time * 0.001)
        return res

    #write fuse H
    def write_fuse_h(self, fuseVal):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0xa8
        tmp[2] = 0x00
        tmp[3] = fuseVal
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        time.sleep(self.fuse_write_time * 0.001)
        return res

    #write fuse L
    def write_fuse_l(self, fuseVal):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0xa0
        tmp[2] = 0x00
        tmp[3] = fuseVal
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        time.sleep(self.fuse_write_time * 0.001)
        return res

    #read fuse E
    def read_fuse_e(self):
        tmp = bytearray(4)
        tmp[0] = 0x50
        tmp[1] = 0x08
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return (0, 0)
        return (1, tmp[3])

    #read fuse H
    def read_fuse_h(self):
        tmp = bytearray(4)
        tmp[0] = 0x58
        tmp[1] = 0x08
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return (0, 0)
        return (1, tmp[3])

    #read fuse L
    def read_fuse_l(self):
        tmp = bytearray(4)
        tmp[0] = 0x50
        tmp[1] = 0x00
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return (0, 0)
        return (1, tmp[3])

    #read lock bits
    def read_lock(self):
        tmp = bytearray(4)
        tmp[0] = 0x58
        tmp[1] = 0x00
        tmp[2] = 0x00
        tmp[3] = 0x00
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        if res == 0:
            return (0, 0)
        return (1, tmp[3])

    #write lock bits
    def write_lock(self, lock):
        tmp = bytearray(4)
        tmp[0] = 0xac
        tmp[1] = 0xe0
        tmp[2] = 0x00
        tmp[3] = lock
        (res, tmp) = self.nhcspi.spi_exch(tmp)
        time.sleep(self.chip_erase_time * 0.001)
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
        parser.add_argument("--write_eeprom", help="EEPROM file: input.hex, input.bin")
        parser.add_argument("--read_eeprom", help = "EEPROM file: output.hex, output.bin")
        parser.add_argument("--verify_eeprom", help = "EEPROM file: input.hex, input.bin")
        parser.add_argument("--write_fuseE", help="Fuse E, ex: 0xFE")
        parser.add_argument("--write_fuseH", help="Fuse H, ex: 0xFE")
        parser.add_argument("--write_fuseL", help="Fuse L, ex: 0xFE")
        parser.add_argument("--read_fuseE", help="Fuse E (y/n)")
        parser.add_argument("--read_fuseH", help="Fuse H (y/n)")
        parser.add_argument("--read_fuseL", help="Fuse L (y/n)")
        parser.add_argument("--read_lock", help = "Read lock bits (y/n)")
        parser.add_argument("--write_lock", help = "Write lock bits, ex: 0xFE")
        args = parser.parse_args()

        print("=======================================================================================")
        print("NHC Pro by Ngo Hung Cuong")
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
            page_size = self.flash_page_size
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

        #write eeprom
        if args.write_eeprom != None:
            print("Write EEPROM:")
            f = open(args.write_eeprom, "rb")
            writebuff = f.read()
            f.close()
            n = len(writebuff)
            writebuff += b'\xff' * (self.eeprom_size - n)
            page_size = self.eeprom_page_size
            for i in range(self.eeprom_size // page_size):
                res = self.write_eeprom(writebuff[i], i)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Write EEPROM: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")

        #read eeprom
        if args.read_eeprom != None:
            print("Read EEPROM:")
            f = open(args.read_eeprom, "wb")
            if self.eeprom_size > 512:
                page_size = 512
            else:
                page_size = self.eeprom_size
            
            for i in range(self.eeprom_size // page_size):
                (res, tmp) = self.read_eeprom(i * page_size, page_size)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Read EEPROM: FAIL")
                f.write(tmp)
                print(".", end='', sep='', flush=True)
            f.close()
            print("\n")

        #verify eeprom
        if args.verify_eeprom != None:
            print("Verify EEPROM:")
            f = open(args.verify_eeprom, "rb")
            writebuff = f.read()
            f.close()
            n = len(writebuff)
            writebuff += b'\xff' * (self.eeprom_size - n)
            
            if self.eeprom_size > 512:
                page_size = 512
            else:
                page_size = self.eeprom_size
            
            for i in range(self.eeprom_size // page_size):
                (res, tmp) = self.read_eeprom(i * page_size, page_size)
                if res == 0:
                    self.exit_prog()
                    self.close_prog()
                    raise("Read EEPROM: FAIL")
                for j in range(page_size):
                    if tmp[j] != writebuff[i * page_size + j]:
                        raise("Verify EEPROM: FAIL")
                print(".", end='', sep='', flush=True)
            print("\n")
        
        #write fuse E
        if args.write_fuseE != None:
            print("Write Fuse E:")
            res = self.write_fuse_e(self.hex_parse(args.write_fuseE))
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Write Fuse E: FAIL")
        
        #write fuse H
        if args.write_fuseH != None:
            print("Write Fuse H:")
            res = self.write_fuse_h(self.hex_parse(args.write_fuseH))
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Write Fuse H: FAIL")

        #write fuse L
        if args.write_fuseL != None:
            print("Write Fuse L:")
            res = self.write_fuse_l(self.hex_parse(args.write_fuseL))
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Write Fuse L: FAIL")

        #Read fuse E
        if args.read_fuseE == 'y':
            print("Read Fuse E:")
            (res, tmp) = self.read_fuse_e()
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Read Fuse E: FAIL")
            print(hex(tmp))

        #Read fuse H
        if args.read_fuseH == 'y':
            print("Read Fuse H:")
            (res, tmp) = self.read_fuse_h()
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Read Fuse H: FAIL")
            print(hex(tmp))

        #Read fuse L
        if args.read_fuseL == 'y':
            print("Read Fuse L:")
            (res, tmp) = self.read_fuse_l()
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("Read Fuse L: FAIL")
            print(hex(tmp))

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
        if args.write_lock != None:
            print("Write lock bits:")
            res = self.write_lock(self.hex_parse(args.write_lock))
            if res == 0:
                self.exit_prog()
                self.close_prog()
                raise("write lock bits: FAIL")

        self.exit_prog()
        self.close_prog()
        print("Done")

prog = atmega8()
prog.process()

