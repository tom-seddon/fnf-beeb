# -*- mode:makefile-gmake; -*-

ifeq ($(OS),Windows_NT)
PYTHON:=py -3
TASSCMD:=bin\64tass.exe
else
PYTHON:=/usr/bin/python3
TASSCMD:=64tass
endif

##########################################################################
##########################################################################

ifeq ($(VERBOSE),1)
_V:=
_TASSQ:=
else
_V:=@
_TASSQ:=-q
endif

TASS:="$(TASSCMD)" --m65xx -C -Wall --line-numbers $(_TASSQ) --verbose-list
SHELLCMD:=$(PYTHON) $(realpath submodules/shellcmd.py/shellcmd.py)
BEEB_DEST:=$(abspath ./beeb/Z)
BUILD:=$(abspath ./build)

##########################################################################
##########################################################################

.PHONY:build
build: _folders
	$(_V)$(TASS) -DPAL=false fnf-2600.s65 --nostart "--list=$(BUILD)/fnf-2600.lst" "--output=$(BUILD)/fnf-2600.bin"
	$(_V)$(TASS) -DPAL=true fnf-2600.s65 --nostart "--list=$(BUILD)/fnf-2600.pal.lst" "--output=$(BUILD)/fnf-2600.pal.bin"
#	$(_V)$(SHELLCMD) sha1 "Frogs and Flies (USA).a26"
#	$(_V)$(SHELLCMD) sha1 "$(BUILD)/fnf-2600.bin"
	$(_V)$(SHELLCMD) -v cmp "$(BUILD)/fnf-2600.bin" "Frogs and Flies (USA).a26"
	$(_V)$(SHELLCMD) -v cmp "$(BUILD)/fnf-2600.pal.bin" "Frogs and Flies (Telegames) (PAL).bin"

.PHONY:_folders
_folders:
	$(_V)$(SHELLCMD) mkdir "$(BEEB_DEST)" "$(BUILD)"

##########################################################################
##########################################################################

.PHONY:diff
diff:
	vbindiff "$(BUILD)/fnf-2600.bin" "Frogs and Flies (USA).a26"

.PHONY:bgtest
bgtest:
	$(_V)$(PYTHON) ./tools/pf_convert.py
	$(_V)$(PYTHON) ./submodules/beeb/bin/png2bbc.py build/bg.png 2 -o $(BEEB_DEST)/P.BG --160

.PHONY:tiapal
tiapal: _folders
	$(_V)$(PYTHON) ./tools/make_tia_palette_pngs.py $(BUILD)

.PHONY:clean
clean:
	$(_V)$(SHELLCMD) rm-tree "$(BUILD)"
