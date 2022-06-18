"""Docstring."""

import curses
import threading
from enum import Enum
from queue import SimpleQueue

from loguru import logger

import libcurses


class ConsoleMessageType(Enum):
    """Types of messages sent through `SimpleQueue` to application."""

    GETCH = "getch"  # single character (`int`) read from curses.
    GETLINE = "getline"  # line (`str`) read from curses.
    LOGGER = "logger"  # logger message to be displayed by curses.


GETCH = ConsoleMessageType.GETCH.value
GETLINE = ConsoleMessageType.GETLINE.value
LOGGER = ConsoleMessageType.LOGGER.value

# ConsoleMessage = namedtuple("conmsg", "msgtype seq data")


class Console:
    """Docstring."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        logwin: curses.window,
        pre_block,
        dispatch,
        queue: SimpleQueue = None,
    ) -> None:
        """Start thread to read keyboard/mouse and push characters to application."""

        # Only `main_thread` may use `logwin`; others are prohibited.
        self.main_thread = threading.current_thread()
        self.logwin = logwin
        self.logwin.keypad(True)

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

        # Workers send messages to `main_thread`.
        self.queue = queue or SimpleQueue()

        #
        self.lineno = 0
        self.debug = False

        # Configure logger.
        self.location = "{name}.{function}:{line}"
        self.verbose = 0
        self._level_name = "INFO"
        self._id = None
        self._config()

        # Start thread to loop over `logwin.getch()` forwarding each
        # character to the REPL input generator `get_msgtype_lineno_line`.
        threading.Thread(target=self.getch, name=GETCH, daemon=True).start()

        # REPL
        # >>>  for msgtype, lineno, line in console.get_msgtype_lineno_line:
        # >>>      print(line)

    def getch(self) -> None:
        """Forward keyboard/mouse characters to `get_msgtype_lineno_line`."""

        while True:
            # This is the only caller of `getch`; others are prohibited.
            char = self.logwin.getch()
            self.queue.put((GETCH, 0, char))
            if char < 0:
                return

    def _config(self) -> None:

        if self._id is not None:
            # Loguru can't actually change the format of an active logger;
            # remove and recreate.
            logger.trace(f"remove logger {self._id}")
            logger.remove(self._id)

        self._id = logger.add(
            self._sink,
            level=self._level_name,
            format="|".join(
                [
                    "{time:HH:mm:ss.SSS}",
                    self.location,
                    "{level}",
                    "{message}{exception}",
                ]
            ),
        )

        logger.trace(f"add logger {self._id} location {self.location!r}")

    def _sink(self, msg) -> None:

        level = msg.record["level"].name

        if self.main_thread == threading.current_thread():
            color = self.colormap[level]
            self.logwin.addstr(msg, color)
            self.logwin.refresh()
        else:
            self.queue.put((LOGGER, 0, level, msg))

    def set_location(self, location) -> None:
        """Set format of `location` field."""

        self.location = location if location is not None else ""
        self._config()
        logger.trace(f"update location={self.location!r}")

    def set_verbose(self, verbose: int) -> None:
        """Set logging level based on `--verbose`."""

        self.verbose = verbose
        #   ["",     "-v",    "-vv"]
        _ = ["INFO", "DEBUG", "TRACE"]
        self._level_name = _[min(verbose, len(_) - 1)]
        self._config()
        logger.trace(f"update verbose={self._level_name!r}")

    def get_msgtype_lineno_line(self) -> str:
        """Yield messages from console and application feeds.

        Thread `self._getch` puts GETCH messages onto the queue.
        We buffer chars until ENTER, then yield msgtype GETLINE.

        Application feeds also put messages onto this queue, which we simply forward.

        We intercept the `LOGGER` feed and write directly to curses `logwin`;
        might be better to simply forward it... then maybe this doesn't
        need `logwin` at all?

        """

        # pylint: disable=too-many-branches

        _line = ""  # collect keys until Enter.

        while True:

            # Flush output, redisplay prompt, ...
            self.pre_block(_line)

            # Wait for keystroke... or other msgtype
            try:
                (msgtype, seq, *args) = self.queue.get()
            except KeyboardInterrupt as err:
                logger.info(repr(err))
                return

            if self.debug:
                logger.trace("msgtype {} seq {} args {}", msgtype, seq, args)

            # Dispatch.

            if msgtype == ConsoleMessageType.LOGGER.value:
                (level, msg) = args
                color = self.colormap[level]
                self.logwin.addstr(msg, color)
                continue

            if msgtype != ConsoleMessageType.GETCH.value:
                # yield msgtype, seq, *args
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
                logger.trace("key {} keyname {}", key, keyname)

            if key == curses.ascii.EOT:
                logger.info(keyname)
                return

            if key in (curses.ascii.LF, curses.ascii.CR, curses.KEY_ENTER):
                self.lineno += 1
                yield GETLINE, self.lineno, _line
                _line = ""

            elif key == curses.ascii.BS:
                if _line:
                    _line = _line[:-1]

            elif key == curses.ascii.NAK:
                _line = ""

            elif curses.ascii.isprint(key):
                _line += chr(key)

            elif not libcurses.is_fkey(key) and self.debug:
                logger.trace("Unhandled key {} keyname {}", key, keyname)

    def toggle_debug(self, key: int) -> None:
        """Change `debug`; signature per `libcurses.register_fkey`."""

        self.debug = not self.debug
        if self.debug:
            logger.trace("key {} debug {}", key, self.debug)
