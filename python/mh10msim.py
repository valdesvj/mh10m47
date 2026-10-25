"""mh10msim.py - run build/MH10M.txt in the C47 simulator (c47sim.py, from Almanac 47) and turn its screens
into pictures.
  run(keys, tax, mem)      the screens shown while MH10M waits for a key and the simulator (registers, texts)
  press(text)              key codes from a text of Casio keys: '12+3=' or with names: 'COST', 'MRC' ...
  png(fn, pix)             a PNG of one screen (LCD colours, 3 pixels per C47 pixel)
  python3 python/mh10msim.py   writes the screens in docs/ and prints the step counts"""
import os, re, struct, sys, zlib
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c47sim

PROG = os.environ.get('MH10M_PROG') or os.path.join(ROOT, 'build', 'MH10M.txt')
W, H = 400, 240
LCD_BG, LCD_ON = (199, 205, 186), (34, 38, 30)
OFF = 42                                    # x<>y: the end
# the Casio's keys -> the C47's KEY? codes
KEY = {'7': 52, '8': 53, '9': 54, '4': 62, '5': 63, '6': 64, '1': 72, '2': 73, '3': 74, '0': 82, '.': 83,
       '+': 85, '-': 75, '*': 65, '/': 55, '=': 41, '±': 43, '>': 45,
       'COST': 11, 'SELL': 12, 'MAR': 13, '%': 14, 'TAX-': 15, 'TAX+': 16,
       'MRC': 21, 'M-': 22, 'M+': 23, 'C': 24, 'AC': 25, 'SET': 26, 'OFF': OFF}
NAMES = sorted((k for k in KEY if len(k) > 1), key=len, reverse=True)


def press(text):
    """Key codes from a text: names (COST, TAX+, MRC, M+, AC, SET ...) or single keys, spaces ignored."""
    out, i = [], 0
    while i < len(text):
        if text[i] == ' ':
            i += 1; continue
        nm = next((n for n in NAMES if text.startswith(n, i)), text[i])
        out.append(KEY[nm]); i += len(nm)
    return out


class _Frames(list):
    def __init__(self, c): super().__init__(); self.c = c; c.at_steps = []
    def append(self, f): self.c.at_steps.append(self.c.steps); super().append(f)


def run(keys, tax=None, mem=None, stack=None, prog=PROG):
    """MH10M for the key codes keys (the last OFF ends it, else it stops at the next key wait). The screens
    (sets of (x, row), row 0 = top) and the simulator (c.at_steps: the steps before each screen)."""
    c = c47sim.load([prog])
    c.s = [D(v) for v in (stack or [0, 0, 0, 0])]; c.pix = []; c.keys = list(keys); c.steps = 0
    c.frames = _Frames(c)
    if tax is not None:
        c.reg['MHTAX'] = D(str(tax))
    if mem is not None:
        c.reg['MHMEM'] = D(str(mem))
    try:
        c.run('MH10M', maxsteps=10 ** 8)
        c.ended = True
    except StopIteration:
        c.ended = False
    shots = [{(x, H - 1 - y) for y, x in f if 0 <= y < H and 0 <= x < W} for f in c.frames]
    return shots, c


def png(fn, pix, scale=3, border=12):
    w, h = W * scale + 2 * border, H * scale + 2 * border
    buf = bytearray(bytes(LCD_BG) * (w * h))
    dot = bytes(LCD_ON) * scale
    for x, r in pix:
        for dy in range(scale):
            o = ((border + r * scale + dy) * w + border + x * scale) * 3
            buf[o:o + len(dot)] = dot
    raw = b''.join(b'\x00' + bytes(buf[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(fn, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                 + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    for fn, keys, kw, what in (
            ('MH10M_start.png', '', {}, 'the start'),
            ('MH10M_1234567890.png', '1234567890', {}, '1234567890 keyed'),
            ('MH10M_third.png', '1/3=', {}, '1 / 3 ='),
            ('MH10M_tax.png', '1500TAX+', {'tax': 8}, '1500 TAX+ at 8 %'),
            ('MH10M_cost.png', '1000COST25MAR', {}, 'cost 1000, margin 25 %: the selling price'),
            ('MH10M_error.png', '99999999*99999999=', {}, 'overflow: E')):
        shots, c = run(press(keys), **kw)
        png(os.path.join(ROOT, 'docs', fn), shots[-1])
        print('docs/%-24s %-45s %6d steps' % (fn, what, c.at_steps[-1] - (c.at_steps[-2] if len(c.at_steps) > 1 else 0)))
    shots, c = run([])
    print('start: %d steps' % c.at_steps[0])
