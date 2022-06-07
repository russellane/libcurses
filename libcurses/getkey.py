"""Get Key."""

import curses
import curses.ascii

from loguru import logger

import libcurses.core
from libcurses.mouse import Mouse


def getkey(win, no_mouse: bool = False) -> int:
    """Read a character from window.

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
            win.refresh()
            with libcurses.core.LOCK:
                curses.doupdate()
            key = win.getch()
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
