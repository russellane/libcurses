"""Example application."""

import curses
import sys
import threading
import time
from collections import deque
from itertools import cycle

from loguru import logger

from libcurses import Grid, LogSink, getkey, getline, register_fkey, wrapper
from libcurses.menu import Menu, MenuItem

try:
    logger.remove(0)
except ValueError:
    ...
logger.add(
    sys.stderr,
    level="TRACE",
    format="{time:HH:mm:ss.SSS}|{level}|{function}|{line}|{message}",
)


class SampleTimer(threading.Thread):
    """Sample periodic widget that uses logger."""

    name = "TIMER"
    daemon = True
    intervals = deque([3, 2, 1, 0.75, 0.5, 0.25])

    def __init__(self) -> None:
        """Init widget."""

        threading.Thread.__init__(self)

    def run(self) -> None:
        """Run sample widget."""

        # speed controls
        register_fkey(lambda key: self.intervals.rotate(-1), curses.KEY_F6)
        register_fkey(lambda key: self.intervals.rotate(1), curses.KEY_F7)

        while True:
            secs = self.intervals[0]
            time.sleep(secs)
            now = time.asctime()
            logger.error("error every {} seconds at {}", secs, now)
            logger.warning("warning every {} seconds at {}", secs, now)
            logger.info("info every {} seconds at {}", secs, now)
            logger.debug("debug every {} seconds at {}", secs, now)
            logger.trace("trace every {} seconds at {}", secs, now)
            logger.log("custom-error", "custom every {} seconds at {}", secs, now)
            logger.log("custom-warning", "custom every {} seconds at {}", secs, now)
            logger.log("custom-always", "custom every {} seconds at {}", secs, now)
            logger.log("custom-info", "custom every {} seconds at {}", secs, now)
            logger.log("custom-debug", "custom every {} seconds at {}", secs, now)
            logger.log("custom-trace", "custom every {} seconds at {}", secs, now)

    @property
    def interval(self) -> float:
        """Return current time period."""
        return self.intervals[0]


