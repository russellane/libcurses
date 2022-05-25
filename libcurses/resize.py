"""Resize grid mixin module."""

import copy
import curses
import curses.ascii

from loguru import logger

from libcurses.core import register_fkey
from libcurses.getkey import getkey
from libcurses.mouse import Mouse, MouseEvent


class ResizeMixin:
    """Resize grid mixin class."""

    # pylint: disable=too-few-public-methods

    _once = True

    def __init__(self):
        """Extend `Grid` with Resize functionality."""

        if self._once:
            self.__class__._once = False
            register_fkey(lambda key: self._handle_term_resized_event(), curses.KEY_RESIZE)
            Mouse.enable()
            Mouse.add_internal_mouse_handler(self._handle_mouse_event)

        super().__init__()

    # respond to mouse activity within the grid, not the perimiter
    @property
    def _mouse_min_y(self) -> int:
        return self.begin_y + 1

    @property
    def _mouse_max_y(self) -> int:
        return self.begin_y + self.nlines - 2

    @property
    def _mouse_min_x(self) -> int:
        return self.begin_x + 1

    @property
    def _mouse_max_x(self) -> int:
        return self.begin_x + self.ncols - 2

    def _handle_term_resized_event(self):
        """Respond to terminal having been resized."""

        # pylint: disable=no-member
        logger.warning(f"old={self.nlines}x{self.ncols} new={curses.LINES}x{curses.COLS}")
        self.nlines, self.ncols = curses.LINES, curses.COLS
        self.win.resize(self.nlines, self.ncols)
        self.grid = [[0 for x in range(self.ncols)] for y in range(self.nlines)]
        self.attrs = [[0 for x in range(self.ncols)] for y in range(self.nlines)]
        if self._builder:
            self._builder()
        # self.redraw()

    def _handle_mouse_event(self, mouse: MouseEvent, args):
        """Handle mouse event to resize boxes within grid.

        If mouse pressed on an interior window border, resize windows on
        both sides of border, and return True.
        """

        _ = args  # unused-argument

        if not (mouse.button == 1 and (mouse.is_pressed or mouse.nclicks == 2)):
            return False  # we don't care, try another handler

        if not (
            mouse.x >= self._mouse_min_x
            and mouse.x <= self._mouse_max_x
            and mouse.y >= self._mouse_min_y
            and mouse.y <= self._mouse_max_y
        ):
            # logger.trace('not within grid')
            return False

        char = self.win.inch(mouse.y, mouse.x) & ~curses.A_COLOR

        if char == curses.ACS_VLINE:
            left = self.getwin(mouse.y, mouse.x - 1)
            right = self.getwin(mouse.y, mouse.x + 1)
            self._resize(mouse, left=left, right=right)
            # logger.trace('after _resize left/right')
            return True

        if char == curses.ACS_HLINE:
            upper = self.getwin(mouse.y - 1, mouse.x)
            lower = self.getwin(mouse.y + 1, mouse.x)
            self._resize(mouse, upper=upper, lower=lower)
            # logger.trace('after _resize upper/lower')
            return True

        # logger.trace('not a border char')
        return False

    def _resize(self, mouse, left=None, right=None, upper=None, lower=None):

        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        # if left and right:
        #     logger.trace(f'left={self.winyx(left)} right={self.winyx(right)}')
        # elif upper and lower:
        #     logger.trace(f'upper={self.winyx(upper)} lower={self.winyx(lower)}')
        # else:
        #     raise RuntimeError('missing left/right or upper/lower')

        kb_resize_mode = mouse.is_ctrl or (mouse.nclicks == 2)
        resized = False

        while True:
            last_mouse = mouse

            if resized:
                self.redraw()
                resized = False

            #
            if left:
                self.border_attr(left, self.N.R, True)
            elif right:
                self.border_attr(right, self.N.L, True)
            if upper:
                self.border_attr(upper, self.N.B, True)
            elif lower:
                self.border_attr(lower, self.N.T, True)
            self.redraw()

            #
            key = getkey(None, no_mouse=True)

            #
            if left:
                self.border_attr(left, self.N.R, False)
            elif right:
                self.border_attr(right, self.N.L, False)
            if upper:
                self.border_attr(upper, self.N.B, False)
            elif lower:
                self.border_attr(lower, self.N.T, False)
            self.redraw()

            #
            if not key:
                return

            if key in (curses.ascii.LF, curses.ascii.CR, curses.ascii.ESC, curses.KEY_ENTER):
                return

            if key == curses.ascii.FF:
                self.redraw()
                logger.trace("continue")
                continue

            if not kb_resize_mode:
                # mouse-dragging resize mode

                if key != curses.KEY_MOUSE:
                    logger.trace("continue")
                    continue

                mouse = MouseEvent()
                logger.trace(f"mouse={mouse!r}")

                if mouse.is_released:
                    return

                if not mouse.is_moving:
                    continue

            else:
                assert kb_resize_mode

                if key == curses.KEY_MOUSE:
                    # emulate keyboard

                    mouse = MouseEvent()
                    logger.trace(f"mouse={mouse!r}")

                    if mouse.button == 4:
                        # emulate left and up arrows
                        if left or right:
                            key = curses.KEY_LEFT
                        elif upper or lower:
                            key = curses.KEY_UP
                    elif mouse.button == 5:
                        # emulate right and down arrows
                        if left or right:
                            key = curses.KEY_RIGHT
                        elif upper or lower:
                            key = curses.KEY_DOWN
                    elif mouse.nclicks or mouse.is_released:
                        # emulate ESC
                        return

                # emulate mouse

                if key == curses.KEY_LEFT:
                    if last_mouse.x <= self._mouse_min_x:
                        logger.trace("continue")
                        continue
                    mouse = copy.copy(last_mouse)
                    mouse.x -= 1

                elif key == curses.KEY_RIGHT:
                    if last_mouse.x >= self._mouse_max_x - 1:
                        logger.trace("continue")
                        continue
                    mouse = copy.copy(last_mouse)
                    mouse.x += 1

                elif key == curses.KEY_UP:
                    if mouse.y <= self._mouse_min_y:
                        logger.trace("continue")
                        continue
                    mouse = copy.copy(last_mouse)
                    mouse.y -= 1

                elif key == curses.KEY_DOWN:
                    if mouse.y >= self._mouse_max_y:
                        logger.trace("continue")
                        continue
                    mouse = copy.copy(last_mouse)
                    mouse.y += 1

                else:
                    logger.trace("continue")
                    continue

                #
                key = curses.KEY_MOUSE
                mouse.bstate = curses.REPORT_MOUSE_POSITION
                mouse.is_moving = True
                mouse.nclicks = 0

            # make sure all operations are allowed before performing any.

            if mouse.x < last_mouse.x and left:
                nlines, ncols = left.getmaxyx()
                if ncols <= 1:
                    logger.trace(f"cannot shrink left={self.winyx(left)}")
                    continue

            if mouse.x > last_mouse.x and right:
                nlines, ncols = right.getmaxyx()
                if ncols <= 1:
                    logger.trace(f"cannot shrink right={self.winyx(right)}")
                    continue

            if mouse.y < last_mouse.y and upper:
                nlines, ncols = upper.getmaxyx()
                if nlines <= 1:
                    logger.trace(f"cannot shrink upper={self.winyx(upper)}")
                    continue

            if mouse.y > last_mouse.y and lower:
                nlines, ncols = lower.getmaxyx()
                if nlines <= 1:
                    logger.trace(f"cannot shrink lower={self.winyx(lower)}")
                    continue

            # perform...

            if mouse.x < last_mouse.x:
                if left:
                    nlines, ncols = left.getmaxyx()
                    # remove rightmost column from left window
                    left.resize(nlines, ncols - 1)
                    resized = True

                if right:
                    # slide right window left 1 column
                    begin_y, begin_x = right.getbegyx()
                    right.mvwin(begin_y, begin_x - 1)

                    # add 1 column to right of right window
                    nlines, ncols = right.getmaxyx()
                    right.resize(nlines, ncols + 1)

            elif mouse.x > last_mouse.x:
                if right:
                    nlines, ncols = right.getmaxyx()
                    # remove rightmost column from right window
                    right.resize(nlines, ncols - 1)
                    resized = True

                    # slide right window right 1 column
                    begin_y, begin_x = right.getbegyx()
                    right.mvwin(begin_y, begin_x + 1)

                if left:
                    # add 1 column to right of left window
                    nlines, ncols = left.getmaxyx()
                    left.resize(nlines, ncols + 1)

            if mouse.y < last_mouse.y:
                if upper:
                    nlines, ncols = upper.getmaxyx()
                    # remove bottom row from upper window
                    upper.resize(nlines - 1, ncols)
                    resized = True

                if lower:
                    # slide lower window up 1 row
                    begin_y, begin_x = lower.getbegyx()
                    nlines, ncols = lower.getmaxyx()
                    lower.mvwin(begin_y - 1, begin_x)

                    # add 1 row to bottom of lower window
                    lower.resize(nlines + 1, ncols)

            elif mouse.y > last_mouse.y:
                if lower:
                    nlines, ncols = lower.getmaxyx()
                    # remove bottom row from lower window
                    lower.resize(nlines - 1, ncols)
                    resized = True

                    # slide lower window down 1 row
                    begin_y, begin_x = lower.getbegyx()
                    lower.mvwin(begin_y + 1, begin_x)

                if upper:
                    # add 1 row to bottom of upper window
                    nlines, ncols = upper.getmaxyx()
                    upper.resize(nlines + 1, ncols)
