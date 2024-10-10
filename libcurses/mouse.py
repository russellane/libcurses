"""Mouse handling.

This module provides `Mouse` and `MouseEvent` classes.
"""

import curses
from collections import defaultdict, namedtuple
from typing import Any, Callable

from loguru import logger

from libcurses.mouseevent import MouseEvent

__all__ = ["Mouse", "MouseEvent"]

# A Mouse handler receives the MouseEvent and any additional args, and
# returns True if the handler "handled" the event, or False if not.

MouseHandler = Callable[[MouseEvent, Any], bool]


class Mouse:
    """The `Mouse` class provides methods to...

    1) enable `curses.getch` to return mouse events (curses.KEY_MOUSE).

    2) register callbacks to respond to mouse events.

    3) respond to `curses.getch` returning `curses.KEY_MOUSE`
       by calling any registered callbacks.
    """

    @staticmethod
    def enable() -> None:
        """Enable `curses.getkey` to return mouse events (curses.KEY_MOUSE).

        Call after `curses.initscr`. If trouble, try `TERM=xterm-1002`.
        """

        newmask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
        (availmask, oldmask) = curses.mousemask(newmask)
        logger.trace(
            f"(availmask={availmask:#x}, oldmask={oldmask:#x}) = mousemask({newmask:#x})"
        )

    # -------------------------------------------------------------------------------
    # Internal mouse handlers

    _handler = namedtuple("_handler", "func args")
    _handlers: list[_handler] = []

    @classmethod
    def add_internal_mouse_handler(
        cls,
        func: MouseHandler,
        args: Any = None,
    ) -> None:
        """Register `func` to be called with `args` when mouse event happens."""

        handler = cls._handler(func, args)
        cls._handlers.append(handler)

    # -------------------------------------------------------------------------------
    # Application may register a handler to respond to mouse activity at coordinates

    _yxhandler = namedtuple("_yxhandler", "func begin_x last_x args")
    _yxhandlers_by_row: dict[int, list[_yxhandler]] = defaultdict(list)

    @classmethod
    def add_mouse_handler(
        cls,
        func: MouseHandler,
        y: int,
        x: int,
        ncols: int,
        args: Any = None,
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        """Call `func` with `args` when mouse event happens at (y, x)."""

        # pylint: disable=too-many-arguments
        cls._yxhandlers_by_row[y].append(cls._yxhandler(func, x, x + ncols - 1, args))

    @classmethod
    def clear_mouse_handlers(cls) -> None:
        """Remove all mouse handlers."""

        cls._yxhandlers_by_row = defaultdict(list)

    @classmethod
    def handle_mouse_event(cls) -> bool:
        """Respond to `curses.getch` returning `curses.KEY_MOUSE`.

        Return True if any handler handled the event, else False.
        """

        mouse = MouseEvent()
        logger.trace(f"{mouse!r}")

        # Mouse handlers return True when they handle the event, and False when they don't.

        # Try internal mouse handlers first.

        if any(x.func(mouse, x.args) for x in cls._handlers):
            return True

        # Try application mouse handler registered at mouse location.

        if any(
            x.begin_x <= mouse.x <= x.last_x and x.func(mouse, x.args)
            for x in cls._yxhandlers_by_row.get(mouse.y, [])
        ):
            return True

        # All handlers, if any, ignored the mouse event.
        return False


add_mouse_handler = Mouse.add_mouse_handler
clear_mouse_handlers = Mouse.clear_mouse_handlers
