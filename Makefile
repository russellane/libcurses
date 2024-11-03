include Python.mk
PROJECT = libcurses
COV_FAIL_UNDER = 18
lint :: mypy
doc :: README.md
README.md:
	./mkdoc $(PROJECT) >$@
