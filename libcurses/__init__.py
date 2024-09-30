"""Curses based boxes, menus, loggers."""

from libcurses.colormap import get_colormap
from libcurses.core import preserve_cursor, register_fkey, wrapper
from libcurses.getkey import getkey
from libcurses.getline import getline
from libcurses.grid import Grid
from libcurses.mouse import add_mouse_handler, clear_mouse_handlers
from libcurses.mouseevent import MouseEvent
from libcurses.sink import Sink

__all__ = [
    "get_colormap",
    "preserve_cursor",
    "register_fkey",
    "wrapper",
    "getkey",
    "getline",
    "Grid",
    "add_mouse_handler",
    "clear_mouse_handlers",
    "MouseEvent",
    "Sink",
]
