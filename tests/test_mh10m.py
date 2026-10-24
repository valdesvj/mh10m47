#!/usr/bin/env python3
"""tests/test_mh10m.py - MH10M in the C47 simulator (python/c47sim.py).
  1. Worked examples of the Casio (the display after each sequence, written out by hand).
  2. 400 random key sequences against a Python model of the same rules (model() below): after every key the
     display (digits, point, thousands marks), E, M, minus and the key's indicator.
  3. The screen: after every key the digit cells as drawn equal the glyphs of the display (layout.py); only the
     last key is inverted; the start screen again after AC and the same key pressed twice.
  4. The end (x<>y): the user's stack lifted with the display's value in X, LASTx kept, R20-R91 cleared,
     MHTAX and MHMEM kept for the next run.
  python3 tools/build_mh10m.py && python3 tests/test_mh10m.py"""
import os, random, sys
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import mh10msim as S
import layout as L

FAIL = []
E10 = D(10) ** 10


def check(ok, what):
    if not ok:
        FAIL.append(what); print('FAIL', what)


# ---------------------------------------------------------------- the display read from the program
def shown(c):
    """The display as the program keeps it (R50-R69): digits, ' for a thousands mark, . for the point."""
    out = ''
    for k in range(9, -1, -1):
        d = int(c.reg.get(str(50 + k), D(-1)))
        g = int(c.reg.get(str(60 + k), D(-1)))
        out += '' if d == 10 else str(d)
        out += ("'" if g & 2 else '') + ('.' if g & 1 else '')
    return out


def run_keys(keys, **kw):
    """The program for the keys; after each key: (display, indicators R36)."""
    states = []
    c0 = {}

    class Grab(S._Frames):
        def append(self, f):
            super().append(f)
            c = self.c
            states.append((shown(c), int(c.reg.get('36', D(0)))))
    import c47sim
    c = c47sim.load([S.PROG])
    c.s = [D(0)] * 4; c.pix = []; c.keys = list(keys); c.steps = 0; c.clock = D('2461338.0')
    c.frames = Grab(c)
    for k, v in kw.items():
        c.reg[{'tax': 'MHTAX', 'mem': 'MHMEM'}[k]] = D(str(v))
    try:
        c.run('MH10M', maxsteps=10 ** 8)
    except StopIteration:
        pass
    return states, c


# ---------------------------------------------------------------- the model: the Casio's rules in Python
def trunc(v):
    """v cut to the 10 digits of the display (no rounding)."""
    a = abs(v)
    if a == 0:
        return D(0)
    n = len(str(int(a))) if a >= 1 else 1
    p = D(10) ** (10 - n)
    return (int(a * p) / p).copy_sign(v) if v else D(0)


def fmt(v, dec=None, n=None):
    """The display of a value (or of digits n with dec decimals being keyed): digits, marks, point."""
    if n is None:
        v = trunc(v); a = abs(v)
        s = format(a.normalize(), 'f') if a else '0'
        ip, _, fp = s.partition('.')
    else:
        s = str(n).rjust(dec + 1, '0') if dec > 0 else str(n)
        ip, fp = (s[:len(s) - dec], s[len(s) - dec:]) if dec > 0 else (s, '')
    out = ''
    for i, ch in enumerate(ip):
        out += ch
        left = len(ip) - 1 - i
        if left and left % 3 == 0:
            out += "'"
    return out + '.' + fp


IGN = 'ignored'          # a key that does nothing: the program leaves the screen as it was


