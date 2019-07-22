#!/usr/bin/env python3.7

# Copyright 2019 Penn Mackintosh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import imageflasher
import fastbootflasher
import idtconfig

import argparse, os

def main(config, device, full, chip=""):
    # First parse the config
    idt_images, fastboot_images = idtconfig.get_images(config.read())
    flasher = imageflasher.ImageFlasher(chip)
    if not device is False:
        flasher.connect_serial(device)
    for addr, fil in idt_images.items():
        flasher.download_from_disk(os.path.join(os.path.dirname(config.name), fil.replace("/", os.path.sep)), addr)
    print("Flash successful!")
    if full:
        print(idt_images, fastboot_images)
        print("Waiting for device to connect. Please do not disconnect the USB or reboot the device.")
        fastbootflasher.flash([(k, os.path.join(os.path.dirname(config.name), v.replace("/", os.path.sep))) for k, v in fastboot_images if not ('MODEM' in k or 'NVM' in k or 'OEMINFO' in k)])
    else:
        print("Wait around 5 minutes with the USB plugged in and the device will enter fastboot. Use fastboot to reflash/recover your system.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(epilog="""Copyright 2019 Penn Mackintosh

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.""")
    parser.add_argument("--norun", "-n", action="store_false", dest="run")
    parser.add_argument("--device", "-d")
    parser.add_argument("--fastboot", "--full", "-f", help="Flashes all fastboot images from the IDT config as well. Will erase IMEI, SN, etc. Not supported with hikey config", action="store_true", default=False, dest="full")
    parser.add_argument("config")
    args = parser.parse_args()
    with open(args.config, "rb") as f:
        main(f, args.device if args.run else False, args.full)
