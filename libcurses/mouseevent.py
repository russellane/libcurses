"""Mouse handling."""

import copy
import curses


class MouseEvent:
    """Something done by a mouse; results of `curses.getmouse()`."""

    # pylint: disable=too-many-instance-attributes
    _last_mouse = None

    def __init__(self):
        """Initialize `MouseEvent` with current mouse info."""

        # https://docs.python.org/3/library/curses.html#curses.getmouse
        _, x, y, _, bstate = curses.getmouse()
        self.x = x
        self.y = y
        self.bstate = bstate

        if bstate & curses.REPORT_MOUSE_POSITION != 0 and self._last_mouse:
            self.button = self._last_mouse.button
            self.nclicks = self._last_mouse.nclicks
            self.is_pressed = True
            self.is_released = False
            self.is_alt = self._last_mouse.is_alt
            self.is_ctrl = self._last_mouse.is_ctrl
            self.is_shift = self._last_mouse.is_shift
            self.is_moving = True
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

    def __str__(self):

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

    def __repr__(self):

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
