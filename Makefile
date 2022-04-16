# -*- mode:makefile-gmake; -*-

TASS:=64tass
PYTHON3:=python3

##########################################################################
##########################################################################

TASSCMD:=$(TASS) --m65xx -C -Wall --line-numbers
SHELLCMD:=$(PYTHON3) $(realpath submodules/shellcmd.py/shellcmd.py)
BEEB_DEST:=$(abspath ./beeb/1)
BUILD:=$(abspath ./build)

##########################################################################
##########################################################################

.PHONY:build
build:
	$(SHELLCMD) mkdir "$(BEEB_DEST)"
	$(SHELLCMD) mkdir "$(BUILD)"

	$(TASS) fnf-2600.s65 --nostart "--list=$(BUILD)/fnf-2600.lst" "--output=$(BUILD)/fnf-2600.bin"
	@$(SHELLCMD) sha1 "$(BUILD)/fnf-2600.bin"
	@$(SHELLCMD) sha1 "Frogs and Flies (USA).a26"


##########################################################################
##########################################################################
