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
build: _folders 2600 beeb

.PHONY:2600
2600: _folders
	$(_V)$(TASS) -DPAL=false fnf-2600.s65 --nostart "--list=$(BUILD)/fnf-2600.lst" "--output=$(BUILD)/fnf-2600.bin"
	$(_V)$(TASS) -DPAL=true fnf-2600.s65 --nostart "--list=$(BUILD)/fnf-2600.pal.lst" "--output=$(BUILD)/fnf-2600.pal.bin"
#	$(_V)$(SHELLCMD) sha1 "Frogs and Flies (USA).a26"
#	$(_V)$(SHELLCMD) sha1 "$(BUILD)/fnf-2600.bin"
	$(_V)$(SHELLCMD) -v cmp "$(BUILD)/fnf-2600.bin" "Frogs and Flies (USA).a26"
	$(_V)$(SHELLCMD) -v cmp "$(BUILD)/fnf-2600.pal.bin" "Frogs and Flies (Telegames) (PAL).bin"

BEEB_SSD:=$(BUILD)/fnf-beeb.ssd
BEEB_LOAD:=0x1900

.PHONY:beeb
beeb: _folders
	$(_V)$(PYTHON) ./tools/make_tia_to_beeb.py "$(BUILD)/tia_to_beeb.s65"
	$(_V)$(TASS) fnf-beeb.s65 -I "$(BUILD)" --nostart "--list=$(BUILD)/fnf-beeb.lst" "--labels=$(BUILD)/fnf-beeb.labels" "--output=$(BEEB_DEST)/$$.FNF"
	$(_V)$(PYTHON) ./tools/make_beeb_files.py --load=$(BEEB_LOAD) --name=FNF --boot="MODE 2" --boot="*RUN FNF" "$(BEEB_DEST)/$$.FNF"
	$(_V)$(PYTHON) ./submodules/beeb/bin/ssd_create.py -o "$(BEEB_SSD)" --dir "$(BEEB_DEST)" "$(BEEB_DEST)/$$.!BOOT" "$(BEEB_DEST)/$$.FNF"

# Run the BBC version in b2 (which must be running, with its HTTP
# server enabled).
.PHONY:run
run: beeb
	$(_V)curl --fail-with-body --silent --show-error -H "Content-Type:application/binary" --upload-file "$(BEEB_SSD)" "http://localhost:48075/run/b2?name=fnf-beeb.ssd"

# Grab the BBC screen from b2 as a PNG.
.PHONY:screenshot
screenshot: _folders
	$(_V)$(PYTHON) ./tools/b2_screenshot.py "$(BUILD)/beeb-screen.png"

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
