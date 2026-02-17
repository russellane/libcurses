# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

libcurses is a Python framework for building multi-threaded, curses-based terminal applications. It provides thread-safe wrappers around standard curses functions, a grid-based window layout system with resizable borders, mouse event handling, and loguru-based logging to curses windows.

Package name: `rlane-libcurses`

## Build Commands

This project uses PDM for dependency management and a Makefile-based build system.

```bash
# Install dependencies
pdm install

# Full build (install deps, lint, test, docs)
make build

# Lint only (black, isort, flake8)
make lint

# Lint with mypy type checking
make lint mypy

# Run tests
make test

# Run single test file
python -m pytest tests/test_grid.py -v

# Run single test function
python -m pytest tests/test_grid.py::test_function_name -v

# Run tests with output visible (no capture)
make pytest_debug

# Format code
make black isort

# Clean build artifacts
make clean
```

## Code Style

- Line length: 97 characters
- Formatting: black + isort (profile: black)
- Type checking: mypy with strict mode enabled
- Docstrings: Google convention (pydocstyle)
- Tests exempt from docstring requirements

## Architecture

### Thread Safety Model

The library makes curses thread-safe through:
- `libcurses.core.LOCK` - A threading lock protecting `curses.doupdate()`
- `libcurses.core.CURSORWIN` - Tracks the last window passed to `getch`
- `preserve_cursor()` - Context manager that saves/restores cursor position atomically

### Key Components

**core.py** - Foundation module with thread-safe wrapper, function key registry, and cursor management
- `wrapper()` - Replacement for `curses.wrapper()` that initializes thread-safety primitives
- `register_fkey()` - Register callbacks for function keys (handlers stored in `FKEYS` dict by key code)
- `preserve_cursor()` - Context manager using LOCK for atomic cursor operations

**grid.py** - Window layout system
- `Grid` class manages a collection of windows with collapsed/shared borders
- Windows positioned via spatial relationships (left, right, top, bottom, left2r, right2l, etc.)
- Interactive border resizing via mouse drag or double-click + arrow keys
- Handles KEY_RESIZE events to rebuild grid when terminal resizes

**mouse.py / mouseevent.py** - Mouse event handling
- `Mouse` class manages event handlers at specific (y, x) coordinates
- `MouseEvent` wraps `curses.getmouse()` with convenient properties (button, nclicks, is_pressed, etc.)
- Internal handlers (for Grid resizing) vs application handlers (coordinate-based)

**getkey.py / getline.py** - Input functions
- `getkey()` - Thread-safe character input with automatic mouse event dispatch
- `getline()` - Line input with backspace, Ctrl-U, mouse handling, and function key support

**logsink.py** - Loguru integration
- `LogSink` class creates a loguru sink that writes to a curses window
- Supports dynamic level changes, location format cycling, and column padding

**colormap.py** - Maps loguru level names to curses color/attribute pairs

### Module Dependencies

```
core.py (foundation - no libcurses imports)
    ↑
getkey.py (imports core, mouse)
    ↑
getline.py (imports core, getkey, mouse)
    ↑
grid.py (imports core, getkey, mouse)

logsink.py (imports core, colormap)
```

## Testing

Tests are in `tests/`. The example application `tests/test_app.py` demonstrates all major features and can be run directly:

```bash
python tests/test_app.py
```

Coverage threshold: 18% (set in Makefile as COV_FAIL_UNDER)
