include Python.mk
PROJECT = libcurses
COV_FAIL_UNDER = 18
lint :: mypy
doc :: mkdoc-readme
.PHONY: mkdoc-readme
mkdoc-readme:
	pdm run ./mkdoc $(PROJECT) >README.md
