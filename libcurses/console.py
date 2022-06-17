"""Docstring."""

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

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        win: curses.window,
        pre_block,
        dispatch,
        queue: SimpleQueue = None,
        debug: bool = False,
    ) -> None:
        """Start thread to read keyboard/mouse and push characters to application."""

        self.win = win

        # Callback to application to flush curses output; or whatever it
        # wants to do with this iteration through the REPL, top of loop,
        # before waiting for next char from console.

        # called before reading each character.
        # this generates keystroke events; getch
        # _hook_getch?
        # prompt?
        # getline/gotline?
        self.pre_block = pre_block

        # application hook to process result of `getline`.
        # called after reading an ENTER character.
        # this generates line events; getline
        # _hook_getline?
        # getline/gotline?
        self.dispatch = dispatch

        #
        self.colormap = libcurses.get_colormap()

        # Worker-threads funnel work-orders to the main-thread.
        self.queue = queue or SimpleQueue()

        #
        self.debug = debug

        # Configure logger to forward messages to main-thread.
        self.sink = libcurses.LoggerSink(self.queue)

        # Start thread to read keyboard/mouse from `win` and forward
        # each character read to application.

        name = ConsoleMessageType.GETCH.value

        def _getch() -> None:

            self.win.keypad(True)
            while True:
                # This is the only caller of `getch`; others are prohibited.
                char = self.win.getch()
                self.queue.put((name, char))
                if char < 0:
                    return

        threading.Thread(target=_getch, name=name, daemon=True).start()

    def getline(self) -> str:
        """Generate lines read (blocking) from the console."""

        # pylint: disable=too-many-branches

        tag = f"{__name__}.getline:"
        _line = ""  # collect keys until Enter.

        while True:
            # logger.debug("do no call logger.debug, et. al. here")

            self.pre_block(_line)

            # Wait for keystroke.
            try:
                (msgtype, *args) = self.queue.get()
            except KeyboardInterrupt as err:
                if self.debug:
                    self.win.addstr(f"{tag} err={err}\n")
                return

            if self.debug:
                self.win.addstr(f"{tag} msgtype={msgtype!r} args={args!r}\n")

            # Dispatch.

            if msgtype == libcurses.ConsoleMessageType.LOGGER.value:
                (level, msg) = args
                color = self.colormap[level]
                self.win.addstr(msg, color)
                continue

            if msgtype != libcurses.ConsoleMessageType.GETCH.value:
                self.dispatch(msgtype, *args)
                continue

            (key,) = args
            if key == curses.KEY_MOUSE:
                libcurses.Mouse.handle_mouse_event()
                continue

            # if key == curses.KEY_RESIZE and curses.is_term_resized(curses.LINES, curses.COLS):
            #     curses.update_lines_cols()
            #     continue

            keyname = curses.keyname(key).decode()
            if self.debug:
                self.win.addstr(f"{tag} key={key} keyname={keyname!r}\n")

            if key == curses.ascii.EOT:
                self.win.addstr(keyname + "\n")
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

            elif not libcurses.is_fkey(key) and self.debug:
                self.win.addstr(f"{tag} Unhandled key={key} keyname={keyname}\n")

    def toggle_debug(self, key: int) -> None:
        """Change `debug`; signature per `libcurses.register_fkey`."""

        self.debug = not self.debug
        if self.debug:
            self.win.addstr(f"key={key} debug={self.debug}\n")
