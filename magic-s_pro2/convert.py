#!/usr/bin/env python
import argparse
import evdev
import logging
import math
import select
import sys
from struct import pack

class IconDef:
    def __init__(self, x, y, key):
        self.x      = x
        self.y      = y
        self.key    = key

class KeyMapping:
    def __init__(self, input, id, output):
        self.input  = input
        self.id     = id
        self.output = output

class TouchInfo:
    def __init__(self, id, x, y, key):
        self.id     = id
        self.x      = x
        self.y      = y
        self.key    = key

DEV_INPUT_KEY       = '/dev/input/event0'
DEV_INPUT_TOUCH     = '/dev/input/event8'
DEV_OUTPUT_KEY      = '/dev/hidg0'

DISP_X      = 1280
DISP_Y      = 720

ABS_X_MIN   = 0
ABS_X_MAX   = 4096
ABS_Y_MIN   = 0
ABS_Y_MAX   = 4096
ABS_SLOT    = 10

KEY_DOWN    = 1
KEY_UP      = 0

ICON_RAD    = 75

DIR_CENTER  = 0xF

ICON_DEF = [
    IconDef(  90, 100, evdev.ecodes.KEY_2),     # L2
    IconDef( 135, 310, evdev.ecodes.KEY_1),     # L1
    IconDef( 250, 490, evdev.ecodes.KEY_LEFT),  # ←
    IconDef( 430, 610, evdev.ecodes.KEY_DOWN),  # ↓
    IconDef( 640, 650, evdev.ecodes.KEY_Z),     # □
    IconDef( 850, 610, evdev.ecodes.KEY_X),     # ×
    IconDef(1030, 490, evdev.ecodes.KEY_C),     # ○
    IconDef(1145, 310, evdev.ecodes.KEY_4),     # R1
    IconDef(1190, 100, evdev.ecodes.KEY_3),     # R2
]

KEY_MAPPING = [
    KeyMapping(evdev.ecodes.KEY_Z,      0,  0), # □
    KeyMapping(evdev.ecodes.KEY_X,      0,  1), # ×
    KeyMapping(evdev.ecodes.KEY_C,      0,  2), # ○
    KeyMapping(evdev.ecodes.KEY_V,      0,  3), # △
    KeyMapping(evdev.ecodes.KEY_RIGHT,  1,  1), # →
    KeyMapping(evdev.ecodes.KEY_LEFT,   1,  3), # ←
    KeyMapping(evdev.ecodes.KEY_DOWN,   1,  2), # ↓
    KeyMapping(evdev.ecodes.KEY_UP,     1,  0), # ↑
    KeyMapping(evdev.ecodes.KEY_1,      0,  4), # L1
    KeyMapping(evdev.ecodes.KEY_2,      0,  6), # L2
    KeyMapping(evdev.ecodes.KEY_3,      0,  7), # R2
    KeyMapping(evdev.ecodes.KEY_4,      0,  5), # R1
    KeyMapping(evdev.ecodes.KEY_O,      0,  9), # Option
    KeyMapping(evdev.ecodes.KEY_P,      0, 12), # PS
    KeyMapping(evdev.ecodes.KEY_S,      0,  8), # Share
]

DIR_MAPPING = [DIR_CENTER] * 16
DIR_MAPPING[1]  = 0 # ↑
DIR_MAPPING[3]  = 1 # ↑→
DIR_MAPPING[2]  = 2 # →
DIR_MAPPING[6]  = 3 # →↓
DIR_MAPPING[4]  = 4 # ↓
DIR_MAPPING[12] = 5 # ↓←
DIR_MAPPING[8]  = 6 # ←
DIR_MAPPING[9]  = 7 # ←↑

key_buf = [0, 0]
w_fd = open(DEV_OUTPUT_KEY, 'wb+')

def main():
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))

    parser = argparse.ArgumentParser()
    parser.add_argument('-v',   action='store_true')
    parser.add_argument('-vv',  action='store_true')
    args = parser.parse_args()
    if args.vv:
        logger.setLevel(logging.DEBUG)
    elif args.v:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.CRITICAL)

    devices = map(evdev.InputDevice, (DEV_INPUT_KEY, DEV_INPUT_TOUCH))
    devices = { dev.fd: dev for dev in devices }

    touch = []
    for i in range(ABS_SLOT):
        touch.append(TouchInfo(-1, -1, -1, -1))

    i = 0

    while True:
        r, w, x = select.select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                logger.debug(event)

                if event.type == evdev.ecodes.EV_ABS:
                    if event.code == evdev.ecodes.ABS_MT_SLOT:
                        i = event.value

                    elif event.code == evdev.ecodes.ABS_MT_POSITION_X:
                        if touch[i].x == -1 and touch[i].y != -1:
                            touch[i].key = check_touch(event.value, touch[i].y)
                            if touch[i].key > 0:
                                write_dev(touch[i].key, KEY_DOWN)

                        touch[i].x = event.value

                    elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                        if touch[i].x != -1 and touch[i].y == -1:
                            touch[i].key = check_touch(touch[i].x, event.value)
                            if touch[i].key > 0:
                                write_dev(touch[i].key, KEY_DOWN)

                        touch[i].y = event.value

                    elif event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                        if event.value == -1:
                            write_dev(touch[i].key, KEY_UP)
                            touch[i].x   = -1
                            touch[i].y   = -1
                            touch[i].key = -1

                        touch[i].id = event.value

                elif event.type == evdev.ecodes.EV_KEY:
                    write_dev(event.code, event.value)

def check_touch(abs_x, abs_y):
    x = (abs_x / (ABS_X_MAX - ABS_X_MIN)) * DISP_X
    y = (abs_y / (ABS_Y_MAX - ABS_Y_MIN)) * DISP_Y

    for icon in ICON_DEF:
        dist = math.sqrt(math.pow(abs(icon.x - x), 2) + math.pow(abs(icon.y - y), 2))
        if dist < ICON_RAD:
            return icon.key

    return -1

def write_dev(key, value):
    mapping = next((x for x in KEY_MAPPING if x.input == key), None)
    if mapping == None:
        return

    logger = logging.getLogger(__name__)

    if value == KEY_DOWN:
        key_buf[mapping.id] |=  (1<<mapping.output)
    else:
        key_buf[mapping.id] &= ~(1<<mapping.output)

    logger.info('{0} {1}'.format(DEV_OUTPUT_KEY, key_buf))

    try:
        w_fd.write(pack('<HBBBBBB', key_buf[0], DIR_MAPPING[key_buf[1]], 128, 128, 128, 128, 0))
        w_fd.flush()
    except FileNotFoundError as e:
        logger.debug(e)

if __name__ == '__main__':
    main()
