"""Get Key.

This module provides the `getkey` function.
"""

import curses
import curses.ascii

from loguru import logger

import libcurses.core
from libcurses.mouse import Mouse

__all__ = ["getkey"]


def getkey(win: curses.window | None = None, no_mouse: bool = False) -> int | None:
    """Read and return a character from window.

    Args:
        win: curses window to read from.
        no_mouse: ignore mouse events (for internal use).

    Return:
        -1 when no-input in no-delay mode, or
        None on end of file, or
        >=0 int character read.
    """

    with libcurses.core.LOCK:
        if win is None:
            assert libcurses.core.CURSORWIN
            win = libcurses.core.CURSORWIN
        libcurses.core.CURSORWIN = win

    while True:
        try:
            win.noutrefresh()
            with libcurses.core.LOCK:
                curses.doupdate()
            key: int = win.getch()
            if key < 0:
                return key

            keyname = curses.keyname(key).decode()
            logger.trace("key {}={!r}", key, keyname)

            if not no_mouse and key == curses.KEY_MOUSE:
                Mouse.handle_mouse_event()
                continue

            # pylint: disable=no-member
            if key == curses.KEY_RESIZE and curses.is_term_resized(curses.LINES, curses.COLS):
                curses.update_lines_cols()

            return None if key == curses.ascii.EOT else key

        except KeyboardInterrupt:
            return None
