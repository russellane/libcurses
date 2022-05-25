"""Menu widget."""

import curses
import curses.ascii
from typing import Dict

from loguru import logger

from libcurses.getkey import getkey
from libcurses.mouse import Mouse


class Menu:
    """Menu class."""

    def __init__(self, title: str, instructions: str) -> None:
        """Initialize menu with `title` and prompting `instructions`."""

        self.title: str = title
        self.subtitle: str = None
        self.instructions: str = instructions
        self.menuitems: Dict(MenuItem) = {}
        self.max_len_keyname: int = 0

    def add_item(self, key, text: str, payload=None) -> None:
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

    def prompt(self, win):
        """Display menu on `win`, read keyboard, and return selected item."""

        while True:
            win.clear()
            win.move(0, 0)
            win.addstr(self.title + "\n")
            if self.subtitle:
                win.addstr(self.subtitle + "\n")
            for item in self.menuitems.values():
                win.addstr(f"  {item.keyname:>{self.max_len_keyname}}: {item.text}\n")
            win.addstr(self.instructions + ": ")

            if not (key := getkey(win, no_mouse=True)):
                return None

            if key == curses.KEY_MOUSE:
                Mouse.handle_mouse_event()
                continue

            keyname = curses.keyname(key).decode()
            win.addstr(keyname + "\n")
            if item := self.menuitems.get(keyname):
                return item

            logger.error("invalid key {}={!r}", key, keyname)


class MenuItem:  # pylint: disable=too-few-public-methods
    """Menu item class."""

    def __init__(self, key, text: str, payload=None) -> None:
        """Initialize menu item instance.

        Args:
            key:        keystroke
            text:       description
            payload:    opaque user data
        """

        self.key = ord(key) if isinstance(key, str) else key
        self.text = text
        self.payload = payload
        self.keyname = curses.keyname(self.key).decode()
