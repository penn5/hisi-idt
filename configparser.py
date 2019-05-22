#!/usr/bin/env python3.7

from lxml import etree

def get_images(xml: bytes):
    tree = etree.fromstring(xml)
    ddr_images = tree.xpath("(//configurations/configuration)[1]/bootloaderimage_ddr/image")
    std_images = tree.xpath("(//configurations/configuration)[1]/bootloaderimage/image")
    images = {int(img.get("address"), 0):img.text for img in ddr_images}
    print(images)
    ddr_ids = [img.get("identifier") for img in ddr_images]
    for img in std_images:
        if not img.get("identifier") in ddr_ids:
            images[int(img.get("address"), 0)] = img.text
    print(images)
get_images(open("COL-BD_1.0.0.35_Download.xml", "rb").read()) # Should be rb
