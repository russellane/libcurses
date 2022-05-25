"""Libcurses core module."""

import curses
from collections import defaultdict
from threading import Lock

CURSORWIN = None  # last window passed to `curses.getch`
LOCK = None  # protect `curses.doupdate`
FKEYS = None  # function key handlers


def wrapper(func):
    """Wrap https://docs.python.org/3/library/curses.html#curses.wrapper."""

    def _wrapper(stdscr):

        global CURSORWIN  # noqa
        global LOCK  # noqa
        global FKEYS  # noqa

        CURSORWIN = stdscr
        LOCK = Lock()
        FKEYS = defaultdict(list)

        func(stdscr)

    curses.wrapper(_wrapper)


def register_fkey(func, key: int = 0) -> None:
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
