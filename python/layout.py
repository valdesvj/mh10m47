"""layout.py - the screen of MH10M: the 7-segment digits, the LCD, the keypad, the indicators.
Used by tools/build_mh10m.py (it writes the program's drawing steps from these) and by the tests.
Screen 400 x 240, row 0 = the bottom (as ATEXT and AGRAPH on the C47)."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stdfont import STD, code
from tinyfont import TINY

# ---- the digits ----
BASE = 145              # the row of bit 0 of the AGRAPH words (64 rows, GRMOD 1: written as they are)
OFF = 6                 # the segments start 6 rows up (row 151)
H, T = 48, 4            # segment height of the digit, thickness of a segment
CELL_W, LEFT, MID = 24, 4, 16
CELL_X0, PITCH = 331, 31        # cell k (0 the right) at x 331 - 31k
GAP_X0 = 356                    # its mark at x 356 - 31k (4 columns)


def rows(a, b):
    """The word with bits a..b (rows from the bottom of the segments)."""
    return sum(1 << (OFF + r) for r in range(a, b + 1))


SEG = {'d': rows(0, T - 1), 'g': rows(22, 25), 'a': rows(H - T, H - 1),
       'e': rows(T + 1, 20), 'f': rows(27, H - T - 2), 'c': rows(T + 1, 20), 'b': rows(27, H - T - 2)}
# the Casio's digits (the 6, 7 and 9 with their tails, as on the MH-10M's display)
DIGITS = {0: 'abcdef', 1: 'bc', 2: 'abdeg', 3: 'abcdg', 4: 'bcfg', 5: 'acdfg', 6: 'acdefg', 7: 'abcf',
          8: 'abcdefg', 9: 'abcdfg', 10: ''}
POINT = rows(0, 3)                       # columns 1-4 of the mark
TICK = rows(H - 10, H - 1)               # columns 2-3: the thousands mark, at the top


def glyph(d):
    """The three AGRAPH words of digit d (10: blank): the left columns (e, f), the middle (a, g, d), the right
    (b, c)."""
    s = DIGITS[d]
    left = sum(SEG[x] for x in 'ef' if x in s)
    mid = sum(SEG[x] for x in 'agd' if x in s)
    right = sum(SEG[x] for x in 'bc' if x in s)
    return left, mid, right


def cell_x(k):
    return CELL_X0 - PITCH * k


def gap_x(k):
    return GAP_X0 - PITCH * k


# ---- the LCD and the title ----
LCD = (4, 395, 144, 231)        # x0, x1, row0, row1 of the frame
IND_ROW = 210                   # the indicators (GRFNT 21, the glyph box 20 rows)
TITLE_ROW = 232                 # the title (GRFNT 10)
TITLE = [('DESK CALCULATOR', 6), ('10 DIGITS', None)]   # a plain title: no maker's name on the screen

# ---- the indicators: bit, text, x ----
# each at its own place: an indicator that is off clears its own pixels (GRMOD 2), so none may overlap
INDICATORS = [(1, 'M', 8), (2, '-', 24), (4, 'E', 38), (8, 'COST', 62), (16, 'SELL', 104), (32, 'MAR', 144),
              (64, 'TAX+', 180), (128, 'TAX-', 222), (256, 'TAX', 262), (1024, 'RATE', 296), (512, 'SET', 338)]

# ---- the keypad (the Casio's: 6 columns, 5 rows; the + key two rows high) ----
KX0, KDX, KW = 3, 66, 62        # key column c at x 3 + 66c, 62 wide
KY0, KDY, KH = 1, 29, 25        # key row r at row 1 + 29r, 25 high (two rows: 54)
# (C47 KEY? code, column, row, rows high, the name on the key)
KEYS = [(11, 0, 4, 1, 'COST'), (12, 1, 4, 1, 'SELL'), (13, 2, 4, 1, 'MAR'), (14, 3, 4, 1, '%'),
        (15, 4, 4, 1, 'TAX-'), (16, 5, 4, 1, 'TAX+'),
        (43, 0, 3, 1, '+/-'), (52, 1, 3, 1, '7'), (53, 2, 3, 1, '8'), (54, 3, 3, 1, '9'), (65, 4, 3, 1, '×'),
        (55, 5, 3, 1, '÷'),
        (45, 0, 2, 1, '▶'), (62, 1, 2, 1, '4'), (63, 2, 2, 1, '5'), (64, 3, 2, 1, '6'), (75, 4, 2, 1, '-'),
        (21, 5, 2, 1, 'MRC'),
        (24, 0, 1, 1, 'C'), (72, 1, 1, 1, '1'), (73, 2, 1, 1, '2'), (74, 3, 1, 1, '3'), (85, 4, 0, 2, '+'),
        (22, 5, 1, 1, 'M-'),
        (25, 0, 0, 1, 'AC'), (82, 1, 0, 1, '0'), (83, 2, 0, 1, '.'), (41, 3, 0, 1, '='), (23, 5, 0, 1, 'M+')]
INSIDE = {1: (1 << 23) - 1, 2: (1 << 52) - 1}     # the inside of a key, from its row + 1 (R90, R91)


def key_box(c, r, h):
    """x0, row0, x1, row1 of a key's outline."""
    x0 = KX0 + KDX * c; y0 = KY0 + KDY * r
    return x0, y0, x0 + KW - 1, y0 + KDY * (h - 1) + KH - 1


def width(text, font=21):
    """The width of a text in ATEXT (GRFNT 21: one column less per character; 10: the tinyFont)."""
    f = TINY if font == 10 else STD
    cp = 1 if font == 21 else 0
    w = 0
    for ch in text:
        g = f.get(code(ch), f[0x3f])
        w += g[0] + g[1] + g[2] - cp
    return w


def outline_pixels():
    """The pixels (row, x) of the keypad and the LCD frame: what the build's AGRAPH runs must draw."""
    px = set()
    for k, c, r, h, nm in KEYS:
        x0, y0, x1, y1 = key_box(c, r, h)
        for x in range(x0 + 1, x1):
            px.add((y0, x)); px.add((y1, x))
        for y in range(y0 + 1, y1):
            px.add((y, x0)); px.add((y, x1))
    x0, x1, y0, y1 = LCD
    for x in range(x0, x1 + 1):
        px.add((y0, x)); px.add((y1, x))
    for y in range(y0, y1 + 1):
        px.add((y, x0)); px.add((y, x1))
    return px
