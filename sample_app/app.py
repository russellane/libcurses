"""Example multi-threaded curses application."""

import curses
import itertools
import sys
from queue import Empty

from loguru import logger

from libcurses import Console, Grid, register_fkey, wrapper
from sample_app.feeds.file import FileFeed
from sample_app.feeds.letter import LetterFeed
from sample_app.feeds.number import NumberFeed

try:
    logger.remove(0)
except ValueError:
    ...
logger.add(
    sys.stderr,
    format="{time:HH:mm:ss.SSS} {level} {function} {line} {message}",
    level="TRACE",
)


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
        logger.level("GETLINE", no=_always, color="<cyan><italic>")
        logger.level("/var/log/syslog", no=_always, color="<magenta>")
        logger.level("noisy.log", no=_always, color="<yellow><bold>")
        logger.level("LETTER", no=_always, color="<yellow>")
        logger.level("NUMBER", no=_always, color="<green>")

        # Application data here...
        self.last_line = None  # for menu to display last things.
        self.last_letter = None
        self.last_number = None

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

        # Application data feeds.
        # Each "message" from a feed:
        #   1. Puts the message into the feed's unique data queue, and
        #   2. Puts a wakeup message into the common control queue.
        self.feeds = {}

        feed = NumberFeed(self.console.queue)
        register_fkey(feed.next_timer, curses.KEY_F1)
        register_fkey(feed.toggle_debug, curses.KEY_F2)
        self.feeds[feed.msgtype] = feed
        self.numbers = feed  # promote for menu

        feed = LetterFeed(self.console.queue)
        register_fkey(feed.next_timer, curses.KEY_F3)
        register_fkey(feed.toggle_debug, curses.KEY_F4)
        self.feeds[feed.msgtype] = feed
        self.letters = feed  # promote for menu

        feed = FileFeed(
            self.console.queue,
            "/var/log/syslog",
            rewind=False,
            follow=True,
        )
        self.feeds[feed.msgtype] = feed

        feed = FileFeed(self.console.queue, "noisy.log", rewind=True, follow=True)
        self.feeds[feed.msgtype] = feed

        # Application controls.
        self.dispatch_debug = False
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
        self.dispatch_debug = not self.dispatch_debug

    def run(self) -> None:
        """Run console message event-loop."""
        self.console.run()

    def refresh(self, line: str) -> None:
        """Redisplay prompt, LINE, and refresh curses.

        Callback before reading each character during GETLINE, passed the
        current value of the LINE as it's being entered.
        """

        # Flush output.
        self.logwin.refresh()
        self.mainwin.clear()
        self.mainwin.move(0, 0)
        self.mainwin.addstr(f"F1 Numbers: speed: {self.numbers.timer}\n")
        self.mainwin.addstr(f"F2 Numbers: debug: {self.numbers.debug}\n")
        self.mainwin.addstr(f"F3 Letters: speed: {self.letters.timer}\n")
        self.mainwin.addstr(f"F4 Numbers: debug: {self.letters.debug}\n")
        self.mainwin.addstr(f"F5 Dispatch Info: {self.dispatch_debug}\n")
        self.mainwin.addstr(f"F7 Console Debug: {self.console.debug}\n")
        self.mainwin.addstr(f"F8 Location: {self.console.location!r}\n")
        self.mainwin.addstr(f"F9 Verbose: {self.console.verbose}\n")
        self.mainwin.addstr(f"Last-Command: {self.last_line!r}\n")
        self.mainwin.addstr(f"Last-Letter: {self.last_letter!r}\n")
        self.mainwin.addstr(f"Last-Number: {self.last_number!r}\n")
        self.mainwin.addstr("Enter command: " + line)
        self.mainwin.refresh()

    def dispatch(self, msgtype: str, *args) -> None:
        """Callback after ENTER during GETLINE, passed the final LINE."""

        # if self.dispatch_debug:
        #     logger.log(msgtype, f"msgtype={msgtype!r} args={args!r}")

        if msgtype == "GETLINE":
            (lineno, line) = args
            logger.log(msgtype, f"lineno {lineno} {line!r}")
            self.last_line = line
            if line and "quit".find(line) == 0:
                self.console.running = False

        elif (feed := self.feeds.get(msgtype)) is not None:
            self.drain(feed)

        else:
            raise ValueError(f"invalid msgtype={msgtype!r} args={args!r}")

        for feed in self.feeds.values():
            self.drain(feed)

    def drain(self, feed) -> None:

        while True:
            try:
                (msgtype, lineno, *args) = feed.queue.get(block=False)
            except Empty:  # as err:
                # logger.info(repr(err))
                break
            logger.log(msgtype, f"lineno {lineno} args={args!r}")


if __name__ == "__main__":
    wrapper(lambda stdscr: Application(stdscr).run())
