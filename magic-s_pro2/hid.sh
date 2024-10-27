#!/bin/bash
modprobe libcomposite

cd /sys/kernel/config/usb_gadget
mkdir -p g1
cd g1

echo 0x0f0d > idVendor  # Hori Co., Ltd
echo 0x00c1 > idProduct # HORIPAD
echo 0x0100 > bcdDevice # v1.0.0
echo 0x0200 > bcdUSB    # USB2
echo 0x00   > bDeviceClass
echo 0x00   > bDeviceSubClass
echo 0x00   > bDeviceProtocol

mkdir -p strings/0x409
echo "00000000"      > strings/0x409/serialnumber
echo "sakebitarinya" > strings/0x409/manufacturer
echo "USB Game Pad"  > strings/0x409/product

C=1
mkdir -p configs/c.$C/strings/0x409
echo 0x80 > configs/c.$C/bmAttributes
echo 500  > configs/c.$C/MaxPower

N="usb0"
mkdir -p functions/hid.$N
echo 0 > functions/hid.$N/protocol
echo 0 > functions/hid.$N/subclass
echo 8 > functions/hid.$N/report_length
echo -ne \\x05\\x01\\x09\\x05\\xa1\\x01\\x15\\x00\\x25\\x01\\x35\\x00\\x45\\x01\\x75\\x01\\x95\\x0e\\x05\\x09\\x19\\x01\\x29\\x0e\\x81\\x02\\x95\\x02\\x81\\x01\\x05\\x01\\x25\\x07\\x46\\x3b\\x01\\x75\\x04\\x95\\x01\\x65\\x14\\x09\\x39\\x81\\x42\\x65\\x00\\x95\\x01\\x81\\x01\\x26\\xff\\x00\\x46\\xff\\x00\\x09\\x30\\x09\\x31\\x09\\x32\\x09\\x35\\x75\\x08\\x95\\x04\\x81\\x02\\x75\\x08\\x95\\x01\\x81\\x01\\xc0 > functions/hid.$N/report_desc

ln -s functions/hid.$N configs/c.$C

ls /sys/class/udc > UDC

chmod 777 /dev/hidg0
ls -l /dev/hidg*
