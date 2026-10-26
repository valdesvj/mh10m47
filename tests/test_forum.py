#!/usr/bin/env python3
"""tests/test_forum.py - build/forum/*.p47u (the files for the forum and the C47's PROGRAMS folder): their steps
(the '@' lines, the comments after ';' and the indentation taken away) are exactly those of build/NAME.txt, so rejig
gives the same .p47; no line starts with ';' or '#' (rejig would make it a REM step); the header: Index, Author,
Version, Source, then the narrative of tools/forum/NAME.txt (what it does, how to use it, what it changes, the
programs and labels) before the first step; the source's comments as '@' lines among the steps.
  python3 tools/build_mh10m.py && python3 tests/test_forum.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ('MH10M',)
FAIL = []


def check(ok, what):
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', what))
    if not ok:
        FAIL.append(what)


for name in NAMES:
    print('==', name)
    lines = open(os.path.join(ROOT, 'build', 'forum', name + '.p47u'), encoding='utf-8').read().split('\n')
    plain = [s for s in open(os.path.join(ROOT, 'build', name + '.txt'), encoding='utf-8').read().split('\n') if s.strip()]
    body = [ln for ln in lines if ln.strip() and not ln.startswith('@')]
    first = lines.index(body[0])
    head = [ln for ln in lines[:first] if ln.startswith('@')]
    check(all(not ln.lstrip().startswith((';', '#')) for ln in body), 'no line starts with ; or # (no REM steps)')
    check(all(ln.startswith('@') or not ln.lstrip().startswith('@') for ln in lines), "the '@' lines start in column 1")
    steps = [ln.split(';', 1)[0].strip() for ln in body]
    check(steps == plain, 'the steps are those of build/%s.txt (%d)' % (name, len(plain)))
    for f in ('Index', 'Author', 'Version', 'Source'):
        check(any(re.match(r'@ %s: +\S' % f, h) for h in head), '@ %s:' % f)
    for part in ('What it is', 'How to use it', 'What it changes on your calculator', 'Programs and labels'):
        check(any(h.startswith('@ ---- %s ----' % part) for h in head), 'the narrative before the steps: %s' % part)
    inside = sum(1 for ln in lines[first:] if ln.startswith('@ '))
    check(inside > len(body) // 50, "%d comment lines ('@') among the %d steps" % (inside, len(body)))
print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
sys.exit(1 if FAIL else 0)
