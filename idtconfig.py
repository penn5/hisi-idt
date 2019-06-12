#!/usr/bin/env python3.7

# Copyright 2019 Penn Mackintosh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from lxml import etree
import re

def get_images(cfg: bytes):
    try:
        tree = etree.fromstring(cfg)
    except:
        raise
        return get_simple(cfg.decode("utf-8")), {}
    ddr_images = tree.xpath("(//configurations/configuration)[1]/bootloaderimage_ddr/image")
    std_images = tree.xpath("(//configurations/configuration)[1]/bootloaderimage/image")
    idt_images = {int(img.get("address"), 0):img.text for img in ddr_images}
    ddr_ids = [img.get("identifier") for img in ddr_images]
    for img in std_images:
        if not img.get("identifier") in ddr_ids:
            idt_images[int(img.get("address"), 0)] = img.text
    print(idt_images)
    fastboot_images = {img.get("identifier", 0):img.text for img in tree.xpath("(//configurations/configuration)[1]/fastbootimage/image")}
    return idt_images, fastboot_images

def get_simple(cfg):
    ret = {}
    for line in cfg.split("\n"):
        match = re.fullmatch(r"(\w+)(?:\W+)(.+)", line)
        if not match:
            continue
        addr = int(match[1], 0)
        file = match[2]
        ret[addr] = file
    return ret
