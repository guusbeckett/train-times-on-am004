#!/usr/bin/env python3

# Copyright (c) 2025 Guus Beckett
# Licensed under the EUPL, Version 1.2 or later;
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# https://joinup.ec.europa.eu/software/page/eupl

import sys
import serial
import time
import re


def calculate_xor_checksum(data_packet):
    """
    Calculates the XOR checksum as required by the manual (Page 4).
    The checksum is the XOR sum of all bytes in the data packet,
    formatted as a two-character uppercase hex string.
    """
    checksum_val = 0
    for byte in data_packet:
        checksum_val ^= byte
    
    # Format as a two-character, zero-padded, uppercase hex string
    checksum_hex = f'{checksum_val:02X}'
    return str(checksum_hex.encode('ascii'))

# --- Configuration ---
# These settings should match your hardware setup.
DEVICE = "/dev/cu.usbserial-0001"
BAUD_RATE = 9600

ser=serial.Serial(
port=DEVICE,
baudrate = BAUD_RATE,
parity=serial.PARITY_NONE,
stopbits=serial.STOPBITS_ONE,
bytesize=serial.EIGHTBITS,
)
checksum = calculate_xor_checksum(sys.argv[1].encode('latin-1', 'replace'))
checksum = re.sub('\'', '', checksum)
checksum = re.sub('b', '', checksum)
counter = '<ID00>' + sys.argv[1] + checksum + '<E>'
print("Checksum: " + checksum)
ser.write(counter.encode('ascii'))
print("Sent: " + counter)
time.sleep(1)