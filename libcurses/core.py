"""Libcurses core module."""

import curses
import sys
from collections import defaultdict
from contextlib import contextmanager
from threading import Lock
from typing import Callable, Iterator

__all__ = [
    "wrapper",
    "register_fkey",
    "is_fkey",
    "preserve_cursor",
]

# A function key handler receives the key pressed, and returns nothing.
FKeyHandler = Callable[[int], None]

CURSORWIN: curses.window  # last window passed to `curses.getch`
LOCK: Lock  # protect `curses.doupdate`
FKEYS: dict[int, list[FKeyHandler]]  # function key handlers


def wrapper(func: Callable[[curses.window], None]) -> None:
    """Use instead of `curses.wrapper`."""

    def _wrapper(stdscr: curses.window) -> None:

        global CURSORWIN  # noqa
        global LOCK  # noqa
        global FKEYS  # noqa

        CURSORWIN = stdscr
        LOCK = Lock()
        FKEYS = defaultdict(list)

        func(stdscr)

    curses.wrapper(_wrapper)


def register_fkey(func: FKeyHandler, key: int = 0) -> None:
    """Register `func` to be called when `key` is pressed.

    Args:
        func: callable, to be called on receipt of `key`.
        key: the key to be captured, e.g., `curses.KEY_F1`,
        or zero (0) for all keys.

    `func` is appended to a list for the `key`;
    pass func=None to remove list of funcs for `key` from registry.
    """

    global FKEYS  # noqa

    if func is None:
        del FKEYS[key]
    else:
        FKEYS[key].append(func)


def is_fkey(key: int) -> bool:
    """If `key` is a registered fkey, run its list of `func`s and return True.

    Return False if `key` is not registered.
    """

    if (funcs := FKEYS.get(key, FKEYS.get(0))) is not None:
        for func in funcs:
            func(key)
        return True
    return False


@contextmanager
def preserve_cursor() -> Iterator[tuple[int, int]]:
    """Context manager to save and restore the cursor."""

    global LOCK  # noqa
    global CURSORWIN  # noqa

    with LOCK:
        try:
            y, x = CURSORWIN.getyx() if CURSORWIN else curses.getsyx()
            yield y, x
        finally:
            if CURSORWIN:
                try:
                    CURSORWIN.move(y, x)
                except curses.error as err:
                    print(f"move({y}, {x}) err={err}", file=sys.stderr, flush=True)
                CURSORWIN.refresh()
            else:
                curses.setsyx(y, x)
                curses.doupdate()


# def keyname(key):
#     """Return string name of `key`."""
#
#     if isinstance(key, int):
#         return curses.keyname(key).decode()
#     return key
#
# def winyx(win):
#     """Return string with window coordinates."""
#
#     # xylint: disable=consider-using-f-string
#     return "(l={}, c={}, y={}, x={})".format(*win.getmaxyx(), *win.getbegyx())
