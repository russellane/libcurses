"""Logger sink to curses window.

This module provides the `LogSink` class.
"""

import curses

from loguru import logger

import libcurses.core
from libcurses.colormap import get_colormap

__all__ = ["LogSink"]


class LogSink:
    """Logger sink to curses window.

    The `LogSink` class provides a logger destination that writes log
    messages to a curses window, and methods that control various
    logging features.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, logwin: curses.window) -> None:
        """Begin logging to `logwin`."""

        self.logwin = logwin
        self.level = "INFO"
        self.location = "{name}.{function}:{line}"
        self.delim = "|"

        self._id: int | None = None
        self._padlev = 0  # pad `level` column.
        self._padloc = 0  # pad `location` column.

        self.logwin.idlok(True)
        self.logwin.leaveok(False)
        self.logwin.scrollok(True)

        self._colormap = get_colormap()
        self._config()

    def reset_padding(self) -> None:
        """Reset column padding."""

        self._padloc = 0
        self._padlev = 0

    def set_level(self, level: str) -> None:
        """Set logging level."""

        self.level = level
        self._config()
        logger.info(self.level)
        self.reset_padding()

    def set_location(self, location: str | None = None) -> None:
        """Set format of `location` field."""

        self.location = location or ""
        self._config()
        logger.info(repr(self.location))
        self.reset_padding()

    def set_verbose(self, verbose: int) -> int:
        """Set logging level based on `--verbose`."""

        #         ["",     "-v",    "-vv"]
        _levels = ["INFO", "DEBUG", "TRACE"]
        self.set_level(_levels[min(verbose, len(_levels) - 1)])
        return verbose

    def _config(self) -> None:
        """Not public."""

        if self._id is not None:
            # Loguru can't actually change the format of an active logger;
            # remove and recreate.
            logger.trace("remove logger {}", self._id)
            logger.remove(self._id)
            self.reset_padding()

        self._id = logger.add(
            self._sink,
            level=self.level,
            format=self.delim.join(
                [
                    "{time:HH:mm:ss.SSS}",
                    self.location,
                    "{level}",
                    "{message}{exception}",
                ]
            ),
        )

        logger.trace("add logger {} location {!r}", self._id, self.location)

    def _sink(self, msg: str) -> None:
        """Not public."""

        delim = self.delim
        time, location, level, message = msg.split(delim, maxsplit=3)
        color = self._colormap[level]

        _len = len(location)
        self._padloc = max(self._padloc, _len)
        location += " " * (self._padloc - _len)

        _len = len(level)
        self._padlev = max(self._padlev, _len)
        level += " " * (self._padlev - _len)

        win = self.logwin

        with libcurses.core.preserve_cursor():

            if sum(win.getyx()):
                win.addch("\n")
            win.addstr(time, color)
            win.addch(delim)

            if location:
                win.addstr(location, color)
                win.addch(delim)

            win.addstr(level, color)
            win.addch(delim)
            win.addstr(message.rstrip(), color)
            win.refresh()
