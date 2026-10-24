#!/usr/bin/env python3
"""build_forum.py - the commented rejig source (.p47u) of MH10M, for the forum and the PROGRAMS folder of a C47
release (as Logic 47's, Almanac 47's and Zones 47's tools/build_forum.py: '@' header lines, then the steps).

  build/forum/MH10M.p47u  from build/MH10M.txt (the steps) and listings/MH10M_doc.txt (the comments)

The steps are those of build/*.txt, one by one (the same .p47 as the plain listing): indented as the source
(STRUCT, two spaces a level), the partner numbers written (DO 01 ... ENDDO 01). The comments of the source
(its REM lines) go after ';' at the end of the steps they stand before, one comment line a step, in a column;
the name of a label (LBL :INIT:) is given as a comment on its LBL and on each XEQ / GTO to it. rejig drops
everything after ';', so the comments take no memory. A line that starts with ';' or '#' would become a REM
step on the calculator (Almanac 47 DEVELOPMENT_NOTES): there are none; the source's header is in '@' lines.

  python3 tools/build_mh10m47.py   (writes it too)
  rejig: the .p47 of build/forum/MH10M.p47u must be the size of the one of build/MH10M.txt.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'forum')
AUTHOR = 'Victor Valdes'
SOURCE = 'https://github.com/valdesvj/mh10m47'
COL = 32                              # the column of the ';' comments (wider steps: two spaces after them)

HEAD = {
    'MH10M': """@ Index:   Casio MH-10M desk calculator: 10 digits, COST SELL MAR, TAX+ TAX-, memory, its keypad on the screen
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): tests/test_mh10m.py, Casio examples worked by hand and 400 random
@ Tested:  key sequences against a separate Python model of the Casio's rules; every screen against the glyphs
@ Tested:  not yet on a C47 (the KEY? codes of ENTER, x<>y, +/-, <-, the operators and the second row to check)
@ Input:   the Casio's keys on the C47: 0-9 . + - x / as they are, ENTER =, +/- +/-, <- the Casio's >,
@ Input:   F1-F6 COST SELL MAR %% TAX- TAX+, the second row MRC M- M+ C AC RATE-SET, x<>y the end
@ Output:  1 / 3 = shows 0.333333333; x 3 = 0.999999999 (as the Casio); 1500 TAX+ at 8 %% shows 1'620.,
@ Output:  TAX+ again 120.; 1000 COST 25 MAR shows SELL 1'333.333333; at the end the value in X
@
@ MH-10M 47: the Casio MH-10M on the C47 / R47. Its 10-digit LCD (7-segment digits drawn with AGRAPH, the
@ point, the thousands marks, the indicators M - E COST SELL MAR TAX+ TAX- TAX RATE SET) and its keypad drawn
@ on the screen; the key pressed is shown inverted until the next one. Algebraic, left to right, results cut
@ to the 10 digits shown; the constant of =; the Casio's %%; MRC (twice clears), M+, M-; cost / selling price /
@ margin (two give the third); tax with a rate set with RATE SET; E on overflow or / 0 (C or AC go on).
@ The tax rate and the memory are kept between runs in the variables MHTAX and MHMEM.
@ Your stack and LASTx are kept (STOS / RCLS in local registers); the value shown is put in X at the end
@ (the stack lifted); the registers R20-R91 are cleared at the end.
@ Needs a C47 / R47 firmware with ATEXT, GRFNT and the STRUCT commands (WSIZE 64).
@ The comments after ';' say what each part does (rejig drops them: they take no memory).
@
""",
}

STEP = re.compile(r'^\s*(\d+)  (.*)$')
NAMED = re.compile(r'^(\s*)(.*?)\s{4}\((\d+)\)$')            # "XEQ :INIT:    (83)", "DO    (01)"


def parse(name):
    """The doc listing: the header comments, then [(indent, step text with names, number, comments before it)]."""
    head, steps, pending = [], [], []
    for ln in open(os.path.join(ROOT, 'listings', name + '_doc.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = STEP.match(ln)
        if m:
            body = m.group(2)
            ind = body[:len(body) - len(body.lstrip())]
            steps.append((ind, body.strip(), int(m.group(1)), pending)); pending = []
        elif ln.strip().startswith(';'):
            text = ln.strip()[1:].strip()
            (pending if steps else head).append(text)          # before step 1: the program's header
    return head, steps


DIGIT_KEYS = {52: 7, 53: 8, 54: 9, 62: 4, 63: 5, 64: 6, 72: 1, 73: 2, 74: 3, 82: 0}
KEYS = {11: 'COST (F1)', 12: 'SELL (F2)', 13: 'MAR (F3)', 14: '%% (F4)', 15: 'TAX- (F5)', 16: 'TAX+ (F6)',
        21: 'MRC (2nd row 1)', 22: 'M- (2nd row 2)', 23: 'M+ (2nd row 3)', 24: 'C (2nd row 4)', 25: 'AC (2nd row 5)',
        26: 'RATE SET (2nd row 6)', 41: '= (ENTER)', 43: '+/- (+/-)', 45: "the Casio's > (<-: the last digit off)",
        55: '/ (the C47 /)', 65: 'x (the C47 x)', 75: '- (the C47 -)', 83: '. (the C47 .)', 85: '+ (the C47 +)'}
OPS = {86: '+: a + b', 87: '-: a - b', 88: 'x: a x b', 89: '/: a / b (b = 0: E)', 90: '+ %: a + ab/100',
       91: '- %: a - ab/100', 92: 'x %: ab/100', 93: '/ %: 100a/b (b = 0: E)', 94: 'the cost: s (100 - m) / 100',
       95: 'the selling price: 100c / (100 - m)', 96: 'the margin: 100 (s - c) / s'}


def data_notes(name, plain, names):
    """Notes on the numeric labels (no REM of their own): {step index: note}. LBL 00-10 the glyphs, LBL 11-85
    the keys at their KEY? codes, LBL 86-96 the operations."""
    notes = {}
    for k, st in enumerate(plain):
        m = re.fullmatch(r'LBL (\d\d)', st)
        if m and m.group(1) not in names:
            lab = int(m.group(1))
            if lab <= 10:
                notes[k] = 'glyph of %s: the words of its left, middle, right columns' % ('a blank cell' if lab == 10 else 'the digit %d' % lab)
            elif lab in DIGIT_KEYS:
                notes[k] = 'key %d (KEY? %d): its Casio key inverted, then the digit' % (DIGIT_KEYS[lab], lab)
            elif lab in KEYS:
                notes[k] = 'KEY? %d: %s' % (lab, KEYS[lab].replace('%%', '%'))
            elif lab in OPS:
                notes[k] = 'operation %d: %s (R75 a, R76 b; R39-R41 c s m)' % (lab, OPS[lab])
    return notes


def build(name):
    head, steps = parse(name)
    plain = open(os.path.join(ROOT, 'build', name + '.txt'), encoding='utf-8').read().split('\n')
    plain = [s for s in plain if s.strip()]
    if len(plain) != len(steps):
        raise SystemExit('%s: %d steps in build/, %d in listings/' % (name, len(plain), len(steps)))
    m = re.search(r'v(\d+\.\d+\.\d+)', head[0])
    version = m.group(1) if m else '?'
    names = {}                                                    # label number -> :NAME:
    for ind, text, n, com in steps:
        mm = NAMED.match(ind + text)
        if mm and mm.group(2).startswith('LBL :'):
            names[mm.group(3)] = mm.group(2)[4:]
    out = [(HEAD[name] % dict(author=AUTHOR, version=version, source=SOURCE)).rstrip('\n')]
    data = data_notes(name, plain, names)
    out += ['@ ' + h if h else '@' for h in head] + ['@', '']
    queue, last = [], None
    for k, ((ind, text, n, com), step) in enumerate(zip(steps, plain)):
        if ';' in step or step.lstrip().startswith(('#', '@')):
            raise SystemExit('%s step %d: %r would not survive rejig' % (name, n, step))
        if com:
            if queue and last is not None:                       # the rest of the last block: on its last step
                out[last] += ' ' + ' '.join(queue)
            queue = list(com)
        note = ''
        mm = re.fullmatch(r'(LBL|XEQ|GTO) (\d\d)', step)
        if mm and mm.group(2) in names:
            note = names[mm.group(2)] if mm.group(1) == 'LBL' else '-> ' + names[mm.group(2)]
        if k in data:
            note = (note + '  ' if note else '') + data[k]
        c = queue.pop(0) if queue else ''
        if note and c:
            c = note + '  ' + c
        elif note:
            c = note
        line = ind + step
        if c:
            line = line.ljust(COL) + '; ' + c if len(line) < COL else line + '  ; ' + c
        out.append(line)
        if c:
            last = len(out) - 1
    if queue and last is not None:
        out[last] += ' ' + ' '.join(queue)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, name + '.p47u')
    with open(fn, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out).rstrip('\n') + '\n')
    ncom = sum(1 for ln in out if re.search(r'\s; ', ln))
    print('build/forum/%s.p47u  %d steps, %d with a comment, version %s' % (name, len(plain), ncom, version))
    return out


if __name__ == '__main__':
    for nm in sys.argv[1:] or ('MH10M',):
        build(nm)
