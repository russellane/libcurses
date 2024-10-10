"""Mouse Event.

This module provides the `MouseEvent` class.
"""

import copy
import curses

__all__ = ["MouseEvent"]


class MouseEvent:
    """Wrap `curses.getmouse` with additional, convenience-properties.

    `MouseEvent` encapsulates the results of `curses.getmouse`,

        x               x-coordinate.
        y               y-coordinate.
        bstate          bitmask describing the type of event.

    and provides these additional properties:

        button          button number (1-5).
        nclicks         number of clicks (1-3).
        is_pressed      True if button is pressed.
        is_released     True if button was just released.
        is_alt          True if Alt key is held.
        is_ctrl         True if Ctrl key is held.
        is_shift        True if Shift key is held.
        is_moving       True if mouse is moving.
    """

    # pylint: disable=too-many-instance-attributes
    _last_mouse = None

    def __init__(self) -> None:
        """Initialize `MouseEvent` with current mouse info."""

        # https://docs.python.org/3/library/curses.html#curses.getmouse
        _, x, y, _, bstate = curses.getmouse()
        self.x: int = x
        self.y: int = y
        self.bstate: int = bstate

        if bstate & curses.REPORT_MOUSE_POSITION != 0 and self._last_mouse:
            self.button: int = self._last_mouse.button
            self.nclicks: int = self._last_mouse.nclicks
            self.is_pressed: bool = True
            self.is_released: bool = False
            self.is_alt: bool = self._last_mouse.is_alt
            self.is_ctrl: bool = self._last_mouse.is_ctrl
            self.is_shift: bool = self._last_mouse.is_shift
            self.is_moving: bool = True
            return

        #
        if bstate & (
            curses.BUTTON1_CLICKED
            | curses.BUTTON1_DOUBLE_CLICKED
            | curses.BUTTON1_TRIPLE_CLICKED
            | curses.BUTTON1_PRESSED
            | curses.BUTTON1_RELEASED
        ):
            self.button = 1  # left

        elif bstate & (
            curses.BUTTON2_CLICKED
            | curses.BUTTON2_DOUBLE_CLICKED
            | curses.BUTTON2_TRIPLE_CLICKED
            | curses.BUTTON2_PRESSED
            | curses.BUTTON2_RELEASED
        ):
            self.button = 2  # middle

        elif bstate & (
            curses.BUTTON3_CLICKED
            | curses.BUTTON3_DOUBLE_CLICKED
            | curses.BUTTON3_TRIPLE_CLICKED
            | curses.BUTTON3_PRESSED
            | curses.BUTTON3_RELEASED
        ):
            self.button = 3  # right

        elif bstate & (
            curses.BUTTON4_CLICKED
            | curses.BUTTON4_DOUBLE_CLICKED
            | curses.BUTTON4_TRIPLE_CLICKED
            | curses.BUTTON4_PRESSED
            | curses.BUTTON4_RELEASED
        ):
            self.button = 4  # wheelup / forward

        else:
            self.button = 5  # wheeldown / backward

        #
        self.nclicks = 0
        self.is_pressed = False
        self.is_released = False

        if bstate & (
            curses.BUTTON1_PRESSED
            | curses.BUTTON2_PRESSED
            | curses.BUTTON3_PRESSED
            | curses.REPORT_MOUSE_POSITION
        ):
            self.is_pressed = True

        elif bstate & (
            curses.BUTTON1_RELEASED | curses.BUTTON2_RELEASED | curses.BUTTON3_RELEASED
        ):
            self.is_released = True

        elif bstate & (curses.BUTTON1_CLICKED | curses.BUTTON2_CLICKED | curses.BUTTON3_CLICKED):
            self.nclicks = 1

        elif bstate & (
            curses.BUTTON1_DOUBLE_CLICKED
            | curses.BUTTON2_DOUBLE_CLICKED
            | curses.BUTTON3_DOUBLE_CLICKED
        ):
            self.nclicks = 2

        elif bstate & (
            curses.BUTTON1_TRIPLE_CLICKED
            | curses.BUTTON2_TRIPLE_CLICKED
            | curses.BUTTON3_TRIPLE_CLICKED
        ):
            self.nclicks = 3

        #
        self.is_alt = bstate & curses.BUTTON_ALT != 0
        self.is_ctrl = bstate & curses.BUTTON_CTRL != 0
        self.is_shift = bstate & curses.BUTTON_SHIFT != 0
        self.is_moving = bstate & curses.REPORT_MOUSE_POSITION != 0

        self.__class__._last_mouse = copy.copy(self)

    def __str__(self) -> str:

        parts = []
        if self.is_alt:
            parts.append("Alt")
        if self.is_ctrl:
            parts.append("Ctrl")
        if self.is_shift:
            parts.append("Shift")
        parts.append("M" + str(self.button))
        string = "+".join(parts)
        if self.nclicks > 1:
            string += f"*{self.nclicks}"
        return string

    def __repr__(self) -> str:

        return (
            self.__class__.__name__
            + "("
            + ", ".join(
                [
                    f"name='{self!s}'",
                    f"y={self.y}",
                    f"x={self.x}",
                    f"bstate={self.bstate:#x}",
                    # f'button={self.button}',
                    f"nclicks={self.nclicks}",
                    # f'is_alt={self.is_alt}',
                    # f'is_ctrl={self.is_ctrl}',
                    # f'is_shift={self.is_shift}',
                    f"is_pressed={self.is_pressed}",
                    f"is_released={self.is_released}",
                    f"is_moving={self.is_moving}",
                ]
            )
            + ")"
        )
