#!/usr/bin/env python
import argparse
import cv2
import numpy
import sif

img = None
color = 0
thick = 1

parser = argparse.ArgumentParser()
parser.add_argument('-i',   action='store_true')
args = parser.parse_args()
if args.i:
    # https://www.jp.square-enix.com/lovelive-sifachm/howtoplay_liveplay.php
    img = cv2.imread('liveplay4.jpg')
    img = cv2.resize(img, (sif.DISP_X, sif.DISP_Y))
    color = (0, 255, 0)
    thick = 2
else:
    img = numpy.full((sif.DISP_Y, sif.DISP_X, 3), 255, dtype=numpy.uint8)

for icon in sif.ICON_DEF:
    cv2.ellipse(img, (icon.x, icon.y), (sif.ICON_RAD, sif.ICON_RAD), 0, 0, 360, color, thick)

cv2.namedWindow('window', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('window', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow('window', img)

cv2.imwrite('{0}.png'.format(sif.ICON_RAD), img)

while True:
    key = cv2.waitKey(0)
    if key == 27: # ESC
        cv2.destroyAllWindows()
        break
