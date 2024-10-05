#!/usr/bin/env python
import argparse
import evdev
import logging
import math
import select
import sys

class IconDef:
    def __init__(self, x, y, key):
        self.x      = x
        self.y      = y
        self.key    = key

class KeyMapping:
    def __init__(self, input, output):
        self.input  = input
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

ICON_DEF = [
#   IconDef(  90, 100, evdev.ecodes.KEY_2),      # L2
    IconDef( 135, 310, evdev.ecodes.KEY_1),      # L1
    IconDef( 250, 490, evdev.ecodes.KEY_LEFT),   # ←
    IconDef( 430, 610, evdev.ecodes.KEY_DOWN),   # ↓
    IconDef( 640, 650, evdev.ecodes.KEY_RIGHT),  # →
    IconDef( 850, 610, evdev.ecodes.KEY_X),      # ×
    IconDef(1030, 490, evdev.ecodes.KEY_C),      # ○
    IconDef(1145, 310, evdev.ecodes.KEY_4),      # R1
#   IconDef(1190, 100, evdev.ecodes.KEY_3),      # R2

    IconDef(  90, 100, evdev.ecodes.KEY_UP),     # ↑
    IconDef(1190, 100, evdev.ecodes.KEY_Z),      # □
]

KEY_MAPPING = [
    KeyMapping(evdev.ecodes.KEY_Z,      0x09),  # □ F
    KeyMapping(evdev.ecodes.KEY_X,      0x2C),  # × Space
    KeyMapping(evdev.ecodes.KEY_C,      0x06),  # ○ C
    KeyMapping(evdev.ecodes.KEY_V,      0x15),  # △ R
    KeyMapping(evdev.ecodes.KEY_RIGHT,  0x20),  # → 3
    KeyMapping(evdev.ecodes.KEY_LEFT,   0x1E),  # ← 1
    KeyMapping(evdev.ecodes.KEY_DOWN,   0x1F),  # ↓ 2
    KeyMapping(evdev.ecodes.KEY_UP,     0x3A),  # ↑ F1
    KeyMapping(evdev.ecodes.KEY_1,      0x14),  # L1 Q
    KeyMapping(evdev.ecodes.KEY_4,      0x08),  # R1 E
    KeyMapping(evdev.ecodes.KEY_O,      0x2B),  # OP Tab
    KeyMapping(evdev.ecodes.KEY_P,      0x29),  # PS Esc
]

key_buf     = [0, 0, 0, 0, 0, 0]

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
        try:
            key_buf.index(mapping.output)
            return
        except ValueError:
            try:
                i = key_buf.index(0)
                key_buf[i] = mapping.output
            except ValueError:
                return
    else:
        try:
            i = key_buf.index(mapping.output)
            key_buf[i] = 0
        except ValueError:
            return

    logger.info('{0} {1}'.format(DEV_OUTPUT_KEY, key_buf))

    try:
        with open(DEV_OUTPUT_KEY, 'rb+') as fd:
            fd.write(bytes([0, 0] + key_buf))
    except FileNotFoundError as e:
        logger.debug(e)

if __name__ == '__main__':
    main()
