"""Example multi-threaded curses application."""

import curses
import itertools
import threading
import time
from queue import SimpleQueue

from loguru import logger

from libcurses import Console, Grid, register_fkey, wrapper


class Application:
    """Example multi-threaded curses application.

    Process data from 3 inputs:
        1. Lines ENTER'ed into the keyboard.
        2. Fruit from a FruitVendor.
        3. Animals from an AnimalFarm.

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
        logger.level("FRUIT", no=_always, color="<green>")
        logger.level("ANIMAL", no=_always, color="<yellow>")

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
            pre_block=self.pre_block,
            dispatch=self.dispatch,
        )

        # Add an application data feed.
        self.fruit_feed = FruitVendor(self.console.queue)
        # speed control
        register_fkey(self.fruit_feed.next_timer, curses.KEY_F1)
        # debug control
        register_fkey(self.fruit_feed.toggle_debug, curses.KEY_F2)

        # Add another application data feed.
        self.animal_feed = AnimalFarm(self.console.queue)
        register_fkey(self.animal_feed.next_timer, curses.KEY_F3)
        register_fkey(self.animal_feed.toggle_debug, curses.KEY_F4)

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
            logger.log("GETLINE", f"msgtype={msgtype} lineno={lineno} line={line!r}")
            if line and "quit".find(line) == 0:
                break
            self.lastline = line

    def pre_block(self, line: str) -> None:

        # Flush output.
        self.logwin.refresh()
        self.mainwin.clear()
        self.mainwin.move(0, 0)
        self.mainwin.addstr(f"F1 Fruit Speed: {self.fruit_feed.timer}\n")
        self.mainwin.addstr(f"F2 Fruit debug: {self.fruit_feed.debug}\n")
        self.mainwin.addstr(f"F3 Animal Speed: {self.animal_feed.timer}\n")
        self.mainwin.addstr(f"F4 Animal debug: {self.animal_feed.debug}\n")
        self.mainwin.addstr(f"F5 Dispatch info: {self.dispatch_info}\n")
        self.mainwin.addstr(f"F7 Console debug: {self.console.debug}\n")
        self.mainwin.addstr(f"F8 Location: {self.console.location!r}\n")
        self.mainwin.addstr(f"F9 Verbose: {self.console.verbose}\n")
        self.mainwin.addstr(f"Lastline: {self.lastline!r}\n")
        self.mainwin.addstr("Enter command: " + line)
        self.mainwin.refresh()

    def dispatch(self, msgtype: str, *args) -> None:

        if self.dispatch_info:
            logger.info(f"msgtype={msgtype!r} args={args!r}")

        if msgtype == "FRUIT":
            (fruit,) = args
            logger.log(msgtype, fruit)
            return

        if msgtype == "ANIMAL":
            (animal,) = args
            logger.log(msgtype, animal)
            return

        raise ValueError(f"invalid msgtype={msgtype!r} args={args!r}")


class FruitVendor:
    """Deliver a fruit every 'x' seconds."""

    name = "FRUIT"
    fruits = itertools.cycle(["11111-APPLE", "22222-BANANA", "33333-ORANGE"])
    timers = itertools.cycle([3, 2, 1])

    def __init__(self, queue: SimpleQueue):
        """Produce a fruit every 'x' seconds."""

        self.queue = queue
        self.debug = False
        self.timer = None
        self.next_timer(None)
        threading.Thread(target=self.work, name=self.name, daemon=True).start()

    def work(self) -> None:
        """Produce a fruit every 'x' seconds."""

        for seq in itertools.count(start=1):
            time.sleep(self.timer)
            fruit = next(self.fruits)
            msg = f"{fruit} after {self.timer} seconds."
            self.queue.put((self.name, seq, msg))

            if self.debug:
                msg = fruit.center(30, "-")
                logger.error(msg)
                logger.warning(msg)
                logger.info(msg)
                logger.debug(msg)
                logger.trace(msg)

    def next_timer(self, key: int) -> None:
        """Change `timer`; signature per `register_fkey`."""

        self.timer = next(self.timers)
        if self.debug:
            logger.success(f"key={key} timer={self.timer}")

    def toggle_debug(self, key: int) -> None:
        """Change `debug`; signature per `register_fkey`."""

        self.debug = not self.debug
        if self.debug:
            logger.success(f"key={key} debug={self.debug}")


class AnimalFarm:
    """Produce an animal every 'x' seconds."""

    name = "ANIMAL"
    animals = itertools.cycle(
        ["11111-CAT", "22222-DOG", "33333-HORSE", "44444-LION", "55555-ZEBRA"]
    )
    timers = itertools.cycle([3, 2, 1])

    def __init__(self, queue: SimpleQueue):
        """Produce an animal every 'x' seconds."""

        self.queue = queue
        self.debug = False
        self.timer = None
        self.next_timer(None)
        threading.Thread(target=self.work, name=self.name, daemon=True).start()

    def work(self) -> None:
        """Produce an animal every 'x' seconds."""

        for seq in itertools.count(start=1):
            time.sleep(self.timer)
            animal = next(self.animals)
            msg = f"{animal} after {self.timer} seconds."
            self.queue.put((self.name, seq, msg))

            if self.debug:
                msg = animal.rjust(30, "-")
                logger.error(msg)
                logger.warning(msg)
                logger.info(msg)
                logger.debug(msg)
                logger.trace(msg)

    def next_timer(self, key: int) -> None:
        """Change `timer`; signature per `register_fkey`."""

        self.timer = next(self.timers)
        if self.debug:
            logger.success(f"key={key} timer={self.timer}")

    def toggle_debug(self, key: int) -> None:
        """Change `debug`; signature per `register_fkey`."""

        self.debug = not self.debug
        if self.debug:
            logger.success(f"key={key} debug={self.debug}")


def test_stub():
    """Make pytest happy with something to do; when in a test directory."""


if __name__ == "__main__":
    wrapper(lambda stdscr: Application(stdscr).main())
