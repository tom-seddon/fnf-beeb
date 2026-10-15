# Notes for Claude

- The port plan, decisions and milestone status are in
  `beeb-port-plan.md`. Keep its status section up to date as milestones
  complete.
- `make` must always pass. It checks that both 2600 ROMs (NTSC and
  PAL) reassemble byte-for-byte. Any change to shared code
  (`src/logic.s65`, `src/prepare_display.s65`, `src/sound.s65`,
  `src/ram.s65`, `src/data_*.s65`) must keep the ROMs identical. Use `.if TARGET==...` for
  platform-specific differences.
- `make VERBOSE=1` shows the commands. The build is silent by default.
- Running the BBC version: b2 runs on the same Mac with its HTTP server
  on `localhost:48075` (check with `curl -s -o /dev/null -w
  "%{http_code}" http://localhost:48075/`; `000` means it isn't
  running, so ask). Useful endpoints (see b2's `doc/Debug-version.md`):
  `reset/b2?config=...`, `run/b2?name=X.ssd` (upload the .ssd as the
  body), `peek/b2/BEGIN/END`, `poke/b2/ADDR`, and `screenshot/b2`
  (returns a PNG of the display; `make screenshot` saves it to
  `build/beeb-screen.png`).
- For testing in b2, use `tools/b2.py` rather than ad hoc scripts.
  From the command line: `run`, `state` (frogs, flies, scores, time of
  day, render time), `peek`/`poke` (label names like `pl_xs+1` work),
  `patch-call NAME` (NOP out main_loop's `jsr NAME`), `step-time`,
  `screenshot`, `show Y0 Y1` (print screen lines as characters). As a
  module (`sys.path.append('tools'); import b2`), `B2()` has the same
  and more, plus `load_screen`/`find_colour` for screenshots. Its
  header comment has recipes: driving inputs by patching out
  `scan_keyboard` and poking SWCHA/INPT4, freezing the flies, parking
  a frog, skipping ahead in time of day. It reads addresses from the
  last build, so `make` first. b2 must be set to draw every frame, and
  screenshots trail a peek by 1-2 frames.
- Target: BBC Model B with DFS, OS kept running, 160x192 MODE 2 screen
  at &4400.
