import bootloader
import sys

boot = bootloader.bootloader()

n = len(sys.argv)

if n != 2:
    raise("Using: firmware.py firmware_name.bin")

if boot.open():
    if boot.get_ver() != "NHCPro Bootloader":
        raise("Check version: FAIL")
    
    if boot.check_mcu_id():
        #erase
        print("Erase:")
        for i in range(64):
            if boot.flash_erase_page(i * 512):
                print('.', end='', sep='', flush=True)
            else:
                raise("Erase: FAIL")
        
        #write        
        print("\nWrite:")
        try:
            f = open(sys.argv[1], "rb")
        except:
            raise("Open firmware file: FAIL")
        #f = open(sys.argv[1], "rb")
        writebuff = f.read()
        f.close()
        n = len(writebuff)
        writebuff += b'\xff' * (32 * 1024 - n)
        readbuff = bytearray()

        for i in range(8):
            if boot.flash_write(i * 4 * 1024, 4 * 1024, writebuff[(i * 4 * 1024): (i * 4 * 1024 + 4 * 1024)]):
                print('.', end='', sep='', flush=True)
            else:
                raise("Write flash: FAIL")
        
        #read and verify
        print("\nRead and Verify:")
        for i in range(8):
            (res, tmp) = boot.flash_read(i * 4 * 1024, 4 * 1024)
            if res:
                readbuff += tmp
                print('.', end='', sep='', flush=True)
            else:
                raise("Read flash: FAIL")
        
        for i in range(32 * 1024):
            if writebuff[i] != readbuff[i]:
                raise("Verify: FAIL")
        print("\nOK")
        boot.reset_to_ap()
    else:
        raise("Check MCU: FAIL")
else:
    raise("Check USB: FAIL")