class Casio:
    OPS = {'+': lambda a, b: a + b, '-': lambda a, b: a - b, '*': lambda a, b: a * b, '/': lambda a, b: a / b}
    PCT = {'+': lambda a, b: a + a * b / 100, '-': lambda a, b: a - a * b / 100, '*': lambda a, b: a * b / 100,
           '/': lambda a, b: a / b * 100}

    def __init__(self, tax=0, mem=0):
        self.rate = D(tax); self.mem = D(mem); self.last = None; self.ac()

    def ac(self):
        self.x = D(0); self.acc = D(0); self.op = None; self.kop = None; self.k = D(0); self.ent = False
        self.err = False; self.mode = False; self.csm = {1: D(0), 2: D(0), 3: D(0)}; self.first = 0
        self.newx = False; self.tax = D(0); self.ind = 0; self.n = 0; self.nd = 0; self.dec = -1; self.neg = False

    def res(self, v):
        if abs(v) >= E10:
            self.err = True
            while abs(v) >= E10:
                v = v / E10
        self.x = trunc(v); self.ent = False; self.newx = False

    def calc(self, op, a, b, table):
        if op == '/' and b == 0:
            self.err = True; return D(0)
        return table[op](a, b)

    def eq1(self):
        if self.op:
            self.res(self.calc(self.op, self.acc, self.x, self.OPS)); self.acc = self.x; self.op = None

    def evalx(self):
        self.x = D(self.n) / D(10) ** max(self.dec, 0) * (-1 if self.neg else 1)

    def key(self, k):
        self.ind = 0
        r = getattr(self, 'k_' + {'+': 'op', '-': 'op', '*': 'op', '/': 'op', '.': 'dot', '±': 'sign', '>': 'bk',
                               '=': 'eq', '%': 'pct', 'TAX+': 'taxp', 'TAX-': 'taxm', 'M+': 'mp', 'M-': 'mp',
                               'COST': 'csm', 'SELL': 'csm', 'MAR': 'csm'}.get(k, 'dig' if k.isdigit() else k))(k)
        self.last = k
        return r

    def k_dig(self, k):
        if self.err:
            return IGN
        if not self.ent:
            self.n = 0; self.nd = 0; self.dec = -1; self.neg = False; self.ent = True; self.newx = True
        if self.nd >= 10:
            return IGN
        self.n = self.n * 10 + int(k)
        if self.dec >= 0:
            self.dec += 1; self.nd += 1
        elif self.n:
            self.nd += 1
        self.evalx()

    def k_dot(self, k):
        if self.err:
            return IGN
        if not self.ent:
            self.n = 0; self.nd = 0; self.dec = -1; self.neg = False; self.ent = True; self.newx = True
        if self.dec >= 0:
            return IGN
        self.dec = 0; self.nd = max(self.nd, 1); self.evalx()

    def k_bk(self, k):
        if self.err or not self.ent:
            return IGN
        if self.dec > 0:
            self.n //= 10; self.dec -= 1; self.nd -= 1
        elif self.dec == 0:
            self.dec = -1
            if self.n == 0:
                self.nd = 0
        else:
            self.n //= 10
            if self.nd:
                self.nd -= 1
        self.evalx()

    def k_sign(self, k):
        if self.err:
            return IGN
        self.x = -self.x; self.neg = not self.neg

    def k_op(self, k):
        if self.err or self.mode:
            return IGN
        if self.newx and self.op:
            self.res(self.calc(self.op, self.acc, self.x, self.OPS)); self.acc = self.x
        if not self.op:
            self.acc = self.x
        self.op = k; self.ent = False; self.newx = False

    def k_eq(self, k):
        if self.mode:
            return self.rset()
        if self.err:
            return IGN
        if self.op:
            self.k = self.acc if self.op == '*' else self.x; self.kop = self.op
            self.res(self.calc(self.op, self.acc, self.x, self.OPS)); self.acc = self.x; self.op = None
        elif self.kop:
            self.res(self.calc(self.kop, self.x, self.k, self.OPS)); self.acc = self.x
        else:
            self.ent = False; self.newx = False

    def k_pct(self, k):
        if self.err or self.mode:
            return IGN
        if self.op:
            self.res(self.calc(self.op, self.acc, self.x, self.PCT)); self.op = None; self.acc = self.x
        else:
            self.res(self.x / 100)

    def k_MRC(self, k):
        if self.err or self.mode:
            return IGN
        if self.last == 'MRC':
            self.mem = D(0); k = None
        else:
            self.x = self.mem; self.ent = False; self.newx = True
        self.last_override = k

    def k_mp(self, k):
        if self.err or self.mode:
            return IGN
        self.eq1()
        if self.err:              # E from the calculation: shown
            return
        m = self.x * (1 if k == 'M+' else -1) + self.mem
        if abs(m) >= E10:
            self.err = True; return
        self.mem = trunc(m); self.ent = False; self.newx = False

    def k_C(self, k):
        if self.err:
            self.err = False; self.op = None; self.ent = False; self.newx = False; self.acc = self.x
        else:
            self.x = D(0); self.ent = False; self.newx = False

    def k_AC(self, k):
        self.ac()

    def k_SET(self, k):
        if self.err:
            return IGN
        if self.mode:
            return self.rset()
        self.mode = True; self.x = self.rate; self.op = None; self.ent = False; self.newx = False

    def rset(self):
        self.rate = abs(self.x); self.x = self.rate; self.mode = False; self.ent = False; self.newx = False
        self.ind = 1024

    def k_taxp(self, k):
        if self.mode:
            return self.rset()
        if self.err:
            return IGN
        if self.last == 'TAX+':
            return self.taxsh()
        self.eq1()
        if self.err:              # E from the calculation: shown
            return
        base = self.x
        self.res(base * self.rate / 100); self.tax = self.x
        self.res(base + self.tax); self.ind = 64

    def k_taxm(self, k):
        if self.err or self.mode:
            return IGN
        if self.last == 'TAX-':
            return self.taxsh()
        self.eq1()
        if self.err:              # E from the calculation: shown
            return
        tot = self.x
        self.res(tot * 100 / (100 + self.rate)); self.tax = tot - self.x; self.ind = 128

    def taxsh(self):
        self.x = self.tax; self.ind = 256; self.ent = False; self.newx = False

    def k_csm(self, k):
        t = {'COST': 1, 'SELL': 2, 'MAR': 3}[k]
        if self.err or self.mode:
            return IGN
        if not self.newx and self.last in ('COST', 'SELL', 'MAR'):
            self.x = self.csm[t]; self.ent = False; self.newx = False
        else:
            self.eq1()
            if self.err:
                return
            self.csm[t] = self.x
            if self.first and self.first != t:
                u = 6 - self.first - t; c, s, m = self.csm[1], self.csm[2], self.csm[3]
                if u == 1:
                    v = s * (100 - m) / 100
                elif u == 2:
                    v = D(0) if m == 100 else c * 100 / (100 - m)
                    self.err = self.err or m == 100
                else:
                    v = D(0) if s == 0 else (s - c) / s * 100
                    self.err = self.err or s == 0
                self.res(v); self.csm[u] = self.x; self.first = 0; t = u
            else:
                self.first = t; self.ent = False; self.newx = False
        self.ind = 4 * t * (t - 1) + 8

    def display(self):
        if self.ent:
            return fmt(None, max(self.dec, 0), self.n)
        return fmt(self.x)

    def indicators(self):
        neg = self.x < 0
        return (self.ind + (1 if self.mem else 0) + (2 if neg else 0) + (4 if self.err else 0)
                + (1536 if self.mode else 0))


