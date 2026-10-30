# b2's HTTP API: what was missing when developing Frogs and Flies

This is a review of b2's HTTP API, from the point of view of using it
to develop and test a BBC Micro game. It was written at the end of
the Frogs and Flies port (milestones 1-5 in
[beeb-port-plan.md](beeb-port-plan.md)), from a log kept during the
work ([notes/b2-api-gaps.md](notes/b2-api-gaps.md)).

Most of the testing was done by an AI agent (Claude) driving b2 from
scripts, with the human developer doing the things only a person at
the keyboard could. That makes the API's gaps unusually visible: an
agent can't glance at the emulator window, hold a key down, or listen.
But the same gaps would get in the way of anyone automating tests, or
just scripting checks from a Makefile.

## How the API was used

The game runs on a BBC Model B (and Master 128), with the OS kept
running. A typical check:

1. `make`, then upload the disc image with `run`.
2. Wait for it to start.
3. Set up a situation: poke positions, game states, inputs.
4. Read back memory (`peek`) and take a `screenshot`.
5. Decode the screenshot into BBC pixels and compare with what was
   expected (for example, with a Stella snapshot of the Atari 2600
   original).

All of this is wrapped up in [tools/b2.py](tools/b2.py).

## What worked well

- **`run` with an uploaded disc image** made the edit-build-run loop
  one command (`make run`). No files to copy, no disc to mount by hand.
- **`peek` and `poke`** were enough for a great deal: reading game
  state, setting up situations, and even patching code in memory.
  Everything below builds on these two.
- **`screenshot`** (added during the project) replaced decoding screen
  memory by hand. It showed problems memory could never show, such as
  the picture's vertical position, and it let the port be compared
  with the original pixel for pixel.
- The API was easy to use from both `curl` and Python, and its error
  messages pointed at the problem.

## The gaps, in order of how much they cost

### 1. No way to press keys

This was the biggest gap. The game reads the keyboard matrix directly
(first with OSBYTE &81, later straight from the System VIA), so
`paste`, which goes through OSRDCH, does nothing.

Workarounds:

- Patch out the main loop's keyboard scan in memory (NOP the `jsr`,
  found by parsing the assembler listing), then poke the variables
  the keyboard code would have set. That only worked because this game
  happens to have a software layer between the keys and the game logic.
- Add a test hook to the game itself: a variable that, when poked, acts
  as a key press on the title screen. This is code in the product that
  exists only because the emulator can't press keys.
- Everything else went to the human: two-player play tests, key
  ghosting, ESCAPE during the game, the Master's numeric keypad, and
  checking that redefined keys work.

**What would help:** key down and key up by BBC key (name, or matrix
row/column), held for a number of frames or until released, and
ideally a queue of key events with frame timings. For example:

    keydown/WIN/KEY        keyup/WIN/KEY
    keys/WIN?press=A,TAB&frames=10

### 2. No pause, step or run-until

The emulator ran freely while tests talked to it, so the state could
change between two requests. A frog's whole jump could finish before
the first screenshot of it arrived. Every check had to either freeze
the game by poking and patching code, or read state before and after
and throw away samples where it had changed.

There was also no way to tell when a program had started after `run`,
so every test began with a fixed sleep of 3-4 seconds.

**What would help:** pause, resume, step N frames (or cycles), and run
until an address is executed or a memory condition holds, each with a
timeout. For example:

    pause/WIN    resume/WIN    step/WIN?frames=1
    run-until/WIN?pc=main_loop&timeout=5000

### 3. Screenshots aren't tied to a point in time

- **Lag:** a screenshot showed the display 1-2 frames behind a `peek`
  made at the same moment, so a screenshot couldn't simply be checked
  against memory.
- **Background throttling:** with b2's option to draw fewer frames
  while in the background, screenshots could be a third of a second or
  more out of date. Several screenshots in a row showing exactly the
  same frame looked like a game bug.
- **Stale rows:** at 60Hz (262-line frames), b2's output only redraws
  its first ~524 of 576 rows; the rest keeps whatever was there before,
  which looked like a second copy of the picture. Nothing in the
  screenshot says which parts are current.
- **Scaling:** the image is the host's rendering, 736x576 with the
  border, so mapping it back to BBC pixels needed offsets found by
  experiment (x 48, y 90 at 50Hz and y 70 at 60Hz, 4x2 pixels per
  MODE 2 pixel).

**What would help:**

- a frame number with every screenshot and peek;
- a combined request that returns a screenshot and some memory ranges
  from the same frame;
- the emulated output itself, or at least the picture area and scale,
  rather than the host rendering;
- unrefreshed areas cleared, or the screenshot cropped to what was
  drawn last frame.

The debugger's pixel metadata (which address and time each pixel came
from), if exposed through the API, would have answered several
questions directly.

### 4. No way to tell whether the emulator is running

Once, b2 got stuck. `run` returned success, but memory stayed empty
and the screenshot showed an old frame. Ruling out a bug in the game
took several peeks and a trip through the listing, and in the end the
human had to look at b2.

**What would help:** a status endpoint (running, paused or stopped,
the PC, and why it stopped), and `run`/`reset` returning an error if
the machine doesn't then run.

### 5. No hardware state or audio

- **Video:** with no way to read CRTC, video ULA or VIA registers, the
  palette had to be read from the OS's private copy at &36F. That was
  only right because the game set colours with VDU 19 at the time.
- **Sound:** sound couldn't be checked at all, beyond peeking the
  game's own record of what it had written to the SN76489. Whether it
  sounded right was down to the human listening.

**What would help:** register dumps for the CRTC, video ULA (palette
and control register), System and User VIAs, and SN76489, plus either
a log of sound chip writes with timestamps or audio capture to a WAV
file for N frames.

### 6. No timing or profiling

Much of the late work was about timing: drawing the sprites while the
beam was elsewhere on the screen. Finding out how long things took
meant adding instrumentation to the game with VIA timers and peeking
the results. The first attempt gave wrong answers, because the vsync
code restarted the timer being used for measuring.

**What would help:** read the CPU cycle counter; "cycles from address
A to address B", averaged over N frames; and the beam position
(scanline) when a given address runs. The last would have answered
the tearing questions directly.

### 7. Smaller things

- **Which machine?** There's no way to ask which configuration is
  running. Tests assumed a Model B with DFS. The Master 128 checks only
  happened because the human had switched b2's configuration, and
  said so.
- **Content type:** `poke` needs `Content-Type: application/octet-stream`.
  Python's default (form-urlencoded) gets a bare "400 Bad Request". The
  docs say octet-stream is assumed "unless otherwise specified", which
  is easy to read as "any type is fine". An error saying what was
  expected would help.
- **Labels:** `peek` and `poke` only take hex addresses. b2 can already
  load 64tass label files, so accepting label names would save a lookup.
- **Registers:** CPU register read and write, and breakpoints that can
  skip or return, would have replaced patching code in memory.

## What the gaps cost

Besides time, the gaps left their mark on the project itself:

- **Code in the game that exists only for testing:** the title screen's
  test key hook, and timing instrumentation (frame times, per-sprite
  deadlines) that's mostly there because the emulator couldn't measure
  it.
- **Tooling that works around the emulator:** patching code by parsing
  the listing, fixed sleeps, peeking before and after each screenshot,
  and hard-coded screenshot offsets for each video mode.
- **Checks that needed a person:** every input test, every listening
  test, and anything that depended on whether b2 was running.

Of the suggestions above, **key input** and **pause/step/run-until**
would remove the most of this. With those, most of the other
workarounds become simple, and the rest become merely convenient.
