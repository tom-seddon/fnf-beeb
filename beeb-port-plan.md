# Frogs and Flies: BBC Micro port plan (first pass)

## 1. The approach in one paragraph

Keep the 2600 game logic almost exactly as it is and replace only the
display kernel. The disassembly already reassembles byte-for-byte, and
the game logic (physics, player state machine, fly AI, tongue,
scoring, time of day, CPU takeover) is plain 6502 that touches the
hardware in a small number of known places. On the BBC those places
become **shadow variables in RAM** (`SWCHA`, `SWCHB`, `INPT4/5`,
`COLUP0/1`, `REFP0/1`, `NUSIZ0/1`, `AUDxx`, ...). A new renderer reads
the game state once per frame and draws into a framebuffer. The
racing-the-beam code (`do_display`, `loc_F000`, `loc_F106`,
`prepare_object_hpos`, `apply_object_hmotions`, the hpos half of
`prepare_display`) doesn't come across.

The main risk is display semantics, not logic: working out exactly
where the kernel puts each object so that the BBC drawing matches. It
is a finite amount of work, and section 3 already covers most of it.

---

## 2. What the 2600 code does each frame (as far as the port needs to know)

```
main_loop:                        (overscan)
    sub_F6BE        collision: fly (missile) vs tongue (ball) -> score +2
    prepare_display score ptrs, sprite/missile/ball ptrs, colour bands, hpos
    inc byte_B3     frame counter
  (vsync, vblank)
    handle_players_inputs   SWCHA -> p0/p1_joystick_direction, idle timer
    update_player_physics   x+=dx, y+=dy for 4 objects (2 frogs, 2 flies)
    update_player_logic     one frog per frame (byte_B3&1): state machine 0-12
    update_tongues          one frog per frame; fire button / CPU auto-tongue
    sub_F5FD                fly AI (one fly every 8 frames)
    sub_F8F0                time of day: byte_B7 7->1, each step 26*64 frames
    sub_FA7E                random ambient croaks
    update_sounds
  (display)
    do_display
```

Things found while reading it that the port relies on:

- **4-object arrays.** RAM is laid out as `[frog0, frog1, fly0, fly1]`
  arrays: `pl_xs/mi_xs`, `pl_ys/mi_ys`, `pl_dxs/mi_visibles`,
  `pl_dys/byte_D1`. `update_player_physics` loops X=3..0 over them. So
  `mi_visibles` is really the **fly X velocity** and `byte_D1` is the
  **fly Y velocity**. Consequence: rebase the RAM block but keep its
  internal layout exactly as it is. Code such as `sta pl_flags+1,x`
  with X=$FF also relies on zero-page wraparound, so everything stays in
  zero page.
- **Sprite frames are addressed by LSB.** `byte_DB,x` holds the low
  byte of a frame's last row in the `grp_data` page. Literal constants
  such as `#$B7`, `#147` and `#165` appear in code (states 7, 10,
  `loc_F4D6`). Keep the `grp_data` page byte-identical and
  page-aligned on the BBC too. It's only ~200 bytes of real data plus
  padding.
- **Sprite frames:** 11 frames of 8x18 (1 bpp, bottom row at the lowest
  address). frog5 (sitting, `$B7`) and frog0-3 (jump, chosen by height
  through `byte_F25B`/`byte_F25F`). splash0-3 are for landing in the
  water. Two extra frames at `$FC82`/`$FC94` are used by the end-of-game
  sequence and look like lettering.
- **Vertical geometry** (kernel line `y` counts 74 at the top down to 1;
  each kernel line is 2 scanlines; playfield row = `y+10`; a further 11
  rows (10..0) are drawn after the kernel loop):
  - frog: kernel lines `pl_y-9 .. pl_y-1` (18 scanlines, 1 GRP row per
    scanline). P1 has `VDELP1=1`, so check it for a 1-scanline offset.
  - tongue (ball): 1 kernel line at `pl_y-3`, 8 pixels wide, drawn in
    the **playfield colour** (`COLUPF`). Only one tongue is drawn per
    frame (`byte_E5`). If both are out they alternate.
  - fly (missile): alternates every 2 frames (`byte_B3&2`):
    - frame A: 4 px wide (`NUSIZ=$20`), kernel lines `mi_y-2..mi_y-1`
    - frame B: 2 px wide (`NUSIZ=$10`), kernel lines `mi_y-2..mi_y`,
      x+2 if moving right.

    The existing comments say "1-clock"/"2-clock". On a real TIA, `$20`
    is 4 clocks and `$10` is 2.
  - Flies also swap between M0 and M1 every frame, which is why
    `sub_F6BE` does `eor byte_B3`. The swap is display-only and doesn't
    come across.