def model(keys, tax=0, mem=0):
    m = Casio(tax, mem); out = [(m.display(), m.indicators())]
    for k in keys:
        m.last_override = 'unset'
        r = m.key(k)
        if m.last_override != 'unset':
            m.last = m.last_override
        out.append(out[-1] if r == IGN else (m.display(), m.indicators()))
    return out


def names(text):
    """'12+3=' -> ['1', '2', '+', '3', '=']; names as in mh10msim.press."""
    inv = {v: k for k, v in S.KEY.items()}
    return [inv[c] for c in S.press(text)]


# ---------------------------------------------------------------- 1. worked examples
EXAMPLES = [
    ('', '0.'),
    ('1234567890', "1'234'567'890."),
    ('12345678901', "1'234'567'890."),                # the 11th digit is not taken
    ('0.05', '0.05'), ('1.50', '1.50'), ('1.5+', '1.5'),
    ('1/3=', '0.333333333'), ('1/3=*3=', '0.999999999'),  # the Casio keeps only what it shows
    ('2+3*4=', '20.'),                                  # left to right
    ('3*5=', '15.'), ('3*5==', '45.'), ('3*5=7=', '21.'),  # x: the first number is the constant
    ('10/2=', '5.'), ('10/2==', '2.5'), ('10/2=8=', '4.'),  # /: the second
    ('5+3==', '11.'), ('5-3==', '1.'),             # the minus is an indicator
     ('5*=', '25.'), ('5+=', '10.'),
    ('1500+15%', "1'725."), ('1500-15%', "1'275."), ('200*15%', '30.'), ('30/200%', '15.'),
    ('50%', '0.5'),
    ('5/0=', '0.'), ('99999*99999=', "9'999'800'001."), ('100000*100000=', '1.'),  # E: the result / 10^10
    ('123456*7654321=', '94.49718533'),
    ('123>', '12.'), ('1.25>>', '1.'), ('1.25>>>', '1.'), ('5±', '5.'), ('7±*2=', '14.'),
    ('100M+50M+MRC', '150.'), ('100M+50M-MRC', '50.'), ('100M+MRCMRC', '100.'),
    ('2+3M+MRC', '5.'),
    ('1000COST25MAR', "1'333.333333"), ('1000COST1250SELL', '20.'), ('1250SELL20MAR', "1'000."),
    ('1000COST25MARCOST', "1'000."),
]
for keys, want in EXAMPLES:
    st, c = run_keys(S.press(keys))
    check(st[-1][0] == want, 'example %-22s display %-16s want %s' % (keys, st[-1][0], want))
