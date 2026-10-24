# AI Assistance Policy

## How this project uses AI

This project was **developed with the help of AI** — Claude (Anthropic) — as a cooperation. AI assisted with brainstorming, code generation, and documentation, but I reviewed all output, validated results against reference implementations, and take full responsibility for the work and any mistakes.

## Responsible use

- ✅ **I checked the results** — Every key of the program is checked in the C47 simulator against a Python model of the Casio's rules, on hand-worked Casio examples and 400 random key sequences, and every screen against the expected glyphs (`tests/test_mh10m.py`)
- ✅ **I maintained domain expertise** — I guide the AI with design decisions based on the Casio MH-10M's behaviour and how it is used for prices, margins and tax
- ✅ **I take full responsibility** — The work is mine; any errors are mine to fix
- ✅ **I'm transparent** — This file documents how AI was used

## Testing & Validation

- Simulator tests: the C47 program in `python/c47sim.py` (from Almanac 47), every screen and every text checked
- The model of the rules written separately from the program, in Python with exact decimals
- To be tested on real C47 hardware before each release

## License

This does not affect the GNU GPL-3.0 license. All code remains open-source and fully accessible.

---

*For more details, see `NOTICE` and the development documentation.*
