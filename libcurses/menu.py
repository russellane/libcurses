"""Menu widget."""

import curses
import curses.ascii
from dataclasses import KW_ONLY, dataclass, field
from typing import Any

from loguru import logger

from libcurses.core import is_fkey
from libcurses.getkey import getkey
from libcurses.mouse import Mouse


@dataclass
class MenuItem:
    """Menu item."""

    key: int | str
    text: str
    payload: Any = field(default=None, repr=False)  # opaque
    keyname: str = field(init=False)

    def __post_init__(self):
        self.key = ord(self.key) if isinstance(self.key, str) else self.key
        self.keyname = curses.keyname(self.key).decode()


@dataclass
class Menu:
    """Menu."""

    title: str
    instructions: str
    _: KW_ONLY
    subtitle: str = None
    win: curses.window = None
    menuitems: [str, MenuItem] = field(init=False, repr=False, default_factory=dict)
    max_len_keyname: int = field(default=0, init=False, repr=False)

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

    def premenu(self) -> None:
        """Top of `getkey`-loop on clear window at (0, 0) before rendering menu."""

    def preprompt(self) -> None:
        """Within `getkey`-loop, after menu, before prompt and `getkey`."""

    def prompt(self):
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
            if item := self.menuitems.get(keyname):
                return item

            logger.error("invalid key {}={!r}", key, keyname)