- **Horizontal:** TIA has 160 colour clocks and Mode 2 has 160 pixels,
  so the mapping is **1:1**, with screen_x = object_x + C for some
  constant C. The `+5` in `prepare_object_hpos` plus RESPx latency make
  C easier to measure (Stella debugger, TIA tab) than to derive.
  Sanity check: frogs should land exactly on the lily pads that
  `is_on_lily` thinks they're on (x 13..67, 82..136).
- **Colours:** 4 vertical bands, from `unk_FEB5[y]`:

  | kernel y | band | BG (`byte_98+n`)   | PF (`byte_9C+n`) |
  |----------|------|--------------------|------------------|
  | 46..74   | 0    | sky                | tree green `C4`  |
  | 38..45   | 1    | sky                | khaki `E4`       |
  | 22..37   | 2    | sky                | green `C6`       |
  | 0..21    | 3    | water              | green `C6`       |

  BG colours come from `unk_F7A2` indexed by time of day `byte_B7`.
  Every group of 4 is `[s,s,s,w]`, so there are only two BG colours
  (sky and water), and they darken towards night. Score digits use
  `pl_colours`, which also change with `byte_B7`. The score-area
  background is `byte_87`.
- **`pf_eor_value` flip:** when `unk_E6,x` is odd, `prepare_display`
  inverts the playfield *and* swaps the BG/PF colours. The main
  picture comes out identical. What actually changes is the tongue
  colour (ball = `COLUPF`) and the score-area background (`byte_87`).
  `unk_E6` only increments once `COLUP0` has bit 7 set, i.e. during the
  end sequence. Check in Stella that it's just a flicker effect.
- **CPU players:** `pl_flags` bit 6 = CPU control. `store_player_inputs`
  resets the idle counter `unk_BD` on any stick change. `sub_F71F`
  counts it down every 64 frames and hands the frog to the CPU. You get
  attract mode and 1-player-vs-CPU without writing anything extra.
- **Label errors to fix as you go:** `CXP0FB` at $04 is really
  `CXM0FB`. The NUSIZ comments are wrong (see above). `mi_visibles`
  and `byte_D1` are misnamed (see above).

---

## 3. Hardware touchpoints and their BBC replacements

| 2600 code | Uses | BBC replacement |
|---|---|---|
| `main` / `debounce_reset` | `SWCHB`, `Intim` seed, `sta 0,x`/`txs` clear of all of $00-$FF | BBC init: clear only the game ZP block; seed `random_seed` from System VIA T1 low byte |
| `main_loop` | `Tim64t`, `Intim`, `VSYNC`, `WSYNC`, `VBLANK`, `CXCLR` | wait for vsync, then call `render_frame` |
| `initialise_memory` | writes `VDELP1`, `COLUP0`, `COLUP1` via zp,x with `.byte` addresses | shadow vars **in zero page** (the addresses are bytes) |
| `pn_state9` | writes `COLUP0/1 = $FF` | shadow var (`prepare_display` reads `COLUP0` back as game state) |
| `prepare_display` | `REFP0,x`, `NUSIZ0/1`, hpos, ptrs | keep the logic half (`byte_E5`, `unk_E6`, colour bands, tongue X); replace the rest with "build render list" |
| `sub_F6BE` | `CXM0FB`/`CXM1FB` bit 6 (missile-ball) | software rectangle test of fly vs the tongue drawn this frame |
| `initialise_player_difficulty`, `main_loop` | `SWCHB` | shadow byte built from keyboard (reset key, difficulty toggles) |
| `handle_players_inputs` | `SWCHA` | shadow byte built from keyboard, same bit layout |
| `update_tongues` | `INPT4,x` (bit 7 = 0 when pressed) | two consecutive shadow bytes `INPT4`, `INPT5` |
| sound code | `AUDC0/AUDF0/AUDV0,x` | shadow bytes, ignored for now (later: TIA-to-SN76489 per frame) |