# with a tax rate, and RATE SET
for keys, tax, want, ind in [('1500TAX+', 8, "1'620.", 64), ('1500TAX+TAX+', 8, '120.', 256),
                             ('1080TAX-', 8, "1'000.", 128), ('1080TAX-TAX-', 8, '80.', 256),
                             ('SET', 8, '8.', 1536), ('SET5SET', 8, '5.', 1024), ('SET5SET200TAX+', 8, '210.', 64),
                             ('SET5=', 8, '5.', 1024)]:
    st, c = run_keys(S.press(keys), tax=tax)
    check(st[-1] == (want, ind), 'tax %-16s %s want %s' % (keys, st[-1], (want, ind)))
st, c = run_keys(S.press('SET5SET'), tax=8)
check(c.reg.get('MHTAX') == D(5), 'RATE SET kept in MHTAX: %s' % c.reg.get('MHTAX'))
# E: only C or AC go on
st, c = run_keys(S.press('100000*100000=12+'))
check(st[-1] == ('1.', 4), 'E locks the keys: %s' % (st[-1],))
st, c = run_keys(S.press('100000*100000=C+1='))
check(st[-1][0] == '2.', 'C after E: the value kept, E off: %s' % (st[-1],))

# ---------------------------------------------------------------- 2. random sequences against the model
rnd = random.Random(47)
POOL = (list('0123456789') * 3 + list('.+-*/=') * 2 + ['±', '>', '%', 'MRC', 'M+', 'M-', 'C', 'AC',
        'COST', 'SELL', 'MAR', 'TAX+', 'TAX-', 'SET'])
bad = 0
for t in range(400):
    seq = [rnd.choice(POOL) for _ in range(rnd.randint(3, 25))]
    tax = rnd.choice([0, 5, 8, 10, 19, 21])
    want = model(seq, tax=tax)
    got, c = run_keys([S.KEY[k] for k in seq], tax=tax)
    if got != want:
        i = next(i for i in range(len(want)) if i >= len(got) or got[i] != want[i])
        bad += 1
        if bad <= 8:
            check(False, 'random %s (tax %s): after %s: program %s model %s'
                  % (' '.join(seq), tax, ' '.join(seq[:i]) or 'the start', got[i] if i < len(got) else None, want[i]))
check(bad == 0, 'random sequences: %d of 400 differ' % bad)

# ---------------------------------------------------------------- 3. the screen
def cells_pixels(disp):
    """The digit area's pixels (x, row from the top) for a display text, from layout.py."""
    digits, marks = [], []
    for ch in disp:
        if ch.isdigit():
            digits.append(int(ch)); marks.append(0)
        elif ch == "'":
            marks[-1] |= 2
        elif ch == '.':
            marks[-1] |= 1
    digits = [10] * (10 - len(digits)) + digits; marks = [0] * (10 - len(marks)) + marks
    px = set()
    for i, (d, g) in enumerate(zip(digits, marks)):
        k = 9 - i
        cols = [L.glyph(d)[0]] * 4 + [L.glyph(d)[1]] * 16 + [L.glyph(d)[2]] * 4
        a = L.POINT if g & 1 else 0; b = a + (L.TICK if g & 2 else 0)
        for x, w in list(zip(range(L.cell_x(k), L.cell_x(k) + 24), cols)) + list(zip(range(L.gap_x(k), L.gap_x(k) + 4), (a, b, b, a))):
            for r in range(64):
                if w >> r & 1:
                    px.add((x, S.H - 1 - (L.BASE + r)))
    return px


