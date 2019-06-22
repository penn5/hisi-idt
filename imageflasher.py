#!/usr/bin/env python3.7
# Reworked from https://github.com/96boards-hikey/tools-images-hikey970/blob/hikey970_v1.0/hisi-idt.py

# Copyright 2019 Penn Mackintosh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import binascii, itertools, logging, serial, serial.tools.list_ports, os

def calc_crc(data, crc=0):
    for char in data:
        crc = ((crc << 8) | char) ^ binascii.crc_hqx(bytes([(crc >> 8) & 0xFF]), 0)
    for i in range(0,2):
        crc = ((crc << 8) | 0) ^ binascii.crc_hqx(bytes([(crc >> 8) & 0xFF]), 0)
    return crc & 0xFFFF

class FlashException(Exception):
    def __init__(self, code, *info):
        self.code = code
        self.info = info
        super(FlashException, self).__init__(info)

class DeviceDetectException(Exception):
    def __init__(self, code, *info):
        self.code = code
        self.info = info
        super(DeviceDetectException, self).__init__(info)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("imageflasher")

startframe = {
    "hi3660": bytes([0xFE,0x00,0xFF,0x01,0x00,0x00,0x00,0x04,0x00,0x00,0x02,0x01]),

    "": bytes([0xFE,0x00,0xFF,0x01,0x00,0x00,0x00,0x04,0x00,0x00,0x02,0x01])
}

headframe = {
    "hi3660": bytes([0xFE,0x00,0xFF,0x01]),

    "": bytes([0xFE,0x00,0xFF,0x01])
}

dataframe = {
    "hi3660": bytes([0xDA]),

    "": bytes([0xDA])
}

tailframe = {
    "hi3660": bytes([0xED]),

    "": bytes([0xED])
}

ack = {
    "hi3660": bytes([0xAA]),

    "": bytes([0xAA])
}

BOOT_HEAD_LEN = 0x4F00
MAX_DATA_LEN = 0x400
IDT_BAUDRATE = 115200
IDT_VID=0x12D1
IDT_PID=0x3609

BAD_ACK = 1
INVALID_LENGTH = 2

TOO_MANY_DEVICES = 1
NOT_ENOUGH_DEVICES = 2

class ImageFlasher():

    def __init__(self, chip):
        self.startframe = startframe.get(chip, startframe[""])
        self.headframe = headframe.get(chip, headframe[""])
        self.dataframe = dataframe.get(chip, dataframe[""])
        self.tailframe = tailframe.get(chip, tailframe[""])
        self.ack = ack.get(chip, ack[""])
        self.serial = None

    def send_frame(self, data, loop):
        crc = calc_crc(data)
        data = data + crc.to_bytes(2, byteorder="big", signed=False)
        for _ in itertools.repeat(None, loop-1):
            if self.serial:
                self.serial.reset_output_buffer()
                self.serial.reset_input_buffer()
                self.serial.write(data)
                ack = self.serial.read(1)
            else:
                ack = self.ack
            if ack and ack != self.ack:
                print()
                raise FlashException(BAD_ACK, "Invalid ACK from device. Flashing was corrupted.", ack, self.ack, data, crc, data)
            else:
                log.debug(f"Sent frame of {len(data)} bytes to device successfully! CRC16 was {crc}")

    def send_start_frame(self):
        if self.serial:
            self.serial.timeout = 0.03
        log.info("Sending start frame")
        self.send_frame(self.startframe, 10000)

    def send_head_frame(self, length, address):
        if self.serial:
            self.serial.timeout = 0.09
        log.info("Sending header frame")
        data = self.headframe
        data += length.to_bytes(4, byteorder="big", signed=False)
        data += address.to_bytes(4, byteorder="big", signed=False)
        self.send_frame(data, 16)

    def send_data_frame(self, n, data):
        if self.serial:
            self.serial.timeout = 0.45
        logging.debug("Sending data frame")
        head = bytearray(self.dataframe)
        head.append(n & 0xFF)
        head.append((~ n) & 0xFF)
        self.send_frame(bytes(head) + data, 32)

    def send_tail_frame(self, n):
        if self.serial:
            self.serial.timeout = 0.01
        logging.info("Sending tail frame")
        data = bytearray(self.tailframe)
        data.append(n & 0xFF)
        data.append((~ n) & 0xFF)
        self.send_frame(bytes(data), 16)

    def send_data(self, data, length, address):
        if isinstance(data, bytes):
            length = len(data)
        if length == 0 or not isinstance(length, int):
            raise FlashException(INVALID_LENGTH)
        nframes = length // MAX_DATA_LEN + (1 if length % MAX_DATA_LEN > 0 else 0)
        self.send_head_frame(length, address)
        n = 0
        while length > MAX_DATA_LEN:
            if isinstance(data, bytes):
                f = data[n*MAX_DATA_LEN:(n+1)*MAX_DATA_LEN]
            else:
                f = data.read(MAX_DATA_LEN)
            n += 1
            self.send_data_frame(n, f)
            length -= MAX_DATA_LEN
            print(f"frame {n}; total frames {nframes}; % complete {100*n/nframes}", end="\r")
        if length:
            if isinstance(data, bytes):
                f = data[n*MAX_DATA_LEN:]
            else:
                f = data.read()
            n += 1
            self.send_data_frame(n, f)
        print(f"frame {n}; total frames {nframes}; % complete {100*n/nframes}")
        self.send_tail_frame(n+1)
        print("DONE!!!")

    def download_from_disk(self, fil, address):
        if fil == "-":
            f = sys.stdin
        else:
            f = open(fil, "rb")
        self.send_data(f, os.stat(fil).st_size, address)

    def connect_serial(self, device=None):
        if device == None:
            ports = serial.tools.list_ports.comports(include_links=False)
            for port in ports:
                if port.vid == IDT_VID and port.pid == IDT_PID:
                    logging.warn(f"Autoselecting {port.hwid} aka {port.description} at {port.device}")
                    if device != None:
                        raise DeviceDetectException(TOO_MANY_DEVICES, "Multiple devices detected in IDT mode", device, port)
                    else:
                        device = port.device
        if device == None:
            raise DeviceDetectException(NOT_ENOUGH_DEVICES, "Need a device in IDT mode plugged in to this computer")
        self.serial = serial.Serial(dsrdtr=True, rtscts=True, port=device.replace("COM", r"\\.\COM"), baudrate=IDT_BAUDRATE, timeout=1)

    def __enter__(self):
        pass
    def __exit__(self):
        try:
            self.serial.close()
        except:
            pass
