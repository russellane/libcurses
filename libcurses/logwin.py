"""Curses Logger."""

import curses
import sys

from loguru import logger

import libcurses.core
from libcurses.colormap import get_colormap


class LoggerWindow:
    """Logger sink display to curses window."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, win):
        """Create logger window."""

        self._colormap = get_colormap()
        self._win = win  # logger window
        self._level_name = "INFO"
        self._msg_delim = "|"
        self._display_delim = "|"

        self._location = "{file}:{line}:{function}"
        self._padding_location = 0  # column alignment
        self._padding_level = 0  # column alignment

        self._win.scrollok(True)
        self._win.idlok(True)
        self._win.leaveok(False)

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
            format=self._msg_delim.join(
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

        time, location, level, message = msg.split(self._msg_delim, maxsplit=3)
        color = self._colormap[level]

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
            self._win.addch(self._display_delim)

            if location:
                self._win.addstr(location, color)
                self._win.addch(self._display_delim)

            self._win.addstr(level, color)
            self._win.addch(self._display_delim)
            self._win.addstr(message.rstrip(), color)
            self._win.noutrefresh()

            if libcurses.core.CURSORWIN:
                try:
                    libcurses.core.CURSORWIN.move(y, x)
                except curses.error as err:
                    print(f"y={y} x={x} err={err}", file=sys.stderr)
                libcurses.core.CURSORWIN.noutrefresh()
            else:
                curses.setsyx(y, x)

            curses.doupdate()
