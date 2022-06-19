"""Example multi-threaded curses application."""

import curses
import itertools
import sys

from loguru import logger

from libcurses import Console, Grid, register_fkey, wrapper
from tests.feeds.file import FileFeed
from tests.feeds.letter import LetterFeed
from tests.feeds.number import NumberFeed

try:
    logger.remove(0)
except ValueError:
    ...
logger.add(sys.stderr, format="{level} {function} {line} {message}", level="TRACE")


class Application:
    """Example multi-threaded curses application.

    Process data from 4 inputs:
        1. Lines ENTER'ed into the keyboard.
        2. Lines tailing a file.
        3. Letters from a LetterFeed.
        4. Numbers from a NumberFeed.

    Also binds some function-keys to control the feeds.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, stdscr: curses.window):
        """Docstring."""

        # Configure logger...
        # Remove bold from default levels.
        for lvl in logger._core.levels.values():
            logger.level(lvl.name, color=lvl.color.replace("<bold>", ""))
        # Add custom logging levels...
        # Set severity of custom levels relative to builtins.
        _warn = logger.level("WARNING").no
        # _info = logger.level("INFO").no
        # _debug = logger.level("DEBUG").no
        # _trace = logger.level("TRACE").no
        _always = _warn
        logger.level("GETLINE", no=_always, color="<cyan>")
        logger.level("FILE", no=_always, color="<blue>")
        logger.level("LETTER", no=_always, color="<yellow>")
        logger.level("NUMBER", no=_always, color="<green>")

        # Application data here...
        self.lastline = None  # for menu to display last line entered.

        # Example of how to reconfigure logger on the fly; (not required)
        self.verbose = itertools.cycle([2, 1, 0])  # ["-vv", "-v", ""]
        self.location = itertools.cycle(
            [
                "{thread.name}.{name}.{function}:{line}",
                "{name}.{function}:{line}",
                "{module}:{function}:{line}",
                "{file}:{line}:{function}",
                None,
            ]
        )

        # Split screen horizontally into 2 panels.
        self.grid = Grid(stdscr)

        # Upper panel: menu/prompt, command line input.
        self.mainwin = self.grid.box(
            "mainwin",
            nlines=self.grid.nlines // 2,
            ncols=0,
            left=self.grid,
            right=self.grid,
            top=self.grid,
        )
        self.mainwin.scrollok(True)

        # Lower panel: logger messages.
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
        self.console = Console(
            logwin=self.logwin,
            refresh=self.refresh,
            dispatch=self.dispatch,
        )

        # Add an application data feed.
        self.numbers = NumberFeed(self.console.queue)
        # speed control
        register_fkey(self.numbers.next_timer, curses.KEY_F1)
        # debug control
        register_fkey(self.numbers.toggle_debug, curses.KEY_F2)

        # Add another application data feed.
        self.letters = LetterFeed(self.console.queue)
        register_fkey(self.letters.next_timer, curses.KEY_F3)
        register_fkey(self.letters.toggle_debug, curses.KEY_F4)

        # Add another application data feed.
        # self.filefeed = FileFeed(self.console.queue, "3lines", rewind=True, follow=False)
        # self.filefeed = FileFeed(self.console.queue, "/etc/passwd", rewind=True, follow=False)
        # self.filefeed = FileFeed(self.console.queue, "/etc/passwd", rewind=True, follow=True)
        # self.filefeed = FileFeed(self.console.queue,
        #   "/var/log/syslog", rewind=True, follow=False)
        self.filefeed = FileFeed(self.console.queue, "/var/log/syslog", rewind=True, follow=True)

        # Application controls.
        self.dispatch_info = False
        register_fkey(lambda key: self.toggle_dispatch_info(), curses.KEY_F5)

        # Library controls.
        register_fkey(self.console.toggle_debug, curses.KEY_F7)

        self.console.set_location(next(self.location))
        register_fkey(
            lambda key: self.console.set_location(next(self.location)),
            curses.KEY_F8,
        )

        self.console.set_verbose(next(self.verbose))
        register_fkey(
            lambda key: self.console.set_verbose(next(self.verbose)),
            curses.KEY_F9,
        )

        self.grid.redraw()

    def toggle_dispatch_info(self) -> None:
        """Toggle control."""
        self.dispatch_info = not self.dispatch_info

    def main(self):
        """Docstring."""

        # REPL
        for msgtype, lineno, line in self.console.get_msgtype_lineno_line():
            # Work...
            # logger.log("GETLINE", f"msgtype={msgtype} lineno={lineno} line={line!r}")
            logger.log(msgtype, f"msgtype={msgtype} lineno={lineno} line={line!r}")
            if line and "quit".find(line) == 0:
                break
            self.lastline = line

    def refresh(self, line: str) -> None:

        # Flush output.
        self.logwin.refresh()
        self.mainwin.clear()
        self.mainwin.move(0, 0)
        self.mainwin.addstr(f"F1 Numbers: speed: {self.numbers.timer}\n")
        self.mainwin.addstr(f"F2 Numbers: debug: {self.numbers.debug}\n")
        self.mainwin.addstr(f"F3 Letters: speed: {self.letters.timer}\n")
        self.mainwin.addstr(f"F4 Numbers: debug: {self.letters.debug}\n")
        self.mainwin.addstr(f"F5 Dispatch Info: {self.dispatch_info}\n")
        self.mainwin.addstr(f"F7 Console Debug: {self.console.debug}\n")
        self.mainwin.addstr(f"F8 Location: {self.console.location!r}\n")
        self.mainwin.addstr(f"F9 Verbose: {self.console.verbose}\n")
        self.mainwin.addstr(f"Lastline: {self.lastline!r}\n")
        self.mainwin.addstr("Enter command: " + line)
        self.mainwin.refresh()

    def dispatch(self, msgtype: str, *args) -> None:

        if self.dispatch_info:
            logger.info(f"msgtype={msgtype!r} args={args!r}")

        # if msgtype == "LETTER":
        #     (lineno, letter) = args
        #     logger.log(msgtype, letter)
        #     return

        # if msgtype == "NUMBER":
        #     (lineno, number) = args
        #     logger.log(msgtype, number)
        #     return

        # if msgtype == "FILE":
        #     (lineno, line) = args
        #     print(f"msgtype {msgtype} lineno {lineno} line {line}")
        #     # logger.log(msgtype, line)
        #     return

        raise ValueError(f"invalid msgtype={msgtype!r} args={args!r}")


def test_stub():
    """Make pytest happy with something to do; when in a test directory."""


if __name__ == "__main__":
    wrapper(lambda stdscr: Application(stdscr).main())
