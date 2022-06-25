# rlane-libcurses/Makefile

PROJECT		= libcurses
SOURCES		= $(PROJECT) app.py

build:		__pypackages__ tags lint
		pdm build

__pypackages__:
		pdm install

.PHONY:		tags
tags:
		ctags -R $(SOURCES) __pypackages__ 

lint:		black isort flake8

black:
		python -m black -q $(SOURCES)

isort:
		python -m isort $(SOURCES)

flake8:
		python -m flake8 $(SOURCES)

clean:
		rm -rf __pypackages__ dist tags 
		find . -type f -name '*.py[co]' -delete
		find . -type d -name __pycache__ -delete

bump_micro:	_bump_micro clean build
_bump_micro:
		pdm bump micro

upload:
		twine upload --verbose -r pypi dist/*

# vim: set ts=8 sw=8 noet:
