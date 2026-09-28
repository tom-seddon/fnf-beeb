# Notes for Claude

- The port plan, decisions and milestone status are in
  `beeb-port-plan.md`. Keep its status section up to date as milestones
  complete.
- `make` must always pass. It checks that both 2600 ROMs (NTSC and
  PAL) reassemble byte-for-byte. Any change to shared code
  (`src/logic.s65`, `src/sound.s65`, `src/ram.s65`, `src/data_*.s65`)
  must keep the ROMs identical. Use `.if TARGET==...` for
  platform-specific differences.
- `make VERBOSE=1` shows the commands. The build is silent by default.
- Running the BBC version: b2 runs on the same Mac with its HTTP server
  on `localhost:48075` (check with `curl -s -o /dev/null -w
  "%{http_code}" http://localhost:48075/`; `000` means it isn't
  running, so ask). Useful endpoints (see b2's `doc/Debug-version.md`):
  `reset/b2?config=...`, `run/b2?name=X.ssd` (upload the .ssd as the
  body), `peek/b2/BEGIN/END`, `poke/b2/ADDR`. There is no screenshot
  endpoint. To see the screen, peek the screen memory and convert it to
  a PNG.
- Target: BBC Model B with DFS, OS kept running, 160x192 MODE 2 screen
  at &4400.
