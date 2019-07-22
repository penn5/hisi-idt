#!/usr/bin/env python3.7

from adb.fastboot import FastbootCommands, FastbootRemoteFailure, FastbootStateMismatch, FastbootInvalidResponse
from adb.adb_commands import AdbCommands
from adb.usb_exceptions import *
import time, functools

def info_cb(fdev, partition, image, msg):
    if msg.header == b"FAIL":
        print(msg)
        if msg.message == b"ultraflash not permitted\x00":
            # try normal flash
            fdev.FlashFromFile(partition, image, info_cb=functools.partial(info_cb, fdev, partition, image), progress_callback=progress_cb)
        raise RuntimeError("Flash Failed")
    print(msg)

def progress_cb(current, total):
    print("flashing current img "+str(100*current/total))

def flash(parts):
    fdev = FastbootCommands()
    while True:
        try:
            fdev.ConnectDevice()
            break
        except DeviceNotFoundError:
            time.sleep(10)
    # For faster flashing we take advantage of "ultraflash" which lets you stream the image
    for partition, file in parts:
        # File must be a filename, not a file()
        if partition == "huawei_crc_check":
            fdev.FlashFromFile(partition, file, info_cb=functools.partial(info_cb, fdev, partition, file), progress_callback=progress_cb)
            continue
        fdev._SimpleCommand(b'ultraflash', arg=partition, info_cb=functools.partial(info_cb, fdev, partition, file), timeout_ms=0)
        fdev.Download(file, info_cb=info_cb, progress_callback=progress_cb)
