import curses
import itertools
import threading
import time

from loguru import logger

import libcurses
from libcurses.grid import Grid
from libcurses.logwin import LoggerWindow
from libcurses.menu import Menu, MenuItem


def test_stub():
    pass


# -------------------------------------------------------------------------------
# interactive non-pytest tests below


def get_test_menu(logwin: LoggerWindow) -> Menu:
    """Create and return test `Menu` instance."""

    menu = Menu("Main menu", "Make your choice")

    def _echo(item: MenuItem) -> bool:
        """Example of a shared handler."""
        logger.success("You selected {}", item.text)
        # return True to break caller's loop

    menu.add_item("1", "Do one thing and do it well.", _echo)
    menu.add_item("2", "Two heads are better than one.", _echo)
    menu.add_item("a", "An apple a day keeps the doctor away.", _echo)
    menu.add_item("b", "Better late than never.", _echo)

    menu.add_item(curses.KEY_F1, "Help!", lambda item: logger.success("Helpful message..."))
    menu.add_item(curses.KEY_F2, "Test LINE mode", "line")
    menu.add_item(curses.KEY_F3, "Test KEY mode", "key")
    menu.add_item(curses.KEY_F4, "Quit", lambda item: True)

    location = itertools.cycle(
        [
            "{module}:{line}",
            "{file}:{line}:{function}",
            "{thread.name}:{file}:{line}:{function}",
            "{name}:{function}:{line}",
            None,
        ]
    )

    menu.add_item(
        curses.KEY_F8, "Cycle location", lambda item: logwin.set_location(next(location))
    )
    return menu


def main(win: curses.window):
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    grid = Grid(win)

    upper = grid.box("upper", grid.nlines // 2, 0, left=grid, right=grid, top=grid)
    upper.scrollok(True)

    lower = grid.box("lower", 0, 0, left=grid, right=grid, top2b=upper, bottom=grid)
    lower.scrollok(True)
    logwin = LoggerWindow(lower)
    logwin.set_verbose(2)

    grid.redraw()

    win = upper
    win.keypad(True)

    _timer = 3

    def _timer_thread():
        while True:
            time.sleep(_timer)
            msg = f"_timer {_timer} time {time.asctime()}"
            logger.error("error " + msg)
            logger.warning("warning " + msg)
            logger.info("info " + msg)
            logger.debug("debug " + msg)
            logger.trace("trace " + msg)

    threading.Thread(target=_timer_thread, daemon=True).start()

    menu = get_test_menu(logwin)
    mode = "menu"
    while True:
        if mode == "menu":
            if (choice := menu.prompt(win)) is None:
                break
            menu.subtitle = f"last choice={choice.__dict__!r}"
            if choice.payload:
                if isinstance(choice.payload, str):
                    mode = choice.payload
                elif choice.payload(choice):
                    break

        elif mode == "line":
            win.addstr("[^D, --, -v, -vv, t++, t--, menu, key] Enter line: ")
            line = libcurses.getline(win)
            win.addstr(f"line={line!r}\n")
            if line is None:
                break
            if line == "--":
                logwin.set_verbose(0)
            elif line == "-v":
                logwin.set_verbose(1)
            elif line == "-vv":
                logwin.set_verbose(2)
            elif line == "t++":
                _timer += 1
            elif line == "t--":
                if _timer > 1:
                    _timer -= 1
            elif line in ("menu", "key"):
                mode = line

        elif mode == "key":
            win.addstr("[^D, F1=MENU, F2=LINE] press KEY: ")
            key = libcurses.getkey(win)
            name = curses.keyname(key).decode()
            win.addstr(f"key={key!r} name={name!r}\n")
            if key is None or key <= 0:
                break
            if key == curses.KEY_F1:
                mode = "menu"
            elif key == curses.KEY_F2:
                mode = "line"


if __name__ == "__main__":
    libcurses.wrapper(main)
