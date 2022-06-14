"""Docstring."""

from loguru import logger
import curses
import threading
from enum import Enum
from queue import SimpleQueue

import libcurses


class ConsoleMessageType(Enum):
    """Types of messages forwarded by `Console` through `SimpleQueue` to application."""

    GETCH = "getch"  # single character (`int`) read from curses.
    LOGGER = "logger"  # logger message to be displayed by curses.


class Console:
    """Docstring."""

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-arguments

    def __init__(
        self,
        stdscr: curses.window,
        logwin: curses.window,
        pre_block,
        dispatch,
        queue: SimpleQueue = None,
    ) -> None:
        """Docstring."""

        self.stdscr = stdscr
        self.logwin = logwin
        self.colormap = libcurses.get_colormap()

        # application hook to flush curses output; or whatever it wants to
        # do with this iteration through the REPL, top of loop, before
        # waiting for next char from console.
        # called before reading each character.
        # this generates keystroke events; getch
        # _hook_getch?
        self.pre_block = pre_block

        # application hook to process result of `getline`.
        # called after reading an ENTER character.
        # this generates line events; getline
        # _hook_getline?
        self.dispatch = dispatch

        # Worker-threads funnel work-orders to the main-thread.
        self.queue = queue or SimpleQueue()

        # Start thread to read keyboard/mouse from `stdscr` and forward
        # each character read to application.

        name = ConsoleMessageType.GETCH.value

        def _getch() -> None:

            self.stdscr.keypad(True)
            while True:
                # This is the only caller of `getch`; others are prohibited.
                char = self.stdscr.getch()
                self.queue.put((name, char))
                if char < 0:
                    return

        threading.Thread(target=_getch, name=name, daemon=True).start()

    def getline(self) -> str:
        """Generate lines read (blocking) from the console."""

        assert self.logwin

        _line = ""  # collect keys until Enter.

        while True:
            # logger.debug("do no call logger.debug, et. al. here")

            self.pre_block(_line)

            # Wait for keystroke.
            (msgtype, *args) = self.queue.get()
            # self.logwin.addstr(f"msgtype={msgtype!r} args={args!r}\n")

            # Dispatch.

            if msgtype == libcurses.ConsoleMessageType.LOGGER.value:
                (level, msg) = args
                color = self.colormap[level]
                self.logwin.addstr(msg, color)
                continue

            if msgtype != libcurses.ConsoleMessageType.GETCH.value:
                self.dispatch(msgtype, *args)
                continue

            (key,) = args
            if key == curses.KEY_MOUSE:
                libcurses.Mouse.handle_mouse_event()
                continue

            keyname = curses.keyname(key).decode()
            self.logwin.addstr(f"key={key} keyname={keyname!r}\n")

            if key == curses.ascii.EOT:
                self.logwin.addstr(keyname + "\n")
                return

            if key in (curses.ascii.LF, curses.ascii.CR, curses.KEY_ENTER):
                yield _line
                _line = ""

            elif key == curses.ascii.BS:
                if _line:
                    _line = _line[:-1]

            elif key == curses.ascii.NAK:
                _line = ""

            elif curses.ascii.isprint(key):
                _line += chr(key)

            elif not libcurses.is_fkey(key):
                self.logwin.addstr(f"Unhandled key={key} keyname={keyname}\n")
