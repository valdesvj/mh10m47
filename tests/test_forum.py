#!/usr/bin/env python3
"""tests/test_forum.py - build/forum/MH10M.p47u: its steps (the comments after ';' and the '@'
header taken away, the indentation too) are exactly those of build/MH10M.txt, so rejig gives
the same .p47; no line starts with ';' or '#' (rejig would make it a REM step); a header with Index, Author,
Version and Source; most code steps of the program part commented.
  python3 tools/build_mh10m47.py && python3 tests/test_forum.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = []


def check(ok, what):
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', what))
    if not ok:
        FAIL.append(what)


for name in ('MH10M',):
    print('==', name)
    lines = open(os.path.join(ROOT, 'build', 'forum', name + '.p47u'), encoding='utf-8').read().split('\n')
    plain = [s for s in open(os.path.join(ROOT, 'build', name + '.txt'), encoding='utf-8').read().split('\n') if s.strip()]
    head = [ln for ln in lines if ln.startswith('@')]
    body = [ln for ln in lines if ln.strip() and not ln.startswith('@')]
    check(all(not ln.lstrip().startswith((';', '#')) for ln in body), 'no line starts with ; or # (no REM steps)')
    steps = [ln.split(';', 1)[0].strip() for ln in body]
    check(steps == plain, 'the steps are those of build/%s.txt (%d)' % (name, len(plain)))
    for f in ('Index', 'Author', 'Version', 'Source'):
        check(any(re.match(r'@ %s: +\S' % f, h) for h in head), '@ %s:' % f)
    check(lines.index(body[0]) > lines.index(head[-1]), 'the header first, then the steps')
    com = sum(1 for ln in body if ';' in ln)
    check(com > len(body) // 10, '%d steps with a comment' % com)
print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
sys.exit(1 if FAIL else 0)
