# MH-10M 47: development notes

## Oct 24, 2026 - v0.1.0, the first version

- Idea (Victor): an emulator of the Casio MH-10M (a 10-digit desk calculator with COST / SELL / MAR and
  TAX+ / TAX-) on the C47, built like Zones 47; then (Victor): the Casio's keypad on the screen, the key
  pressed shown highlighted.
- Screen (python/layout.py): the LCD at the top (frame rows 144-231), the keypad under it (6 x 5 keys of
  62 x 25, the + key two rows high, the Casio's layout), the title in the tinyFont above the LCD.
- Digits: 7 segments, 48 rows high, 4 thick, 24 wide; the 6, 7 and 9 with their tails as on the MH-10M.
  A digit is three AGRAPH words (the left columns e f, the middle a g d, the right b c), written in GRMOD 1
  (the 64 rows as they are), so a cell needs no clearing. The mark after a cell: the point (4 x 4) and the
  thousands mark (2 x 10, at the top), 4 columns. LBL 00-10 push the words (the build writes them).
- Only what changes is drawn: the digit and the mark shown in each cell are kept (R50-R69); the cells looked
  at are those with a digit now or last time (R49), so a short number does not walk all ten.
- The key pressed: its inside inverted (GRMOD 3, XOR), 60 columns of 23 ones (52 for +); the key before is
  inverted again first, so one key is shown at a time, until the next key. The keys are drawn once at the
  start by the build's AGRAPH runs (the outline pixels in 4 bands of 64 rows, equal columns joined).
- Indicators: each at its own place in GRFNT 21 above the digits: all cleared with GRMOD 2 (their pixels
  off), then each drawn with GRMOD 2 - 2 x its bit (an indicator that is off clears only its own pixels: they
  may not overlap; a first try with TAX+, TAX- and TAX at one place showed the one on spoiled by the others).
- Keys: XEQ IND 33 to the label of the KEY? code, when "/k/" is in the list R85 (αPOS); x<>y ends. The
  Casio's top row on F1-F6, its MRC M- M+ C AC RATE-SET on the C47's second row, ENTER =, <- the Casio's >.
  KEY? codes checked on a C47 before: F1-F6 11-16 (Logic 47), the digits, + 85 (Almanac 47); the rest from the
  same row/column pattern: to check (README).
- The rules (as the Casio): algebraic, left to right; results cut (not rounded) to the 10 digits shown and kept
  so (1 / 3 x 3 = 0.999999999); K: x keeps the first number, + - / the second; the Casio's %; MRC twice clears;
  M+ / M- / TAX / COST... finish the calculation first; E: the result / 10^10 until it fits, or / by 0; only
  C and AC go on. COST / SELL / MAR: margin on the selling price. The tax rate and the memory in the global
  variables MHTAX and MHMEM (0 STO+ makes them, as TZ in Zones 47).
- Cutting to 10 digits (LBL :TRUNC:): 10^(10 - digits before the point) by dividing by 10 (no LOG), IP; then
  the decimals counted up from 0 (FP of |x| 10^d), so an integer takes no loop and money two. R86 keeps the
  value whose digits R45 / R46 hold: the display does not cut the same value twice.
- Speed (profiled by label in the simulator): the first version took 2 000-2 700 steps a key (the AGRAPH loops,
  3 steps a column; the display walking ten cells; cutting twice). Now LBL :R16: and :R4: (AGRAPH unrolled),
  the cells in use only, the decimals counted up: a key 650-1 700 steps (0.1-0.3 s at Almanac 47's 0.17 ms a
  step), the start 4 200 (0.7 s).
- 98 of the 100 local labels used (11 glyphs, 30 keys, 11 operations, 46 named): small conditions written
  without a label where the false case leaves 0 in X (`RCL 26 X≠0? 1 STO+ 27`).
- Tests (tests/test_mh10m.py): Casio examples worked by hand, 400 random key sequences against a Python model
  of the rules (exact decimals; the display, E, M, minus and the key's indicator after every key), the digit
  cells against the glyphs of layout.py after every key, one key inverted at a time, the end (the stack, LASTx,
  the registers, MHMEM).

## Oct 24, 2026 - the commented rejig source build/forum/MH10M.p47u (Victor)

- Logic 47's tools/build_forum.py: an '@' header (Index, Author, Version, Source, Tested, Input, Output), the
  steps of build/MH10M.txt indented (STRUCT), the source's REM lines after ';', label names on LBL / XEQ / GTO,
  notes on the numeric labels (the glyphs 00-10, the keys at their KEY? codes, the operations 86-96). Run at the
  end of tools/build_mh10m.py; tests/test_forum.py. Not yet checked with rejig: the .p47 should be that of
  build/MH10M.txt.
- docs/MH10M_tour.gif (tools/make_gif.py): a session key by key.

## To do

1. Run on Victor's C47 (convert build/MH10M.txt with rejig); check the KEY? codes with KEYTEST (KT3).
2. Ideas: a GT (grand total) key as on other Casio models; the key highlight only while the key is held, if
   the C47 can tell.
