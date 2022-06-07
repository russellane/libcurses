"""Get Line."""

import curses
import curses.ascii

from loguru import logger

from libcurses.core import is_fkey
from libcurses.getkey import getkey
from libcurses.mouse import Mouse


def getline(win):
    """Return line of input from window."""

    # pylint: disable=too-many-branches

    y, x = win.getyx()
    line = ""

    while True:
        if not (key := getkey(win, no_mouse=True)):
            return None

        if key in (curses.ascii.LF, curses.ascii.CR, curses.KEY_ENTER):
            for _ in range(len(line)):
                win.addstr(chr(curses.ascii.BS))
                win.delch()
            return line

        if key == curses.ascii.BS:
            if line:
                line = line[:-1]
                win.addstr(chr(key))
                win.delch()

        elif key == curses.ascii.NAK:
            while line:
                line = line[:-1]
                win.addstr(chr(curses.ascii.BS))
                win.delch()

        elif key == curses.KEY_MOUSE:
            Mouse.handle_mouse_event()

        elif is_fkey(key):
            if line:
                win.addstr(y, x, line)

        elif curses.ascii.isprint(key):
            try:
                win.addstr(chr(key))
                line += chr(key)
            except curses.error as err:
                logger.error(f"err={err} locals={locals()}")

        else:
            logger.trace(f"ignoring not isprint key={key!r}")
