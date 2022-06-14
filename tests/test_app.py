"""Example multi-threaded curses application."""

import curses
import itertools
import threading
import time
from queue import SimpleQueue

from loguru import logger

import libcurses


def test_stub():
    """Make pytest happy with something to do; when in a test directory."""


class Application:
    """Example multi-threaded curses application."""

    def __init__(self, stdscr: curses.window):
        """Docstring."""

        # Remove bold from loguru default colors
        for lvl in logger._core.levels.values():
            logger.level(lvl.name, color=lvl.color.replace("<bold>", ""))
        # Create custom logging levels here...

        # Application data here...

        # Example of how to reconfigure logger on the fly; (not required)
        self.verbose = itertools.cycle([2, 1, 0])  # ["-vv", "-v", ""]
        self.location = itertools.cycle(
            [
                "{module}:{line}",
                "{file}:{line}:{function}",
                "{thread.name}:{file}:{line}:{function}",
                "{name}:{function}:{line}",
                None,
            ]
        )

        # Split screen horizontally into 2 panels.
        self.grid = libcurses.Grid(stdscr)

        # upper panel
        self.mainwin = self.grid.box(
            "mainwin",
            nlines=self.grid.nlines // 2,
            ncols=0,
            left=self.grid,
            right=self.grid,
            top=self.grid,
        )
        self.mainwin.scrollok(True)

        # lower panel
        self.logwin = self.grid.box(
            "logwin",
            nlines=0,
            ncols=0,
            left=self.grid,
            right=self.grid,
            top2b=self.mainwin,
            bottom=self.grid,
        )
        self.logwin.scrollok(True)

        # Start curses threading.
        self.console = libcurses.Console(
            stdscr=stdscr,
            logwin=self.logwin,
            pre_block=self.pre_block,
            dispatch=self.dispatch,
        )

        # Add an application data feed.
        # This one generates logger messages every `x` seconds.
        timer = TimerFeed(self.console.queue)

        # F3 instructs TimerFeed to change value of `x`.
        libcurses.register_fkey(timer.next_timer, curses.KEY_F3)

        # Configure logger to forward log messages to application.
        # Message: ("LOGGER", level, msg)
        sink = libcurses.LoggerSink(self.console.queue)

        sink.set_location(next(self.location))
        libcurses.register_fkey(
            lambda key: sink.set_location(next(self.location)), curses.KEY_F1
        )

        sink.set_verbose(next(self.verbose))
        libcurses.register_fkey(lambda key: sink.set_verbose(next(self.verbose)), curses.KEY_F2)

        sink.win = self.logwin
        self.grid.redraw()

    def main(self):
        """Docstring."""

        # REPL
        for line in self.console.getline():
            # Work...
            self.logwin.addstr(f"line={line!r}\n")

    def pre_block(self, _line: str) -> None:

        # Flush output.
        self.logwin.refresh()
        self.mainwin.clear()
        self.mainwin.move(0, 0)
        self.mainwin.addstr("CMD: " + _line)
        self.mainwin.refresh()

    def dispatch(self, msgtype: str, *args) -> None:

        logger.error(f"dispatch: msgtype={msgtype!r} args={args!r}\n")

        if msgtype == "TIMER":
            (line,) = args
            self.logwin.addstr(f"Timer: msgtype={msgtype!r} line={line!r}\n")
            return

        if msgtype == libcurses.ConsoleMessageType.GETCH.value:
            (char,) = args
            self.logwin.addstr(f"GETCH: msgtype={msgtype!r} char={char!r}\n")
            return

        raise ValueError(f"invalid msgtype={msgtype!r} args={args!r}")


class TimerFeed:
    """Example application data feed."""

    name = "TIMER"

    def __init__(self, queue: SimpleQueue):
        """Start feed to use logger periodically, default every 3 seconds."""

        self.queue = queue
        self._timer = itertools.cycle([3, 2, 1])
        self.timer = self.next_timer(None)

        threading.Thread(target=self.work, name=self.name, daemon=True).start()

    def next_timer(self, key: int) -> int:
        """Cycle to next value.

        Signature for call from `libcurses.register_fkey`.
        """

        self.timer = next(self._timer)
        logger.trace(f"key={key} timer={self.timer}")
        return self.timer

    def work(self) -> None:
        """Simulate some external event."""

        while True:
            time.sleep(self.timer)
            msg = f"Timer {self.timer} time {time.asctime()}"
            self.queue.put((self.name, msg))
            logger.error("error " + msg)
            logger.warning("warning " + msg)
            logger.info("info " + msg)
            logger.debug("debug " + msg)
            logger.trace("trace " + msg)


if __name__ == "__main__":
    libcurses.wrapper(lambda stdscr: Application(stdscr).main())
