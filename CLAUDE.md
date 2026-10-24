# MH-10M 47: working rules

- Work on a new branch; Victor creates and merges the PRs. Never force-push or rewrite history.
- Commit author: "Victor Valdes" <valdesvj@users.noreply.github.com>.
- Never commit binaries (.p47 files made by rejig).
- Edit the program in programs_rem/MH10M.txt (commented source), then run python3 tools/build_mh10m.py:
  it writes programs/, build/ and listings/. Never edit those three by hand.
- The build fills the marker lines REM ==== GLYPHS, WORDS, STATIC, INDOFF and INDON from python/layout.py
  (the 7-segment glyphs, the LCD, the keypad, the indicators): change the screen there.
- STRUCT as Elements 47: IF / ELSE / ENDIF, DO / WHILE / ENDDO, indented, no numbers in the source; a test
  right before IF / WHILE; never a test before ELSE, ENDIF, DO, ENDDO. At most 10 IF and 10 DO (the original
  DM42; MH10M has 6 DO). Named labels LBL :NAME: (1-7 letters or digits). Numeric labels: 00-10 the glyphs,
  11-85 the keys at their KEY? codes (XEQ IND 33), 86-89 + - x /, 90-93 their %, 94-96 cost / sell / margin.
  98 of the 100 local labels are used: merge small routines before adding one.
- Text on the C47 screen: ATEXT in GRFNT 21 (GRFNT 10 for the title). Restore GRFNT 20 and GRMOD 0 before
  the program ends. GRMOD and GRFNT take X: write `3 GRMOD`. AGRAPH words always through SINT.
- Key waits: DO / PAUSE 50 / KEY? 33 / WHILE / ENDDO (as Elements 47). KEY? codes checked on the C47: F1-F6
  11-16, the digits, + 85; the others not yet (README).
- Only commands already run on a C47 in Almanac 47, Elements 47 or Zones 47; a new command: say so and ask
  Victor to try it.
- Check every change in the simulator (python3 python/mh10msim.py writes docs/*.png) and with
  python3 tests/test_mh10m.py (the Casio model in the test is the reference of the rules: change both).
- python/c47sim.py, stdfont.py, tinyfont.py come from Almanac 47 (via Zones 47): a fix is made there first,
  then copied here.
- Work in one repository at a time (this one); the other 47 repositories are for reference only.
- Ask before anything that can't be undone. Pull requests only for mh10m47.