Most of the logic then assembles unchanged, because on the BBC build
`SWCHA`, `COLUP0` and so on are just defined as RAM addresses. Real
edits are needed only in `main`, `main_loop`, `sub_F6BE` and the tail
of `prepare_display`.

---

## 4. Source organisation and build

**Keep the 2600 byte-exact check green throughout.** It is the safety
net for refactoring.

1. Split `fnf-2600.s65` into include files, included **in the original
   order** so the 2600 layout doesn't move:
   - `ram.s65`: the $80-$F6 variable block (as a relocatable `.logical`
     or `* =` section)
   - `logic.s65`: state machine, physics, tongues, fly AI, time of day,
     `rnd`, the collision *response* part
   - `sound.s65`
   - `tia_display.s65`: kernel, hpos, TIA half of `prepare_display` (2600 only)
   - `data_grp.s65`, `data_pf.s65`, `data_tables.s65`
   - `fnf-2600.s65`: top level: TIA/RIOT equates, reset vectors, includes
2. Add `fnf-beeb.s65`: BBC equates (shadow regs), the same `ram.s65`
   rebased into zero page, `logic.s65`, the data includes, and the BBC
   platform files:
   - `beeb_main.s65`: init, main loop, vsync
   - `beeb_input.s65`: keyboard to `SWCHA`/`SWCHB`/`INPT4`/`INPT5`
   - `beeb_render.s65`: background, sprites, score, palette
   - `beeb_tables.s65`: screen row addresses, Mode 2 pixel expansion,
     bit reverse, TIA-to-BBC colour
3. Makefile: a `beeb` target assembles to `beeb/Z/$.FNF` + `.inf`
   (BeebLink folder, as `BEEB_DEST` already sets up) and an `.ssd`
   using `submodules/beeb/bin/ssd_create.py`. Keep `make` doing the
   2600 compare.

Places where 2600-only differences can't be handled by include order
(e.g. `prepare_display` being half logic, half TIA) get
`.if TARGET==TARGET_2600` blocks. Keep them to a handful.

---

## 5. BBC runtime design

### Machine and memory (baseline: Model B, DFS, OS kept running)

| Range | Use |
|---|---|
| &00-&8F | game RAM (the 2600 $80-$F6 block rebased, ~119 bytes) + ~16 bytes of shadow regs + renderer ZP temps. Tight but fits. Several 2600 display pointers (`pf*_data_ptr`, digit ptrs, `enam*`, `enabl`, `grp*`) become dead, which frees space later |
| &100 | stack |
| &1900-&43FF | code + data (~10.7K available; estimate ~5-6K: logic ~2.2K, renderer ~2K, tables ~1K) |
| &4400-&7FFF | 160x192 MODE 2 screen (&3C00 bytes) |

**Screen: 160x192 from the start.** That is the 2600 picture 1:1 (~190
lines). Setup:

- Select MODE 2 through the OS first. This gets the ULA mode, the
  20K hardware wrap size in the addressable latch, and the OS's idea
  of the palette.
- Then reprogram the CRTC:
  - R6 = 24 displayed character rows
  - R7 ≈ 30 vertical sync position, to re-centre the picture (tune by
    eye in b2)
  - R12/R13 = &4400/8 = &0880 screen start
- Clear &4400-&7FFF yourself.
- After this, the OS VDU drivers don't know the screen layout, so
  don't use OS text or graphics output. VDU 19 for palette changes is
  still fine.

**Boot ordering gotcha:** selecting MODE 2 clears &3000-&7FFF, which
overlaps the code area. So the order must be MODE 2 *then* load the
code. `!BOOT` does `MODE 2` then `*RUN FNF`. If the code ever changes
mode itself, it has to do so before it overwrites anything above
&3000.

**Keeping the OS** makes disc loading, `*FX19` vsync and `OSBYTE &81`
key reads free. Housekeeping with the OS running:

- disable Escape (`*FX229,1`) so it can't abort anything
- stop the keyboard buffer filling up while keys are held: flush it
  each frame (`*FX15`) or turn off auto-repeat (`*FX11,0`)
