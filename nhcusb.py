import usb.core
import usb.util
import usb.backend.libusb0
backend = usb.backend.libusb0.get_backend(find_library=lambda x: "libusb0.dll")

class nhcusb:
    dev = None
    def open(self, vid, pid):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid, backend=backend)
        if self.dev is None:
            return 0
        self.dev.set_configuration()
        usb.util.claim_interface(self.dev, 0)
        return 1

    def close(self):
        if self.dev is not None:
            usb.util.release_interface(self.dev, 0)
            usb.util.dispose_resources(self.dev)
            self.dev = None

    def write(self, data, length = 64, ep = 0x01):
        tmp = bytearray(length)
        for i in range(length):
            tmp[i] = data[i]
        count = self.dev.write(ep, tmp, 5000)
        return count == length

    def read(self, length = 64, ep = 0x81):
        tmp = self.dev.read(ep, length, 5000)
        if len(tmp) != length:
            return 0, tmp
        return 1, tmp

