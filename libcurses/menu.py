"""Menu widget.

This module provides `Menu` and `MenuItem` classes.
"""

import curses
import curses.ascii
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from libcurses.core import is_fkey
from libcurses.getkey import getkey
from libcurses.mouse import Mouse

__all__ = ["Menu", "MenuItem"]


@dataclass
class MenuItem:
    """Menu item."""

    key: int | str
    text: str
    payload: Any = field(default=None, repr=False)  # opaque
    keyname: str = field(init=False)

    def __post_init__(self) -> None:
        self.key = ord(self.key) if isinstance(self.key, str) else self.key
        self.keyname = curses.keyname(self.key).decode()


@dataclass(kw_only=True)
class Menu:
    """Menu."""

    title: str
    instructions: str
    subtitle: str | None = None
    win: curses.window | None = None
    menuitems: dict[str, MenuItem] = field(init=False, repr=False, default_factory=dict)
    max_len_keyname: int = field(default=0, init=False, repr=False)

    def add_item(self, key: int | str, text: str, payload: Any = None) -> None:
        """Add item to menu.

        Args:
            key:        keystroke
            text:       description
            payload:    opaque user data
        """

        item = MenuItem(key, text, payload)
        self.menuitems[item.keyname] = item
        if self.max_len_keyname < (_ := len(item.keyname)):
            self.max_len_keyname = _

    def premenu(self) -> None:
        """Top of `getkey`-loop on clear window at (0, 0) before rendering menu."""

    def preprompt(self) -> None:
        """Within `getkey`-loop, after menu, before prompt and `getkey`."""

    def prompt(self) -> MenuItem | None:
        """Display menu on `self.win`, read keyboard, and return selected item."""

        win = self.win
        assert win
        win.keypad(True)

        while True:
            win.clear()
            win.move(0, 0)
            self.premenu()

            win.addstr(self.title + "\n")
            if self.subtitle:
                win.addstr(self.subtitle + "\n")
            for item in self.menuitems.values():
                win.addstr(f"  {item.keyname:>{self.max_len_keyname}}: {item.text}\n")

            self.preprompt()
            win.addstr(self.instructions + ": ")

            if not (key := getkey(win, no_mouse=True)):
                return None

            if key == curses.KEY_MOUSE:
                Mouse.handle_mouse_event()
                continue

            if is_fkey(key):
                continue

            keyname = curses.keyname(key).decode()
            win.addstr(keyname + "\n")
            if _item := self.menuitems.get(keyname):
                return _item

            logger.error("invalid key {}={!r}", key, keyname)