- don't use flashing colours, so the OS never rewrites the palette
  behind our back

If memory gets tight later, the options are in order of effort:
1. drop the dead 2600 tables
2. relocate the code down below &1900 after loading (the game doesn't
   need DFS workspace once it's running)
3. take over the machine

### Main loop

Keep the 2600 order so behaviour (including the one-frame display lag)
is identical:

```
main_loop:
    jsr wait_vsync            ; *FX19 to start with
    jsr render_frame          ; from the render list built last frame
    jsr scan_keyboard         ; -> SWCHA, SWCHB, INPT4, INPT5 shadows
    lda SWCHB
    lsr a
    bcc reset                 ; reset key
    jsr check_fly_tongue      ; was sub_F6BE
    jsr prepare_display       ; logic half + build render list
    inc byte_B3
    jsr handle_players_inputs ; --- from here on: 2600 code verbatim ---
    jsr update_player_physics
    jsr update_player_logic
    jsr update_tongues
    jsr sub_F5FD
    jsr sub_F8F0
    jsr sub_FA7E
    jsr update_sounds         ; harmless: writes shadow AUD regs
    jmp main_loop
```

**Speed:** the BBC is 50Hz, so the game runs at 5/6 of NTSC speed,
which is exactly what the PAL 2600 cartridge does (its logic is the
same, only colours and timer values differ). An optional 6:5 frame
skip to match NTSC speed can come later.

### Rendering

**Background** is static apart from colour. Render it once at startup
**from the PF tables at runtime** rather than storing a 15K image.
85 rows x 3 bytes (`pf0/1/2_data`), reflected, 20 bits per half. Each
PF bit is 4 px = exactly 2 Mode 2 bytes, and each PF row is 2
scanlines. The colour of each pixel is `role(band(row), bit)`.
`tools/pf_convert.py` already does this in Python and makes a good
reference and test image.

**Colour = palette, not pixels.** Each 2600 colour *register role* gets
its own Mode 2 logical colour. Time-of-day changes and the
end-sequence flicker then become palette writes, and nothing on screen
is redrawn.

| Logical | Role | Driven by |
|---|---|---|
| 0 | sky (bands 0-2 BG) | `byte_98` |
| 1 | water (band 3 BG) | `byte_9B` |
| 2 | tree green (band 0 PF) | `byte_9C` |
| 3 | khaki (band 1 PF) | `byte_9D` |
| 4 | lily/shore green (bands 2-3 PF) | `byte_9E` |
| 5 | frog 0 | `COLUP0` |
| 6 | frog 1 **and flies** | `COLUP1` (flies share frog 1's logical colour) |
| 7 | spare | (was a separate fly colour; free if we ever want it back) |
| 8 | tongue | `COLUPF` of the tongue's band |
| 9 | score 0 | `pl_colours` |
| 10 | score 1 | `pl_colours+1` |
| 11 | score-area background | `byte_87` |
| 12-15 | spare | later: second colour of dither pairs for sky/water |

Colour values are the **NTSC** ones (`.if PAL` false throughout), with
PAL-rate timing. On the 2600 the flies alternate between the two
player colours each frame. Here they are always frog 1's colour, and
the end sequence's `COLUP0/1 = $FF` makes them white along with both
frogs, as before. Known wrinkle: a fly passing over frog 1 won't be
visible. If that matters, give the flies logical 7 again.

Each frame, `render_frame` compares those source bytes with the values
last applied. For each one that changed it calls
`set_role_colour(role, tia_colour)`, which has two backends:

- stock ULA: `tia_to_beeb[c>>1]` gives the nearest of the 8 colours,
  written to &FE21 (or through VDU 19, since it happens a handful of
  times per game)
- VideoNuLA (later): the 12-bit RGB from the existing
  `D.TIANULAPAL`/`tia_palette.py` work

Dithering (your DITHER5 / `pf_convert.py` pairs) slots in later by
giving the big roles two logical colours and rendering the background
as a pattern of the pair. Sprites and the rest of the renderer don't
change.

**Sprites.** Keep the 2600 1 bpp GRP data as it is and expand at draw
time:

- Mode 2 byte = 2 pixels (left pixel bits 7,5,3,1; right 6,4,2,0).
  For a sprite colour c, a 4-entry table maps a 2-bit pixel pair to
  (mask, colour byte): `00→(&FF,0)`, `01→(&AA,right(c))`,
  `10→(&55,left(c))`, `11→(&00,both(c))`.
- Even x: 4 bytes per row. Odd x: shift the 8 bits into 9, giving 5
  bytes per row.
- `REFP` reflection uses a 256-byte bit-reverse table.
- Row addresses come from a 256-entry lo/hi table (Mode 2 character
  cell layout: +1 per line, +640 per 8 lines). Column offset is
  `(x>>1)*8`.
- Save-under: before drawing, copy the bytes underneath (at most 5x18
  per frog) and restore them **in reverse order** next frame. Overlaps
  (frog/frog, tongue/fly) then sort themselves out.
- Draw order follows TIA priority: tongue → flies → frog 1 → frog 0.

Rough per-row inner loop (odd x shown):

```
    ldy #row
    lda (grp),y          ; 8 px, 1 bpp
    tax
    lda reverse,x        ; only if reflected
    ...                  ; split into 2-bit pairs; for each byte column:
    lda (scr),y
    and mask_tab,x
    ora colour_tab,x
    sta (scr),y
```

Estimated cost: ~5 objects x (save + restore + draw) is roughly
15-20K cycles, about half a frame at 2MHz. That's fine for a first
pass.

**Tongue:** an 8x2 rectangle at `(ball_x, line(pl_y-3))`. Ball X is
already computed in `prepare_display` (`pl_x ± unk_F796[counter] + 1`),
so keep that code.

**Flies:** 4x4 or 2x6 rectangles as described in section 2. Nothing is
drawn when `mi_y == 0`.

**Score:** 4 digits, each 3x5 PF bits = 12x15 px (PF bit = 4 px, digit
row = 3 scanlines). P0 at x≈20..47, P1 at x≈100..127 (PF1, not
reflected, rewritten mid-line). Redraw only when `pl_scores` changes.
Colour comes from the palette. Either decode the existing
`left_digits_pf_data` table or use 3-bit columns.

**Tearing:** first pass renders straight after vsync. Frogs mostly live
at the bottom of the screen, so the beam is usually ahead of the
drawing. If it's visible, options are: draw in bottom-to-top order,
start the render from a VIA timer at a chosen raster line, or split
into two passes chasing the beam. Not a first-pass concern.

### Input

`scan_keyboard` builds the 2600 register images directly, so
`handle_players_inputs` and `update_tongues` are untouched:

```
SWCHA  bits 7..4 = P0 ~R ~L ~D ~U, bits 3..0 = P1 ~R ~L ~D ~U   (0 = pressed)
INPT4  bit 7 = ~P0 fire;   INPT5 bit 7 = ~P1 fire
SWCHB  bit 0 = ~reset, bit 6 = P0 pro, bit 7 = P1 pro
```

Drive it from a table of 10 INKEY codes, so remapping is trivial. A
suggested default:

| | Up | Down | Left | Right | Fire |
|---|---|---|---|---|---|
| P0 (left frog) | W | S | A | D | Tab (or SHIFT) |
| P1 (right frog) | ↑ | ↓ | ← | → | COPY (or RETURN) |

Plus f0 = game reset, f1/f2 = toggle P0/P1 difficulty (latched in
`SWCHB`). The 192-line screen has no spare strip, so show the
difficulty as a small marker in the score area. There's free
background at x 0-19, 48-99 and 128-159. An "A"/"P" glyph or a block
next to each score, in that player's score colour, would do. Leave it
out of the first pass if it gets in the way.

First pass uses `OSBYTE &81` with negative INKEY codes (10 calls a
frame is fine). Check the key matrix for ghosting on diagonal + fire
combinations. SHIFT and CTRL aren't in the matrix, so they never
ghost, which makes them good fire keys. Direct System VIA scanning can
come later.

### Collision (`sub_F6BE` replacement)

The 2600 reads the TIA missile-ball latch from the frame just drawn,
then does an extra X check. `mi_x - pl_x - 1` is compared unsigned
against 6, so a hit is rejected only when the fly is within ~6 px to
the right of the frog's X, i.e. over the frog's own body. In software, for the tongue that
was rendered last frame (`byte_E5`, only if its counter is non-zero)
and each fly: if their rectangles overlap, set Y = fly index, X =
`byte_E5`, and fall into the existing tail of `sub_F6BE`, which does
the X check, adds 2 to the score in BCD, and resets the fly. Drop
the `eor byte_B3`.

---

## 6. Milestones

Each one ends with something visible in b2 that you can compare with
Stella.

0. **Refactor, 2600 still byte-exact.** Split into includes; define the
   shadow-register seam; fix the misleading labels in section 2.
   *Done when:* `make` still reports both ROMs identical.
1. **Beeb skeleton.** Boots from `.ssd` or BeebLink (`!BOOT`: MODE 2,
   then `*RUN`), reprograms the CRTC to 160x192 at &4400, sets the
   palette through `set_role_colour` for time-of-day 7, renders the
   background from the PF data, draws both scores as "00".
   *Done when:* a b2 screenshot looks like a Stella screenshot with no
   sprites.
2. **Logic transplant + frogs.** Main loop at 50Hz, keyboard shadows,
   frogs drawn with save-under, all 11 frames, reflection. Jumps,
   water splash, respawn on the lily pad.
   *Done when:* two people can hop frogs around from the keyboard and
   the frogs land on the lily pads where they should, which also pins
   down the X offset C.
3. **Flies, tongue, collision, score.**
   *Done when:* the game is playable, with scores going up by 2.
4. **The rest of the game.** Palette changes over time of day, the
   end-of-game sequence (states 6-12, lettering sprites, fly across the
   screen), CPU takeover after idling, reset and difficulty keys.
   *Done when:* a full game runs from start through the end sequence,
   and a game left idle plays itself.
5. **Later (not first pass):**
   - sound: shadow AUDC/AUDF/AUDV → SN76489 once per frame
   - dithering / VideoNuLA palette
   - tearing
   - 6:5 NTSC speed option
   - title and instruction screen, key redefinition
   - Master/Electron considerations

**Optional but cheap confidence check:** the logic is the same code, so
the same seed and the same per-frame inputs should give the same RAM on
both machines. Log `$80-$F6` each frame in Stella (debugger script) and
the rebased block in b2, then diff. The first divergence points
straight at a porting bug.

---

## 7. Decisions

Decided on 2026-09-28:
- **Machine:** Model B + DFS (PAGE &1900) as the baseline, OS kept
  running. Reconsider if memory gets tight.
- **Screen:** 160x192 MODE 2 at &4400 from the start.
- **Colours:** NTSC values, 50Hz timing. Colour is only data in
  `unk_F79E`/`unk_F7A2`/`p*_colours` and the table in
  `set_role_colour`, so it's easy to revisit.
- **Flies:** same colour as frog 1 for now. Rethink if that doesn't
  work out.

- **Difficulty display:** a small marker next to each score (see
  Input). It only has to be visible. If it isn't self-explanatory, the
  instructions can explain it.

Decided on 2026-10-14:
- **Playfield symmetry:** the BBC background stays exactly
  symmetrical. The 2600's mid-line PF write effect (see Status) is
  not copied. `tools/compare_stella.py` will keep reporting those
  pixels as differences.

To revisit once the game is running:
- Fly colour.

---

## 8. Status

| Milestone | Status |
|---|---|
| 0. Refactor, 2600 still byte-exact | done (3dec04f) |
| 1. Beeb skeleton | done (d747ef5, checked against Stella) |
| 2. Logic transplant + frogs | done (439dc8a, 0e92285; keyboard play tested) |
| 3. Flies, tongue, collision, score | done (f373ba7, 679d89e, and this; play tested) |
| 4. The rest of the game | next |

Milestone 1 notes:
- `fnf-beeb.s65` assembles the shared code unchanged. Only `VDELP1`,
  `COLUP0` and `COLUP1` need to be zero page shadows (they're in
  `initial_addrs`). The other shadow registers live after the code
  and the shared code just uses absolute addressing for them.
- Zero page: game RAM &00-&7F, shadows and renderer pointers from
  &80 (`zp_end` checks it stays below &90). Code ends around &2900.
- Screen layout (`src/beeb_render.s65`): score area lines 0-20
  (digits on lines 2-16), PF rows 84..0 on lines 21-190 at 2 lines
  each, line 191 black.
- Stock ULA colours come from `tools/make_tia_to_beeb.py`, which
  classifies by hue rather than nearest RGB (nearest RGB turns the
  greens and khaki black). Time of day 7 gives cyan sky, blue water,
  green trees and lily pads, and yellow reeds. Trees and lily pads are
  both green: revisit with dithering or VideoNuLA.
- Band boundaries follow `unk_FEB5` (water from PF row 31 down, reeds
  rows 48-55). Checked against Stella with `tools/compare_stella.py`:
  they match exactly (`tools/pf_convert.py` is wrong by a row in
  places).
- The 2600 picture isn't quite symmetrical. The kernel writes PF2 and
  PF1 while the beam is in the right half, so on the second scanline
  of each kernel row, right-half x 100-111 (PF2 bits 2-0) and x 132-143
  (PF1 bits 5-7) already show the next row down. The exact write time
  shifts a little on rows with sprites, so a few rows don't show it.
  The rows after the kernel loop (10-0) write PF in hblank and don't
  show it. This accounts for all but 8 of the 322 pixels that differ
  from Stella. The BBC doesn't copy this (see Decisions).
- `prepare_colours` (`src/beeb_main.s65`) duplicated the colour half
  of `prepare_display` until milestone 3 shared it.

Milestone 2 notes:
- The shared logic runs every frame in the 2600's order, at 50Hz.
  `sub_F6BE` is still called, but the collision shadows are always 0
  until milestone 3.
- Frog geometry, checked pixel for pixel against Stella: frog i is on
  kernel lines `pl_y-9..pl_y-1` (only lines 1-74 are drawn). On the
  BBC, sprite row k (0-17) is screen line `171-2*pl_y+k`, with GRP
  byte `grp_data+byte_DB-2-k`. Every frame (sitting, jump, splash)
  has its top row at k=0. Screen X is `pl_x+1`, so the X offset C=1.
- Sprites use save-under, restored in reverse order. Blank rows at the
  top and bottom of a frame are skipped, the column code is unrolled,
  and the masks come from tables (`sprite_masks_0..3`).
- Timing: the OS vsync event starts User VIA T1 (one-shot) to time out
  as the beam leaves the bottom of the picture (line 192). The main
  loop renders then (about 5-7ms with two frogs, inside the ~7.7ms
  before the picture starts again), then runs the game logic.
  `render_time` holds the last render time in us. Things that didn't
  work: rendering straight after `*FX19` (a frog near the top of a
  jump was erased before the beam reached it and redrawn after, so it
  never appeared); waiting for line 192 after `*FX19` (rendering ran
  past the next vsync, halving the frame rate); a free-running T1 synced
  once at startup (frogs were sometimes caught half drawn, presumably
  as it drifted).
- CPU jumps (state 7) always land on a pad. Only a player's jump
  (state 2) can splash. Splash (states 3-5) checked by poking a frog
  into a player jump over the water.
- b2's `screenshot` shows the state from 1-2 frames before a RAM
  peek taken at the same time (the frame shows the state before that
  frame's logic, plus the frame being scanned out). Compare
  screenshots with RAM only when the game state is steady, or allow
  for that. With b2 set to draw fewer frames when it's in the
  background, screenshots can be much staler (a third of a second or
  more): b2 must be set to draw every frame for these checks.

Milestone 3 notes:
- Split into three steps, each tested and committed separately:
  flies, tongue (including sharing the logic half of
  `prepare_display`), then collision and score.
- Kernel timing: loop iteration y starts at cycle 33 of BBC line
  167-2y and takes exactly 152 cycles (2 lines). This came from the
  PF2/PF1 write positions measured against Stella (x 100 and 132). It
  also gives the frog formula, and shows objects can only appear on
  lines 22-167 (milestone 2 clipped to 21-168, which only mattered
  while a frog was sinking).
- Flies are missiles: 4 px wide on kernel lines `mi_y-2..mi_y-1` when
  `byte_B3` bit 1 is clear, otherwise 2 px wide on `mi_y-2..mi_y`
  (selector table page $FF instead of $FE) and 2 px right if moving
  right. Screen X is `mi_x` (TIA missiles start a clock before
  players). The kernel writes ENAM0 at beam x 94 and ENAM1 at x 118,
  so a missile left of its write point appears a line lower; the
  flies swap between M0 and M1 every frame, so between x 94 and 118 a
  fly jitters by a line, as on the 2600. Consistent with the Stella
  snapshot (both 4x4 flies start on even lines, which only the
  "left of the write" case gives), but not checked against Stella
  with known `mi_x`/`mi_y`.
- Tongue (step 2): `prepare_display` is now shared
  (`src/prepare_display.s65`), with its TIA setup in `.if
  TARGET==TARGET_2600` blocks. On the BBC it records the tongue's frog
  `pl_y` (`tongue_pl_y`, 0 for none) and ball X (`tongue_x`) instead
  of positioning the ball. The BBC's copy of the colour code
  (`prepare_colours`) is gone. When the 2600 code swaps the BG/PF
  colours (`pf_eor_value`=$ff, end sequence flicker), the BBC palette
  reads the role sources swapped back, so the picture stays the same
  and the tongue and score area change as on the 2600. Not seen yet:
  it only happens in the end sequence (milestone 4).
- The tongue is the ball: 8x2 on kernel line `pl_y-3`, at screen X
  `tongue_x` (like a missile), a line lower if left of the ENABL write
  (beam x 70). Its colour is COLUPF of the band of kernel line
  `pl_y-2` (the kernel sets COLUPF for a line at the start of the line
  below). In the lily pad band that's the pads' colour, so a sitting
  frog's tongue hardly shows over a pad, as on the 2600. Fire checked
  by poking INPT4 with a frog parked mid-air: tongue out for ~0.36s,
  both facings, both sides of x 70.
- Collision (step 3): `sub_F6BE` is unchanged. After drawing,
  `check_collisions` tests the tongue's rectangle against each fly's
  (as drawn, after clipping) and sets bit 6 of CXM0FB or CXM1FB for
  whichever missile drew that fly, like the TIA latch. `sub_F6BE`
  then maps it back to a fly with `eor byte_B3`, skips hits over the
  frog's body, adds 2 to the score and resets the fly, as on the
  2600. To keep the tongue and frogs from the same frame, the main
  loop now runs `sub_F6BE` and `prepare_display` just before drawing
  (previously the tongue was drawn a frame behind the frogs).
  Checked by poking: hits score 2 with fire in pro mode, and
  automatically in amateur mode; no hit over the frog's body, out of
  reach, or two lines off. Attract mode scores by itself.
- Render timing, measured properly now with User VIA T2 (the T1-based
  figures in milestone 2 were too low: when rendering ran past vsync,
  the vsync event restarted T1 mid-render): 4.4-9.6ms with two frogs
  and two flies, most when both frogs jump. Rendering now starts when
  the beam passes line 168 (no sprites below 167) rather than 192.
  The deadline for something on the top sprite line (22) is then
  ~10.6ms; flies are drawn first, and frogs, drawn last, are rarely
  above line 71 (deadline ~13.8ms). Flies only save and draw the byte
  columns they need (1-3). Still worth watching as more is drawn:
  with the tongue the worst seen is 10.7ms, just over the line 22
  deadline (only a sprite that high and drawn late would be caught).
- Not copied: a missile straddling its write point is split into a
  staircase on the 2600; the BBC treats the whole fly by its left edge.
  And ENAM isn't cleared when the kernel loop ends, so on the 2600 a
  fly at `mi_y` 2-3 would streak down to the bottom of the picture.

Tooling:
- `make run` builds and runs the `.ssd` in b2. `make screenshot`
  saves b2's display (border included) to `build/beeb-screen.png`
  using b2's `screenshot` endpoint.
- Vertical position: R7=32 puts the picture as near centre as whole
  character rows allow (90px of border above, 104px below in b2's
  576-line output).
- Possible for milestone 2: py65 (`pip3 install --user py65`) for
  headless frame-by-frame RAM comparison of the 2600 logic against the
  BBC build.
