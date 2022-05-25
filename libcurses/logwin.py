"""Curses Logger."""

import curses
import re
import sys

from loguru import logger

import libcurses.core


class LoggerWindow:
    """Logger sink display to curses window."""

    # Map each loguru level name to a curses color/attr
    colormap = {}  # key=loguru level name, value=curses color/attr

    def __init__(self, win):
        """Create logger window."""

        self._win = win  # logger window
        self._level_name = "INFO"
        self._gutter = "│"  # split messages on this separater

        self._location = "{file}:{line}:{function}"
        self._padding_location = 0  # column alignment
        self._padding_level = 0  # column alignment

        self._win.scrollok(True)
        self._win.idlok(True)
        self._win.leaveok(False)

        colors = {  # key=loguru color name, value=curses color
            "black": curses.COLOR_BLACK,
            "blue": curses.COLOR_BLUE,
            "cyan": curses.COLOR_CYAN,
            "green": curses.COLOR_GREEN,
            "magenta": curses.COLOR_MAGENTA,
            "red": curses.COLOR_RED,
            "white": curses.COLOR_WHITE,
            "yellow": curses.COLOR_YELLOW,
        }

        attrs = {  # key=loguru attr name, value=curses attr
            "bold": curses.A_BOLD,
            "dim": curses.A_DIM,
            "normal": curses.A_NORMAL,
            "hide": curses.A_INVIS,
            "italic": curses.A_ITALIC,
            "blink": curses.A_BLINK,
            "strike": curses.A_HORIZONTAL,
            "underline": curses.A_UNDERLINE,
            "reverse": curses.A_REVERSE,
        }

        for idx, lvl in enumerate(logger._core.levels.values()):
            fg = curses.COLOR_WHITE
            bg = curses.COLOR_BLACK
            attr = 0
            for word in re.findall(r"[\w]+", lvl.color):
                if word.islower() and (_ := colors.get(word)):
                    fg = _
                elif word.isupper() and (_ := colors.get(word.lower())):
                    bg = _
                elif _ := attrs.get(word):
                    attr |= _

            curses.init_pair(idx + 1, fg, bg)
            self.__class__.colormap[lvl.name] = curses.color_pair(idx + 1) | attr
            logger.trace(
                f"name={lvl.name} color={lvl.color} idx={idx+1} fg={fg} bg={bg} "
                f"color={self.colormap[lvl.name]} attr={attr:o}"
            )

        #
        self._logger_id = None
        self._init_logger()

    def _init_logger(self) -> None:

        if self._logger_id is not None:
            # Loguru can't actually change the format of an active logger;
            # remove and recreate.
            logger.trace(f"remove _logger_id {self._logger_id}")
            logger.remove(self._logger_id)
            self._padding_location = 0
            self._padding_level = 0

        self._logger_id = logger.add(
            self._curses_sink,
            level=self._level_name,
            format=self._gutter.join(
                [
                    "{time:HH:mm:ss.SSS}",
                    self._location,
                    "{level}",
                    "{message}{exception}",
                ]
            ),
        )

        logger.trace(f"add _logger_id {self._logger_id} _location {self._location!r}")

    def set_location(self, location):
        """Set the location format.

        Args:
            location:   `loguru` format string to format the location section of each
                        message. For example, "{thread.name}:{file}:{line}:{function}".
        """

        self._location = location if location is not None else ""
        self._init_logger()

    def set_verbose(self, verbose: int):
        """Set logging level based on `--verbose`."""

        _ = ["INFO", "DEBUG", "TRACE"]
        self._level_name = _[min(verbose, len(_) - 1)]
        self._init_logger()

    def _curses_sink(self, msg):

        time, location, level, message = msg.split(self._gutter, maxsplit=3)
        color = self.colormap[level]

        w = len(location)
        self._padding_location = max(self._padding_location, w)
        location += " " * (self._padding_location - w)

        w = len(level)
        self._padding_level = max(self._padding_level, w)
        level += " " * (self._padding_level - w)

        with libcurses.core.LOCK:

            y, x = (
                libcurses.core.CURSORWIN.getyx() if libcurses.core.CURSORWIN else curses.getsyx()
            )

            if sum(self._win.getyx()):
                self._win.addch("\n")
            self._win.addstr(time, color)
            self._win.addch(curses.ACS_VLINE)

            if location:
                self._win.addstr(location, color)
                self._win.addch(curses.ACS_VLINE)

            self._win.addstr(level, color)
            self._win.addch(curses.ACS_VLINE)
            self._win.addstr(message.rstrip(), color)
            self._win.refresh()

            if libcurses.core.CURSORWIN:
                try:
                    libcurses.core.CURSORWIN.move(y, x)
                except curses.error as err:
                    print(f"y={y} x={x} err={err}", file=sys.stderr)
                libcurses.core.CURSORWIN.refresh()
            else:
                curses.setsyx(y, x)

            curses.doupdate()