def area(pix, x0, x1, r0, r1):
    return {(x, y) for x, y in pix if x0 <= x <= x1 and S.H - 1 - r1 <= y <= S.H - 1 - r0}


seq = '1234.5+67.89=*3=1/3=MRC5±'
shots, c = S.run(S.press(seq))
want = model(names(seq))
for i, (shot, (disp, ind)) in enumerate(zip(shots, want)):
    check(area(shot, 40, 362, L.BASE, L.BASE + 63) == cells_pixels(disp), 'screen %d: the digits are not %s' % (i, disp))
start = shots[0]
keypad = lambda p: area(p, 0, 399, 0, 142)
for i, k in enumerate(S.press(seq)):
    kc = next(kk for kk in L.KEYS if kk[0] == k)
    x0, y0, x1, y1 = L.key_box(*kc[1:4])
    box = {(x, S.H - 1 - y) for x in range(x0 + 1, x0 + 61) for y in range(y0 + 1, y1)}
    check(keypad(shots[i + 1]) == keypad(start) ^ box, 'screen %d: only the key %s inverted' % (i + 1, kc[4]))
shots2, c = S.run(S.press(seq + 'AC'))
check(area(shots2[-1], 0, 399, 144, 239) == area(start, 0, 399, 144, 239), 'AC: the LCD as at the start')
shots3, c = S.run(S.press('5ACAC'))
check(keypad(shots3[-1]) == keypad(shots3[-2]), 'the same key twice: it stays inverted')

# ---------------------------------------------------------------- 4. the end
import c47sim
c = c47sim.load([S.PROG])
c.s = [D(11), D(12), D(13), D(14)]; c.lastx = D(99); c.pix = []; c.frames = []; c.clock = D('2461338.0')
c.keys = S.press('12*3=M+') + [S.OFF]
c.reg['77'] = D(5); c.reg['19'] = D(7)
c.run('MH10M', maxsteps=10 ** 8)
check(c.s == [D(36), D(11), D(12), D(13)], 'the end: the value in X, the stack lifted: %s' % c.s)
check(c.lastx == D(99), 'the end: LASTx kept')
check(all(c.reg.get(str(r), D(0)) == 0 for r in range(20, 92)), 'the end: R20-R91 cleared')
check(c.reg.get('19') == D(7), 'the end: R19 not touched')
check(c.reg.get('MHMEM') == D(36), 'the end: the memory kept in MHMEM')
check(c.pix == [] and c.grmod == 0 and c.grfnt == 20, 'the end: screen cleared, GRMOD 0, GRFNT 20')
st, c = run_keys(S.press('MRC'), mem=36)
check(st[-1] == ('36.', 1), 'the memory from MHMEM at the next run: %s' % (st[-1],))

# ---------------------------------------------------------------- 5. standby (LBL :WAKE:)
def standby(gap):
    """12+ keyed, then a key wait with no key during which the clock moves gap seconds, then 3 = 0FF.
    Returns the simulator (ended or not) and the key codes not used."""
    c = c47sim.load([S.PROG])
    c.s = [D(11), D(12), D(13), D(14)]; c.lastx = D(99); c.pix = []; c.frames = []; c.clock = D('2461338.0')
    script = S.press('12+') + [None] + S.press('3=') + [S.OFF]

    def count(op, x):
        if op == 'KEY?':
            k = script.pop(0) if script else S.OFF
            if k is None:                          # no key: the calculator slept gap seconds in the PAUSE
                c.keys = []; c.keyskip = True; c.clock += D(gap) / D(86400)
            else:
                c.keys = [k]; c.keyskip = False
    c.count = count
    try:
        c.run('MH10M', maxsteps=10 ** 8)
    except StopIteration:
        pass
    return c, script


c, left = standby(600)
check(left == S.press('3=') + [S.OFF], 'standby: the key wait after 10 min ends the program (keys left %s)' % left)
check(c.s == [D(12), D(11), D(12), D(13)] and c.lastx == D(99), 'standby: the stack back, the value in X: %s' % c.s)
check(c.pix == [] and c.grmod == 0, 'standby: the screen cleared')
c, left = standby(5)
check(left == [] and c.s[0] == D(15), 'no standby (5 s): it waits on, 12 + 3 = 15: %s' % c.s)

print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
sys.exit(1 if FAIL else 0)
