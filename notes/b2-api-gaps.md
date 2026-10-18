# b2 HTTP API gaps - working log (agent-facing)

Raw material for the human-readable b2 API document (milestone 5 item
in beeb-port-plan.md). Append an entry whenever b2's API gets in the
way: what was being done, what was missing or awkward, the workaround,
and what facility would have helped. Keep entries terse; the final
document is written from these.

Format: `- [area] problem. Workaround: ... Wanted: ...` (with the
milestone/date where useful).

## Input

- [keyboard] No way to press BBC keys. `paste` goes through OSRDCH,
  but the game reads the keyboard matrix with OSBYTE &81 (negative
  INKEY), so pasted text does nothing. Workaround: NOP out main_loop's
  `jsr scan_keyboard` in memory and poke the SWCHA/INPT4 shadows
  (tools/b2.py patch_call). Only possible because the game has a
  software layer between keys and logic. Wanted: key down/up by BBC
  key (name or matrix code), held for N frames or until released;
  ideally queued with frame timing. (M2-M4)
- [keyboard] Keyboard play tests had to be done by the user for the
  same reason (e.g. ghosting on diagonal + fire). (M2)

## Output: video

- [screenshot] Originally no screenshot endpoint; had to peek screen
  memory plus the OS palette copy (&36F) and decode MODE 2 by hand,
  which couldn't show CRTC problems (position, size). The added
  `screenshot` endpoint fixed this. (M1)
- [screenshot] Screenshot and peek aren't from the same frame: a
  screenshot trails a peek taken at the same moment by 1-2 frames, so
  checks had to use steady states or peek before and after and discard
  mismatches. Wanted: pause/step, or a combined "screenshot + memory
  ranges from the same frame" request. (M2-M3)
- [screenshot] With b2's "draw fewer frames in the background" option
  on, screenshots were up to ~0.3s+ stale, which looked like a game
  bug (identical screenshots during a splash). Wanted: screenshots of
  the emulated frame regardless of host display rate, or a
  frame number with each screenshot. (M2, found M3)
- [screenshot] The image is the host rendering (736x576, scaled, with
  border); mapping to BBC pixels needs hard-coded offsets (x 48, y 90,
  4x2 per MODE 2 pixel), found by experiment. Wanted: raw emulated
  output, or the picture's position/scale in the response; exposing
  the debugger's pixel metadata (address/time per pixel) would be even
  better. (M1)
- [screenshot] With a 262-line (60Hz) frame, b2's output only refreshes
  the first ~524 of its 576 rows; the rest keeps old content (a stale
  copy of the picture's top), which looks like a second picture. A
  screenshot can be partly stale with no indication. Wanted: unrefreshed
  areas cleared, or the screenshot cropped to what the TV drew last
  frame. (M5)
- [hardware state] No API to read CRTC/ULA/VIA registers. Palette had
  to come from the OS's copy at &36F (only right because VDU 19 was
  used). Wanted: device register dump endpoints (CRTC, video ULA
  palette, System/User VIA, SN76489). (M1, M5)

## Output: audio

- [audio] No way to capture or inspect sound. The TIA->SN76489
  conversion was checked by logging the game's own record of SN76489
  writes (peek), and by the user listening. Wanted: SN76489 register
  state endpoint, a log of sound chip writes with timestamps, and/or
  audio capture to WAV for N frames. (M5)

## Execution control and timing

- [sync] No pause/step/run-until. Tests ran against a free-running
  emulator, so state changed between requests (e.g. a jump finished
  before the first screenshot of it). Workarounds: park sprites in
  fixed states by poking, patch out code. Wanted: pause, resume, step
  N frames/cycles, run until address executed / memory condition, all
  with timeouts. (M2-M4)
- [boot] No way to know when the program has started after `run`;
  used fixed sleeps (3-4s). Wanted: run-until-address (e.g. main_loop)
  or "wait until PC reaches X" with timeout. (M1-M5)
- [timing] No cycle counter or profiling via the API. Render time was
  measured by instrumenting the code with VIA timers and peeking the
  result; the first attempt (User VIA T1) gave wrong figures because
  the vsync event restarted T1 mid-render. Wanted: read the CPU cycle
  counter, or "cycles between address A and address B" averaged over
  N frames; beam position (scanline) at a given PC would have made the
  tearing analysis direct. (M2-M3)
- [patching] Stubbing out calls meant NOPing `jsr` instructions found
  by parsing the 64tass listing. Wanted: CPU register read/write, and
  breakpoints that can skip/return (or run a callback-like action).
  (M2-M5)

- [status] No way to ask whether the emulator is running, paused or
  stopped in the debugger. During the 60Hz work, `run` appeared to
  succeed but memory stayed zero and the screenshot showed an old
  frame; it took several peeks and a listing to rule out a code bug.
  Wanted: a status endpoint (running/paused/stopped, PC, why stopped),
  and `run`/`reset` reporting failure if the machine isn't running.
  (M5)

## Configuration

- [config] No way to ask which config/model is running, so tests
  assumed a Model B with DFS. Wanted: endpoint returning the current
  config name and hardware. (M1)

## Minor

- [poke] `poke` needs `Content-Type: application/octet-stream`; Python
  urllib's default (form-urlencoded) gets a bare 400. The docs say
  octet-stream is assumed "unless otherwise specified", which is easy
  to misread as "any type is fine". A clearer error would help. (M2)
- [peek/poke] Addresses are hex only in the path; label names (from
  loaded symbols) would save a lookup step. b2 can load 64tass label
  files already. (M2-M5)
