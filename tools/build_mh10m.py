#!/usr/bin/env python3
"""Build the MH10M files from the commented source programs_rem/MH10M.txt.

One program, MH10M. Its labels are written by name in the source (LBL :SHOW:, XEQ :SHOW:, 1-7 letters and
digits); the build gives each name a free local number 00-99 (listings/MH10M_labels.txt says which is which).
The control flow is written with the C47 STRUCT commands (AN0007), indented, without numbers: the build
checks the structures as the firmware's VALID does and numbers them (IF 01 ...).
The drawing steps are written by the build from python/layout.py (the source keeps only the marker line):
  REM ==== GLYPHS  LBL 00-10: the three AGRAPH words of each digit (0-9, 10 blank), SINT, STO 70-72
  REM ==== WORDS   R80 the decimal point, R81 the thousands mark, R90 / R91 the inside of a key (1 / 2 rows)
  REM ==== STATIC  the title, the LCD frame and the keypad (AGRAPH runs, equal columns joined), the key names
  REM ==== INDOFF  every indicator's text at its place (GRMOD 2 before: their pixels off)
  REM ==== INDON   each indicator drawn with GRMOD 2 - 2 x its bit of R74
Files written:
  programs/MH10M.txt        the program without REM lines, numeric labels (to convert with rejig)
  build/MH10M.txt           the calculator file (the same steps)
  listings/MH10M_doc.txt    numbered steps with the comments and the label names
  listings/MH10M_labels.txt the local labels: name, number, what it does
  build/forum/MH10M.p47u    the same program as a commented rejig source (tools/build_forum.py)
structures(), resolve(), estimate(), source_steps() and labels_text() come from Zones 47
(tools/build_zone47.py, from Elements 47).
  python3 tools/build_mh10m.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import layout as L

NAME = 'MH10M'
NAMED_RE = re.compile(r'(LBL|GTO|XEQ) :([A-Za-z0-9]{1,7}):$')
OPENERS = {'IF': 'ENDIF', 'DO': 'ENDDO', 'REPEAT': 'UNTIL'}
STRUCT = ('IF', 'ELSE', 'ENDIF', 'DO', 'WHILE', 'ENDDO', 'REPEAT', 'UNTIL')
DM42_MAX = 10           # STRUCT_MAX_NUMBER and STRUCT_MAX_NESTING of the original DM42 (R47, DM42n: 255, 63)
NOT_USED = ('FOR', 'NEXT', 'FORₓ', 'NEXTₓ', 'FOR𝑦ˣ', 'FORᵀᴼᴾ')
BAND = 15               # dot rows per band (45 pixel rows, one AGRAPH word)


def is_test(step):
    """A step that leaves a test answer (the firmware's structTest list: the comparisons, the flag and type
    tests ending with ?, the counters, KEY?)."""
    op = step.split(' ')[0]
    return op.endswith('?') or op in ('DSE', 'ISG', 'DSZ', 'ISZ', 'DSL', 'ISE')


def structures(steps):
    """The steps with the partner numbers of the STRUCT commands, as VALID numbers them (manage.c /
    structured.c structWalkProgram): per program, IF, DO and REPEAT in three series from 1, in the order
    the openers appear; ELSE, WHILE, ENDDO, ENDIF, UNTIL take the number of their opener. Stops on what
    VALID refuses (a closer without its opener or of another kind, a structure left open at END or across
    a routine (RTN then LBL), a DO without WHILE, an IF / WHILE / UNTIL without a test just before it) and
    on a test before ELSE, ENDIF, DO, ENDDO, REPEAT or UNTIL: the firmware never skips those (structured.c
    structNoLegacySkip)."""
    out, open_, n = [], [], {}

    def fail(i, msg):
        raise SystemExit('STRUCT, step %d (%s): %s' % (i + 1, steps[i], msg))
    for i, s in enumerate(steps):
        op = s.split(' ')[0]
        prev = steps[i - 1] if i else ''
        if op in NOT_USED:
            fail(i, 'FOR / NEXT not used here (they take the start, end and step off the stack)')
        if op in STRUCT and s != op:
            fail(i, 'written without a number: the build numbers the structures')
        if op in ('IF', 'WHILE', 'UNTIL') and not is_test(prev):
            fail(i, 'no test just before it')
        if op in ('ELSE', 'ENDIF', 'DO', 'ENDDO', 'REPEAT', 'UNTIL') and is_test(prev) and not op == 'UNTIL':
            fail(i, 'a test before it: the firmware never skips a structure step')
        if s == 'END' or (s.startswith('LBL ') and prev == 'RTN'):
            if open_:
                fail(i, 'structure %s %02d still open' % tuple(open_[-1][:2]))
            if s == 'END':
                n = {}
        if op in OPENERS:
            n[op] = n.get(op, 0) + 1
            # the original DM42 (c43 structured.h, OLD_HW): 10 numbers of each kind per program, 10 levels
            if n[op] > DM42_MAX or len(open_) >= DM42_MAX:
                fail(i, 'past the original DM42 limit: %d %s a program, %d levels (structured.h, OLD_HW)'
                     % (DM42_MAX, op, DM42_MAX))
            open_.append([op, n[op], False])
            out.append('%s %02d' % (op, n[op]))
            continue
        if op in STRUCT:
            want = {'ELSE': 'IF', 'ENDIF': 'IF', 'WHILE': 'DO', 'ENDDO': 'DO', 'UNTIL': 'REPEAT'}[op]
            if not open_ or open_[-1][0] != want:
                fail(i, 'no %s open here' % want)
            top = open_[-1]
            if op in ('ELSE', 'WHILE'):
                if top[2]:
                    fail(i, 'a second %s' % op)
                top[2] = True
            if op == 'ENDDO' and not top[2]:
                fail(i, 'a DO without WHILE')
            if op in ('ENDIF', 'ENDDO', 'UNTIL'):
                open_.pop()
            out.append('%s %02d' % (op, top[1]))
            continue
        out.append(s)
    if open_:
        raise SystemExit('STRUCT: %s %02d still open at the end' % tuple(open_[-1][:2]))
    return out


def estimate(steps):
    """Estimated .p47 bytes of a program: 2.3 bytes per command, 2 + its characters per number and
    per binary number, 2 + its UTF-8 bytes per text. Calibrated on Almanac 47's MOON47 (4 836 bytes) and
    NAVFULL (24 160 bytes), within 3 % of both; rejig gives the real size."""
    b = 0.0
    for s in steps:
        if s.startswith('"'):
            b += 2 + len(s.encode('utf-8')) - 2
        elif re.fullmatch(r'-?[\d.]+(E-?\d+)?|[01]+#2', s):
            b += 2 + len(s)
        elif NAMED_RE.match(s):
            b += 3 + len(s.split(':')[1])      # command, 249, length, the name (bytes of the test program)
        else:
            b += 2.3
    return int(round(b))


def resolve(steps):
    """The steps with each named label replaced by a free local number (the fallback file), and the
    numbers: the numbers 00-99 not taken by a numeric label of the first program (the other programs
    have their own local labels), in order. Stops on a name defined twice, a name used but not defined,
    more labels than 00-99."""
    defs = [m.group(2) for s in steps for m in [NAMED_RE.match(s)] if m and m.group(1) == 'LBL']
    dup = sorted({d for d in defs if defs.count(d) > 1})
    if dup:
        raise SystemExit('named labels defined twice: %s' % ', '.join(dup))
    used = {m.group(2) for s in steps for m in [NAMED_RE.match(s)] if m}
    if used - set(defs):
        raise SystemExit('named labels used but not defined: %s' % ', '.join(sorted(used - set(defs))))
    bad = [s for s in steps if re.match(r'(LBL|GTO|XEQ) :', s) and not NAMED_RE.match(s)]
    if bad:
        raise SystemExit('a named label is 1-7 letters or digits between colons: %s' % bad[:3])
    first = steps[:steps.index('END') + 1] if 'END' in steps else steps
    taken = {int(m.group(1)) for s in first for m in [re.fullmatch(r'LBL (\d\d)', s)] if m}
    free = [n for n in range(100) if n not in taken]
    if len(defs) > len(free):
        raise SystemExit('%d named labels, only %d local numbers free' % (len(defs), len(free)))
    num = dict(zip(defs, free))
    return [NAMED_RE.sub(lambda m: '%s %02d' % (m.group(1), num[m.group(2)]), s) for s in steps], num


def programs(steps):
    """The programs of a list of steps (each ends with END)."""
    out, cur = [], []
    for s in steps:
        cur.append(s)
        if s == 'END':
            out.append(cur); cur = []
    return out


def source_steps(lines):
    """The steps of the source lines: no REM, no empty lines, the indentation off."""
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith('REM')]


def glyph_steps():
    out = []
    for d in range(11):
        out.append('LBL %02d' % d)
        for w, r in zip(L.glyph(d), (70, 71, 72)):
            out += [str(w), 'SINT', 'STO %d' % r]
        out.append('RTN')
    return out


def word_steps():
    return [str(L.POINT), 'STO 80', str(L.TICK), 'STO 81', str(L.INSIDE[1]), 'STO 90', str(L.INSIDE[2]), 'STO 91']


BANDS = (1, 65, 129, 193)       # the AGRAPH passes of the frame and the keypad (64 rows each)


def band_runs(px):
    """Per band: the runs (x, n, word) of equal non-zero columns, from the outline pixels px."""
    out = []
    for b in BANDS:
        cols = [sum(1 << (y - b) for y in range(b, b + 64) if (y, x) in px) for x in range(400)]
        runs, x = [], 0
        while x < 400:
            n = 1
            while x + n < 400 and cols[x + n] == cols[x]:
                n += 1
            if cols[x]:
                runs.append((x, n, cols[x]))
            x += n
        out.append((b, runs))
    return out


def text_row(text, top, height, font=21):
    """The ATEXT row that puts the ink of text in the middle of rows top .. top + height - 1."""
    from stdfont import STD, code
    gs = [STD.get(code(ch), STD[0x3f]) for ch in text if ch != ' ']
    lo = min(g[5] for g in gs); hi = max(g[5] + g[4] for g in gs)        # ink rows: line + rb .. line + rb + rg - 1
    return top + (height - (hi + lo)) // 2


def static_steps():
    out = ['10', 'GRFNT']
    for t, x in L.TITLE:
        if x is None:
            x = 394 - L.width(t, 10)
        out += ['"%s"' % t, str(L.TITLE_ROW), str(x), 'ATEXT Z']
    out += ['0', 'GRMOD']
    for b, runs in band_runs(L.outline_pixels()):
        out += [str(b), '0']
        cur = 0
        for x, n, w in runs:
            if x != cur:
                out += ['DROP', str(x)]
            out += [str(w), 'SINT', 'STO 84', 'DROP']
            out += ['XEQ :R16:'] * (n // 16) + ['XEQ :R4:'] * (n % 16 // 4)
            if n % 4 == 1:
                out.append('AGRAPH 84')
            elif n % 4:
                out += [str(n % 4), 'STO 73', 'DROP', 'XEQ :RUN:']
            cur = x + n
    out += ['21', 'GRFNT']
    for k, c, r, h, nm in L.KEYS:
        x0, y0, x1, y1 = L.key_box(c, r, h)
        x = x0 + (L.KW - L.width(nm)) // 2
        out += ['"%s"' % nm, str(text_row(nm, y0, y1 - y0 + 1)), str(x), 'ATEXT Z']
    return out


def ind_steps(on):
    out = []
    for bit, t, x in L.INDICATORS:
        if on:
            out += ['RCL 74', str(bit), '÷', 'IP', '2', 'MOD', '-2', '×', '2', '+', 'GRMOD']
        out += ['"%s"' % t, str(L.IND_ROW), str(x), 'ATEXT Z']
    return out


MARKERS = {'GLYPHS': glyph_steps, 'WORDS': word_steps, 'STATIC': static_steps,
           'INDOFF': lambda: ind_steps(False), 'INDON': lambda: ind_steps(True)}


def expand(lines):
    out = []
    for ln in lines:
        out.append(ln)
        m = re.match(r'\s*REM ==== (\w+)', ln)
        if m and m.group(1) in MARKERS:
            ind = ln[:len(ln) - len(ln.lstrip())]
            out += [ind + s for s in MARKERS[m.group(1)]()]
    return out


def labels_text(lines, num):
    out = [NAME + ' local labels: name (programs_rem/%s.txt), number (build/%s.txt), what it does' % (NAME, NAME), '']
    for i, ln in enumerate(lines):
        m = NAMED_RE.match(ln)
        if m and m.group(1) == 'LBL':
            j = i
            while j > 0 and lines[j - 1].startswith('REM'):
                j -= 1
            note = lines[j][3:].strip(' -') if j < i else ''
            note = re.sub(r'^(LBL )?:%s:\s*' % m.group(2), '', note)
            out.append(':%s:%s %02d  %s' % (m.group(2), ' ' * (8 - len(m.group(2))), num[m.group(2)], note[:90]))
    return '\n'.join(out) + '\n'


def build():
    src = os.path.join(ROOT, 'programs_rem', NAME + '.txt')
    lines = expand([ln.rstrip() for ln in open(src, encoding='utf-8')])
    steps = source_steps(lines)
    numeric, num = resolve(steps)
    numeric = structures(numeric)
    if [s for s in steps if s.startswith('LBL "')] != ['LBL "%s"' % NAME] or steps.count('END') != 1:
        raise SystemExit('one program, %s' % NAME)
    listing, n = [], 0
    for ln in lines:
        if not ln.strip():
            continue
        ind = ln[:len(ln) - len(ln.lstrip())]
        if ln.lstrip().startswith('REM'):
            listing.append('      ' + ind + '; ' + ln.lstrip()[3:].strip())
        else:
            extra = '' if numeric[n] == steps[n] else '    (%s)' % numeric[n].split(' ', 1)[1]
            listing.append('%4d  %s' % (n + 1, ind + steps[n] + extra))
            n += 1
    plain = '\n'.join(numeric) + '\n'
    for d in ('programs', 'build', 'listings'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    for d in ('programs', 'build'):
        with open(os.path.join(ROOT, d, NAME + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write(plain)
    with open(os.path.join(ROOT, 'listings', NAME + '_doc.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(listing) + '\n')
    with open(os.path.join(ROOT, 'listings', NAME + '_labels.txt'), 'w', encoding='utf-8') as fh:
        fh.write(labels_text(lines, num))
    return numeric


if __name__ == '__main__':
    st = build()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_forum
    build_forum.build(NAME)                                   # build/forum/MH10M.p47u, the commented rejig source
    txt = [s for s in st if s.startswith('"')]
    print('%s %5d steps, %2d local labels, longest text %d, about %d bytes (.p47, estimated)' % (
        NAME, len(st), sum(1 for s in st if re.match(r'LBL \d\d', s)), max(len(s) - 2 for s in txt), estimate(st)))
