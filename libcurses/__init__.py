"""Framework and tools for multi-threaded, curses(3)-based, terminal applications.

* Write to screen from multiple threads.

    * Use `libcurses.wrapper` instead of `curses.wrapper`.
    * Use `libcurses.getkey` instead of `curses.getch`.
    * Use `libcurses.getline` instead of `curses.getstr`.
    * Preserve the cursor with context manager `libcurses.preserve_cursor`.

* Register callbacks with `register_fkey` to handle function-keys pressed
  during `getkey` and `getline` processing.

* Register callbacks with `add_mouse_handler` to handle mouse events
  during `getkey` and `getline` processing.

* Manage a logger destination, `LogSink`, to write to a curses window.

* A `Grid` framework.
"""

from libcurses.colormap import get_colormap
from libcurses.core import preserve_cursor, register_fkey, wrapper
from libcurses.getkey import getkey
from libcurses.getline import getline
from libcurses.grid import Grid
from libcurses.logsink import LogSink
from libcurses.mouse import add_mouse_handler, clear_mouse_handlers
from libcurses.mouseevent import MouseEvent

__all__ = [
    "Grid",
    "LogSink",
    "MouseEvent",
    "add_mouse_handler",
    "clear_mouse_handlers",
    "get_colormap",
    "getkey",
    "getline",
    "preserve_cursor",
    "register_fkey",
    "wrapper",
]
