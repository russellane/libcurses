"""Mouse handling."""

import curses
from collections import defaultdict, namedtuple

from loguru import logger

from libcurses.mouseevent import MouseEvent


class Mouse:
    """Mouse handling."""

    @staticmethod
    def enable():
        """Enable `curses.getkey` to return mouse events.

        Call after `curses.initscr`. If trouble, try `TERM=xterm-1002`.
        """

        newmask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
        (availmask, oldmask) = curses.mousemask(newmask)
        logger.trace(
            f"(availmask={availmask:#x}, oldmask={oldmask:#x}) = mousemask({newmask:#x})"
        )

    # -------------------------------------------------------------------------------
    # Internal mouse handlers

    handler = namedtuple("handler", "func args")
    handlers = []

    @classmethod
    def add_internal_mouse_handler(cls, func, args=None):
        """Register `func` to be called with `args` when mouse event happens."""

        handler = cls.handler(func, args)
        cls.handlers.append(handler)

    # -------------------------------------------------------------------------------
    # Application may register a handler to respond to mouse activity at coordinates

    yxhandler = namedtuple("yxhandler", "func begin_x last_x args")
    yxhandlers_by_row = {}

    @classmethod
    def add_mouse_handler(cls, func, y, x, ncols, args=None):
        """Call `func` with `args` when mouse event happens at (y, x)."""

        # pylint: disable=too-many-arguments
        cls.yxhandlers_by_row[y].append(cls.yxhandler(func, x, x + ncols - 1, args))

    @classmethod
    def clear_mouse_handlers(cls):
        """Remove all mouse handlers."""

        cls.yxhandlers_by_row = defaultdict(list)

    @classmethod
    def handle_mouse_event(cls):
        """Respond to `curses.getch` returning `curses.KEY_MOUSE`.

        Return True if any handler handled the event, else False.
        """

        mouse = MouseEvent()
        logger.trace(f"{mouse!r}")

        # Mouse handlers return True when they handle the event, and False when they don't.

        # Try internal mouse handlers first.

        if any(handler.func(mouse, handler.args) for handler in cls.handlers):
            return True

        # Try application mouse handler registered at mouse location.

        if any(
            handler.begin_x <= mouse.x <= handler.last_x and handler.func(mouse, handler.args)
            for handler in cls.yxhandlers_by_row.get(mouse.y, [])
        ):
            return True

        # All handlers, if any, ignored the mouse event.
        return False


add_mouse_handler = Mouse.add_mouse_handler
clear_mouse_handlers = Mouse.clear_mouse_handlers