class Application:
    """Example application."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, stdscr: curses.window):
        """Example application."""

        # Configure logger...
        # Remove bold from default levels.
        for lvl in logger._core.levels.values():  # type: ignore[attr-defined]
            logger.level(lvl.name, color=lvl.color.replace("<bold>", ""))
        # Add custom logging levels...
        # Set severity of custom levels relative to builtins.
        _error = logger.level("ERROR").no
        _warning = logger.level("WARNING").no
        _always = _warning
        _info = logger.level("INFO").no
        _debug = logger.level("DEBUG").no
        _trace = logger.level("TRACE").no
        logger.level("custom-error", no=_error, color="<red><underline>")
        logger.level("custom-warning", no=_warning, color="<yellow><underline>")
        logger.level("custom-always", no=_always, color="<yellow><underline>")
        logger.level("custom-info", no=_info, color="<white><underline>")
        logger.level("custom-debug", no=_debug, color="<blue><underline>")
        logger.level("custom-trace", no=_trace, color="<cyan><underline>")

        # Application data here...
        self.timer: SampleTimer
        self.last_line: str  # for menu to display last line entered.
        self.menu: Menu
        self.mode: str | None = "menu"

        # +----------+---------+
        # | main     | history |
        # +----------+---------+
        # | logger             |
        # +----------+---------+

        self.grid = Grid(stdscr)

        # menu/prompt, command line input.
        self.mainwin = self.grid.box(
            "mainwin",
            top=self.grid,
            nlines=self.grid.nlines // 2,
            left=self.grid,
            ncols=self.grid.ncols // 2,
        )
        self.mainwin.scrollok(True)

        self.histwin = self.grid.box(
            "histwin",
            top=self.mainwin,
            nlines=0,
            bottom=self.mainwin,
            left2r=self.mainwin,
            ncols=0,
            right=self.grid,
        )
        self.histwin.scrollok(True)

        # Lower panel: logger messages.
        self.logwin = self.grid.box(
            "logwin",
            top2b=self.mainwin,
            nlines=0,
            bottom=self.grid,
            left=self.grid,
            ncols=0,
            right=self.grid,
        )

        # Begin logging to `logwin`.
        self.sink = LogSink(self.logwin)

        # Change format of `location` field on the fly; (not required)
        self.location = cycle(
            [
                "{thread.name}.{name}.{function}:{line}",
                "{name}.{function}:{line}",
                "{module}:{function}:{line}",
                "{file}:{line}:{function}",
                None,
            ]
        )
        self.sink.set_location(next(self.location))
        register_fkey(
            lambda key: self.sink.set_location(next(self.location)),
            curses.KEY_F8,
        )

        # Change verbosity on the fly; (not required)
        self.verbose = cycle([2, 1, 0])  # ["-vv", "-v", ""]
        self.sink.set_verbose(next(self.verbose))
        register_fkey(self._cycle_verbose, curses.KEY_F9)

        # Reset logger column padding.
        register_fkey(lambda key: self.sink.reset_padding(), curses.KEY_F10)

        self.grid.redraw()

    def _cycle_verbose(self, _key: int) -> None:
        """This worked as a lambda; mypy didn't like it as a lambda."""
        self.sink.set_verbose(next(self.verbose))
        self._add_history("from global fkey: " + self.sink.level)

    def run(self) -> None:
        """Run application."""

        threading.current_thread().name = "MAIN"
        self.timer = SampleTimer()
        self.timer.start()

        self.mode = "menu"

        while self.mode:
            if self.mode == "menu":
                self.menu_mode()
            elif self.mode == "line":
                self.getline_mode()
            elif self.mode == "key":
                self.getkey_mode()
            else:
                raise RuntimeError(self.mode)

            self.grid.refresh()

    # def premenu(self) -> None:
    #     """Top of `getkey`-loop on clear window at (0, 0) before rendering menu."""
    #     self.menu.subtitle = self._fkey_help()

    def preprompt(self) -> None:
        """Within `getkey`-loop, after menu, before prompt and `getkey`."""

        assert self.menu.win is self.mainwin
        self.mainwin.addstr(self._fkey_help() + "\n")

    def menu_mode(self) -> None:
        """Run menu mode."""

        # https://github.com/PyCQA/pylint/issues/5225
        # pylint: enable=no-value-for-parameter
        self.menu = Menu(
            title="Main menu",
            instructions="Make your choice",
            win=self.mainwin,
        )

        self.menu.preprompt = self.preprompt  # type: ignore[method-assign]

        def _echo(item: MenuItem) -> bool:
            """Shared handler."""
            self._add_history("from menu item: " + item.text)
            logger.success("You selected {!r}", item.text)
            return False
            # return True  # to break caller's loop

        self.menu.add_item(ord("1"), "This is the FIRST choice.", _echo)
        self.menu.add_item(ord("2"), "This is the SECOND choice.", _echo)
        self.menu.add_item(ord("a"), "Items are case-sensitive.", _echo)
        self.menu.add_item(ord("A"), "ITEMS ARE CASE-SENSITIVE.", _echo)

        self.menu.add_item(
            curses.KEY_F1, "Help!", lambda item: logger.success("Helpful message...")
        )
        self.menu.add_item(curses.KEY_F2, "Test LINE mode", "line")
        self.menu.add_item(curses.KEY_F3, "Test KEY mode", "key")
        self.menu.add_item(curses.KEY_F4, "Quit", lambda item: True)

        if (item := self.menu.prompt()) is None:
            self.mode = None
            return

        self._add_history(repr(item))
        # self.menu.subtitle = f"last item={item}"
        if item.payload:
            if isinstance(item.payload, str):
                self.mode = item.payload
                self._add_history(f"mode={self.mode!r}")
            elif item.payload(item):
                self.mode = None

    def getline_mode(self) -> None:
        """Run getline mode."""

        win = self.mainwin

        win.clear()
        win.addstr(
            "\n".join(
                [
                    "LINE mode",
                    self._fkey_help(),
                    "",
                    "[^D, 'menu', 'key'] Enter line: ",
                ]
            )
        )

        line = getline(win)
        self._add_history(f"line={line!r}")
        logger.info(f"line={line!r}\n")
        if line is None or line in ("menu", "key"):
            self.mode = line
        else:
            self.last_line = line

    def getkey_mode(self) -> None:
        """Run getkey mode."""

        self.mainwin.addstr("[^D, F1=MENU, F2=LINE] press KEY: ")
        key = getkey(self.mainwin)
        name = curses.keyname(key).decode() if key is not None else "None"
        self.mainwin.addstr(f"key={key!r} name={name!r}\n")
        if key is None or key <= 0:
            self.mode = ""
        if key == curses.KEY_F1:
            self.mode = "menu"
        elif key == curses.KEY_F2:
            self.mode = "line"

    def _add_history(self, msg: str) -> None:

        if sum(self.histwin.getyx()):
            self.histwin.addch("\n")
        self.histwin.addstr(msg)

    def _fkey_help(self) -> str:

        return "\n".join(
            [
                "Global function keys:",
                f"  F6/F7: Faster/Slower: {self.timer.interval!r}",
                f"  F8 Cycle location: {self.sink.location!r}",
                f"  F9 Cycle level: {self.sink.level!r}",
                "   F10: Reset padding",
            ]
        )


if __name__ == "__main__":
    wrapper(lambda stdscr: Application(stdscr).run())
