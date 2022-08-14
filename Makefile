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
build: _folders
	$(TASS) fnf-2600.s65 --nostart "--list=$(BUILD)/fnf-2600.lst" "--output=$(BUILD)/fnf-2600.bin"
	@$(SHELLCMD) sha1 "Frogs and Flies (USA).a26"
	@$(SHELLCMD) sha1 "$(BUILD)/fnf-2600.bin"
	@cmp -s "Frogs and Flies (USA).a26" "$(BUILD)/fnf-2600.bin"

.PHONY:_folders
_folders:
	$(SHELLCMD) mkdir "$(BEEB_DEST)"
	$(SHELLCMD) mkdir "$(BUILD)"

##########################################################################
##########################################################################

.PHONY:diff
diff:
	vbindiff "$(BUILD)/fnf-2600.bin" "Frogs and Flies (USA).a26"

.PHONY:bgtest
bgtest:
	$(PYTHON3) ./tools/pf_convert.py
	$(PYTHON3) ./submodules/beeb/bin/png2bbc.py build/bg.png 2 -o $(BEEB_DEST)/P.BG --160
