# frogs and flies

See https://en.wikipedia.org/wiki/Frogs_and_Flies

A disassembly of the Atari 2600 game, and (work in progress) a port to
the BBC Micro. See [beeb-port-plan.md](beeb-port-plan.md) for the port
plan and progress.

# getting the code

This repo uses submodules:

    git clone --recurse-submodules git@github.com:tom-seddon/fnf-beeb

or, in an existing working copy, `git submodule update --init`.

# how to build

## prerequisites

* [64tass](http://tass64.sourceforge.net/) on the PATH (1.60 known to work)
* [Python 3.x](https://www.python.org/) - on macOS/Linux the Makefile
  expects `/usr/bin/python3`
* GNU Make (the macOS-supplied 3.81 is fine)
* Some kind of Unix (this will improve!)

For running the BBC version:

* [b2](https://github.com/tom-seddon/b2), with its HTTP server
  listening on the default port (48075) - see `Tools` > `Options` >
  `HTTP Server`. The build will use it to load and run the BBC version
* [Stella](https://stella-emu.github.io/) is useful for comparing with
  the 2600 original

## build process

Type `make`

The code builds to `build/fnf-2600.bin` and `build/fnf-2600.pal.bin`
in the working copy. The build fails unless these exactly match
`Frogs and Flies (USA).a26` and `Frogs and Flies (Telegames)
(PAL).bin` from the repo.

# source layout

* `fnf-2600.s65` - top level for the 2600 build
* `src/logic.s65`, `src/sound.s65`, `src/ram.s65`, `src/data_*.s65` -
  shared between the 2600 and BBC builds
* `src/tia*.s65`, `src/riot.s65` - 2600 only
* `tools/` - Python scripts for examining the ROM data
* `beeb/0` - BBC-side experiments (BeebLink volume)
