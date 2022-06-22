# russellane/Python.mk

build::		__pypackages__ tags lint test doc
		pdm build

lint::		black isort flake8
test::		pytest
doc::		;

bump_micro::	_bump_micro clean build
_bump_micro:
		pdm bump micro

publish_local::
		cd dist; echo *.whl | cpio -pdmuv `pip config get global.find-links`

publish_test::
		twine upload --verbose -r testpypi dist/*

publish_prod::
		twine upload --verbose -r pypi dist/*

install::
		-pipx uninstall $(PROJECT)
		pipx install $(PROJECT)

__pypackages__:
		pdm install

.PHONY:		tags
tags::
		ctags -R $(PROJECT) sample_app tests __pypackages__ 

black::
		python -m black -q $(PROJECT) sample_app tests

isort::
		python -m isort $(PROJECT) sample_app tests

flake8::
		python -m flake8 $(PROJECT) sample_app tests

pytest::
		python -m pytest --exitfirst --showlocals --verbose sample_app tests

pytest_debug::
		python -m pytest --exitfirst --showlocals --verbose --capture=no sample_app tests

coverage::
		python -m pytest --cov=$(PROJECT) sample_app tests

cov_html::
		python -m pytest --cov=$(PROJECT) --cov-report=html sample_app tests
		xdg-open htmlcov/index.html

clean::
		rm -rf .coverage .pytest_cache __pypackages__ dist htmlcov tags 
		find . -type f -name '*.py[co]' -delete
		find . -type d -name __pycache__ -delete

# put `doc :: README.md` into Makefile, if desired
.PHONY:		README.md
README.md:
		python -m $(PROJECT) --md-help >$@

# vim: set ts=8 sw=8 noet:
