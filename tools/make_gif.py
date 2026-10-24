#!/usr/bin/env python3
"""Write docs/MH10M_tour.gif: MH10M in the C47 simulator, a short session key by key (the key pressed shown
inverted on the Casio's keypad): 1234.5 + 67.89 = (1'302.39), x 3 = (3'907.17), M+; with the tax rate 8 %:
1500 TAX+ (1'620.) TAX+ (the tax, 120.); 1000 COST 25 MAR (the selling price 1'333.333333); 1 / 3 =, x 3 =
(0.999999999, as the Casio); MRC (the memory, 3'907.17). 0.7 s a key, 1.8 s on the results.
Needs Pillow (pip install pillow).
  python3 tools/build_mh10m.py && python3 tools/make_gif.py"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import mh10msim as S
from PIL import Image

SCALE, BORDER = 2, 8
SESSION = ['1234.5+67.89=', '*3=', 'M+', 'AC', '1500TAX+', 'TAX+', 'AC', '1000COST', '25MAR', 'AC',
           '1/3=', '*3=', 'MRC']


def image(pix):
    w, h = S.W * SCALE + 2 * BORDER, S.H * SCALE + 2 * BORDER
    im = Image.new('P', (w, h), 0)
    im.putpalette(list(S.LCD_BG) + list(S.LCD_ON) + [0] * 762)
    px = im.load()
    for x, r in pix:
        for dy in range(SCALE):
            for dx in range(SCALE):
                px[BORDER + x * SCALE + dx, BORDER + r * SCALE + dy] = 1
    return im


def main():
    keys, ends = [], []
    for part in SESSION:
        keys += S.press(part); ends.append(len(keys))
    shots, c = S.run(keys, tax=8)
    ims = [image(s) for s in shots]
    dur = [1500] + [1800 if i in ends else 700 for i in range(1, len(ims))]
    fn = os.path.join(ROOT, 'docs', 'MH10M_tour.gif')
    ims[0].save(fn, save_all=True, append_images=ims[1:], duration=dur, loop=0, optimize=True)
    print('%s: %d frames, %d bytes' % (os.path.relpath(fn, ROOT), len(ims), os.path.getsize(fn)))


if __name__ == '__main__':
    main()
