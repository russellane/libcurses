"""Group of resizable windows.

This module provides the `Grid` class.
"""

from __future__ import annotations

import copy
import curses
import curses.ascii
from enum import IntFlag
from typing import Any, Callable

from loguru import logger

import libcurses.core
from libcurses.getkey import getkey
from libcurses.mouse import Mouse, MouseEvent

__all__ = ["Grid"]

# A character/attribute pair.
CharAttr = tuple[int, int] | None

# A callback to add boxes to an empty grid.
GridBuilder = Callable[[], None]

# -------------------------------------------------------------------------------


class Grid:
    """Grid of windows.

    A rectangular collection of windows with shared (collapsed) borders that
    resize the windows to either side (syncronized shrink/expand) when moused upon.

            +-------+---+------+    example `Grid`, 9 windows.
            |       |   |      |
            +-------+---+------+
            |           |      |
            +------+----+------+
            |      |           |
            +------+--+--------+
            |         |        |
            +---------+--------+

    Drag and drop an interior border to resize the windows on either side.

    Double-click an interior border to enter Resize Mode:
        * scroll-wheel and arrow-keys move the border, and
        * click anywhere, Enter and Esc to exit Resize Mode.

    Grids also provide a wrapper around `curses.newwin` that takes positioning
    parameters that describe the spatial-relationship to other windows on the
    screen, instead of (y,x) coordinates:

              +--------+                 +--------+
              |        |                 |  ^     |
              |        |<------ left2r --|  |     |
              |        |                 |  |     |
              |<---------------- left ---|  |     |
              |        |                 |  |     |
              +--------+                 +--|-----+
                 |  |                       |  ^
        bottom2t |  | bottom            top |  | top2b
                 v  |                       |  |
              +-----|--+                 +--------+
              |     |  |                 |        |
              |     |  |-- right ---------------->|
              |     |  |                 |        |
              |     |  |-- right2l ----->|        |
              |     v  |                 |        |
              +--------+                 +--------+

    For example, this 3x13 grid with three 3x5 boxes may be described at least
    three different ways:

                +---+---+---+
                | a | b | c |
                +---+---+---+

        grid = Grid(curses.newwin(3, 13))

        1)  a = grid.box('a', 3, 5)
            b = grid.box('b', 3, 5, left2r=a)
            c = grid.box('c', 3, 5, left2r=b)

        2)  c = grid.box('c', 3, 5, right=grid)
            b = grid.box('b', 3, 5, right=c)
            a = grid.box('a', 3, 5, right=b)

        3)  a = grid.box('a', 3, 5, left=grid)
            c = grid.box('c', 3, 5, right=grid)
            b = grid.box('b', 3, 0, left2r=a, right=c)

    If two endpoints are given (such as 3b), the length will be calculated to
    fill the gap between the endpoints.
    """

    # pylint: disable=too-many-instance-attributes

    class N(IntFlag):
        """has neighbor to the direction."""

        T = 1
        R = 2
        B = 4
        L = 8

    # -------------------------------------------------------------------------------

    _borders: dict[int, int]
    _init_called = False

    @classmethod
    def _init_borders(cls) -> None:
        """Init borders.

        5------1------6
        |      |      |
        4------+------2
        |      |      |
        8------3------7
        """

        # pre-black:
        # cls._borders = {
        #     0       | 0       | 0       | 0:            0,
        #     0       | 0       | 0       | cls.N.T:      0,
        #     0       | 0       | cls.N.R | 0:            0,
        #     0       | 0       | cls.N.R | cls.N.T:      curses.ACS_LLCORNER,     # 8
        #     0       | cls.N.B | 0       | 0:            0,
        #     0       | cls.N.B | 0       | cls.N.T:      curses.ACS_VLINE,
        #     0       | cls.N.B | cls.N.R | 0:            curses.ACS_ULCORNER,     # 5
        #     0       | cls.N.B | cls.N.R | cls.N.T:      curses.ACS_LTEE,         # 4
        #     cls.N.L | 0       | 0       | 0:            0,
        #     cls.N.L | 0       | 0       | cls.N.T:      curses.ACS_LRCORNER,     # 7
        #     cls.N.L | 0       | cls.N.R | 0:            curses.ACS_HLINE,
        #     cls.N.L | 0       | cls.N.R | cls.N.T:      curses.ACS_BTEE,         # 3
        #     cls.N.L | cls.N.B | 0       | 0:            curses.ACS_URCORNER,     # 6
        #     cls.N.L | cls.N.B | 0       | cls.N.T:      curses.ACS_RTEE,         # 2
        #     cls.N.L | cls.N.B | cls.N.R | 0:            curses.ACS_TTEE,         # 1
        #     cls.N.L | cls.N.B | cls.N.R | cls.N.T:      curses.ACS_PLUS,
        # }

        cls._borders = {
            0 | 0 | 0 | 0: 0,
            0 | 0 | 0 | cls.N.T: 0,
            0 | 0 | cls.N.R | 0: 0,
            0 | 0 | cls.N.R | cls.N.T: curses.ACS_LLCORNER,  # 8
            0 | cls.N.B | 0 | 0: 0,
            0 | cls.N.B | 0 | cls.N.T: curses.ACS_VLINE,
            0 | cls.N.B | cls.N.R | 0: curses.ACS_ULCORNER,  # 5
            0 | cls.N.B | cls.N.R | cls.N.T: curses.ACS_LTEE,  # 4
            cls.N.L | 0 | 0 | 0: 0,
            cls.N.L | 0 | 0 | cls.N.T: curses.ACS_LRCORNER,  # 7
            cls.N.L | 0 | cls.N.R | 0: curses.ACS_HLINE,
            cls.N.L | 0 | cls.N.R | cls.N.T: curses.ACS_BTEE,  # 3
            cls.N.L | cls.N.B | 0 | 0: curses.ACS_URCORNER,  # 6
            cls.N.L | cls.N.B | 0 | cls.N.T: curses.ACS_RTEE,  # 2
            cls.N.L | cls.N.B | cls.N.R | 0: curses.ACS_TTEE,  # 1
            cls.N.L | cls.N.B | cls.N.R | cls.N.T: curses.ACS_PLUS,
        }

    # -------------------------------------------------------------------------------

    def _get_border_symbol(self, y: int, x: int) -> tuple[int, int]:
        """Returns character and attribute."""

        assert self.grid[y][x]
        neighbors = 0

        if y > 0 and self.grid[y - 1][x]:
            neighbors |= self.N.T

        if x + 1 < self.ncols and self.grid[y][x + 1]:
            neighbors |= self.N.R

        if y + 1 < self.nlines and self.grid[y + 1][x]:
            neighbors |= self.N.B

        if x > 0 and self.grid[y][x - 1]:
            neighbors |= self.N.L

        attr = curses.A_REVERSE if self.attrs[y][x] else curses.A_NORMAL

        char = self._borders.get(neighbors)
        assert char
        return char, attr

    def __init__(
        self,
        win: curses.window,
        bkgd_grid: CharAttr = None,
        bkgd_box: CharAttr = None,
    ) -> None:
        """Create grid in `win`.

        Args:
            win: window to build grid in; uses entire surface.
            bkgd_grid: tuple(ch[,attr]) to apply to the grid.
            bkgd_box: tuple(ch[,attr]) to apply to boxes.
        """

        if not self._init_called:
            # one-time initializations
            self._init_called = True
            self._init_borders()
            libcurses.core.register_fkey(lambda key: self.redraw(), curses.KEY_REFRESH)
            libcurses.core.register_fkey(lambda key: self.redraw(), curses.ascii.FF)

        # this is the users window; we did not create it, but we will draw
        # the borders on it and display it.

        self.win = win
        if bkgd_grid is not None:
            win.bkgd(*bkgd_grid)
        self.bkgd_box = bkgd_box

        # the grid consumes the entire window.

        self.nlines, self.ncols = self.win.getmaxyx()
        self.begin_y, self.begin_x = self.win.getbegyx()

        self.grid = [[0 for x in range(self.ncols)] for y in range(self.nlines)]
        self.attrs = [[0 for x in range(self.ncols)] for y in range(self.nlines)]
        self._draw_box(self.nlines, self.ncols, 0, 0)
        self.boxes = [self.win]
        self.boxnames = {self.win: "grid"}
        self._builder: GridBuilder

        libcurses.core.register_fkey(
            lambda key: self.handle_term_resized_event(), curses.KEY_RESIZE
        )
        Mouse.enable()
        Mouse.add_internal_mouse_handler(self._handle_mouse_event)

        logger.trace(self)

    def __repr__(self) -> str:

        return (
            self.__class__.__name__
            + "("
            + ", ".join(
                [
                    f"nlines={self.nlines}",
                    f"ncols={self.ncols}",
                    f"begin_y={self.begin_y}",
                    f"begin_x={self.begin_x}",
                    f"winyx={self.winyx(self.win)}",
                ]
            )
            + ")"
        )

    def register_builder(self, func: GridBuilder) -> None:
        """Register `func` to add boxes to this grid.

        Configure KEY_RESIZE to call it whenever that event occurs.

        And call `func` now.
        """

        self._builder = func
        if self._builder is not None:
            self._builder()

    def _draw_box(
        self,
        nlines: int,
        ncols: int,
        begin_y: int,
        begin_x: int,
    ) -> None:
        """Creates a box on the grid of the given size at the given coordinates."""

        lasty = begin_y + nlines - 1
        lastx = begin_x + ncols - 1

        begin_y -= self.begin_y
        begin_x -= self.begin_x
        lasty -= self.begin_y
        lastx -= self.begin_x

        assert begin_y >= 0
        assert begin_x >= 0
        assert nlines >= 3
        assert ncols >= 3
        assert lasty < self.nlines
        assert lastx < self.ncols
        assert lasty <= self.nlines
        assert lastx <= self.ncols

        # Store a truthy integer at each position on the grid where a border
        # character is to be. The actual values (1..8) don't matter; they
        # correspond to the comment and doc in `_init_borders`.

        for x in range(1, ncols - 1):
            self.grid[begin_y][begin_x + x] = 1  # top
            self.grid[lasty][begin_x + x] = 3  # bottom

        for y in range(1, nlines - 1):
            self.grid[begin_y + y][lastx] = 2  # right
            self.grid[begin_y + y][begin_x] = 4  # left

        # corners
        self.grid[begin_y][begin_x] = 5
        self.grid[begin_y][lastx] = 6
        self.grid[lasty][lastx] = 7
        self.grid[lasty][begin_x] = 8

    # -------------------------------------------------------------------------------

    def border_attr(self, win: curses.window, direction: Grid.N, flag: int) -> None:
        """Set border attributes."""

        nlines, ncols = win.getmaxyx()
        begin_y, begin_x = win.getbegyx()

        if direction == self.N.L:
            for y in range(nlines):
                self.attrs[begin_y + y][begin_x - 1] = flag

        elif direction == self.N.R:
            for y in range(nlines):
                self.attrs[begin_y + y][begin_x + ncols] = flag

        elif direction == self.N.T:
            for x in range(ncols):
                self.attrs[begin_y - 1][begin_x + x] = flag

        elif direction == self.N.B:
            for x in range(ncols):
                self.attrs[begin_y + nlines][begin_x + x] = flag

    # -------------------------------------------------------------------------------

    def box(
        self,
        boxname: str,
        nlines: int,
        ncols: int,
        begin_y: int = 0,
        begin_x: int = 0,
        bkgd_box: CharAttr = None,
        left: Grid | curses.window | None = None,
        right: Grid | curses.window | None = None,
        top: Grid | curses.window | None = None,
        bottom: Grid | curses.window | None = None,
        left2r: curses.window | None = None,
        right2l: curses.window | None = None,
        top2b: curses.window | None = None,
        bottom2t: curses.window | None = None,
    ) -> curses.window:
        # pylint: disable=too-many-positional-arguments
        """Create box.

        Creates and returns a new `curses` window, after drawing a box
        around it on the grid, whose borders are collapsed with the borders
        of any adjacent boxes.

        Args:
            boxname: name of box.
            nlines: number of lines.
            ncols: number of columns.
                Size of box; size of curses-window is 1 less on each side.
                    +-----------+
                    |5x13 box   |
                    |surrounding|
                    |3x11 window|
                    +-----------+
            begin_y: upper-left line.
            begin_x: upper-left column.
                Upper-left corner of box on the grid, relative to a
                reference box if given, else relative to the overall grid.
                Positive values are measured from the top and left edges of
                the reference, negative values from the bottom and right edges.
            bkgd_box: tuple(ch[,attr]) to apply to boxes.
        Same-side spatial-reference parameters, type `curses.window` or `Grid`:
            left:       align left of this box with left of referenced window (or the grid).
            right:      align right of this box with right of referenced window (or the grid).
            top:        align top of this box with top of referenced window (or the grid).
            bottom:     align bottom of this box with bottom of referenced window (or the grid).
        Opposite-side spatial-reference parameters, type `curses.window` only:
            left2r:     align left of this box with right of referenced window.
            right2l:    align right of this box with left of referenced window.
            top2b:      align top of this box with bottom of referenced window.
            bottom2t:   align bottom of this box with top of referenced window.
        """

        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals

        # logger.trace("-" * 80)

        # logger.trace(
        #     f"boxname={boxname!r} nlines={nlines} ncols={ncols} "
        #     f"begin_y={begin_y} begin_x={begin_x}"
        # )

        # Determine dimensions/coordinates of upper-left corner of box on the grid.

        nlines, begin_y = self._getmaxbeg(
            boxname,
            0,
            nlines,
            begin_y,
            top,
            top2b,
            bottom,
            bottom2t,
            "top",
            "top2b",
            "bottom",
            "bottom2t",
        )

        ncols, begin_x = self._getmaxbeg(
            boxname,
            1,
            ncols,
            begin_x,
            left,
            left2r,
            right,
            right2l,
            "left",
            "left2r",
            "right",
            "right2l",
        )

        # logger.trace(
        #     f"boxname={boxname!r} nlines={nlines} ncols={ncols} "
        #     f"begin_y={begin_y} begin_x={begin_x}"
        # )
        self._draw_box(nlines, ncols, begin_y, begin_x)

        # If this box is known, then resize (instead of creating) the window.

        if known := [k for k, v in self.boxnames.items() if v == boxname]:
            win = known[0]
            win.resize(nlines - 2, ncols - 2)
            win.move(0, 0)
            win.mvwin(begin_y + 1, begin_x + 1)
            self.boxes.append(win)
        else:
            # create window inside the box
            win = curses.newwin(nlines - 2, ncols - 2, begin_y + 1, begin_x + 1)

            if bkgd_box:
                win.bkgd(*bkgd_box)
            elif self.bkgd_box:
                win.bkgd(*self.bkgd_box)

            self.boxes.append(win)
            self.boxnames[win] = boxname

        logger.trace(f"winyx={self.winyx(win)}")
        return win

    # -------------------------------------------------------------------------------

    def getbegyx(self) -> tuple[int, int]:
        """Docstring."""

        return self.win.getbegyx()

    def getmaxyx(self) -> tuple[int, int]:
        """Docstring."""

        return self.win.getmaxyx()

    # -------------------------------------------------------------------------------

    def _getmaxbeg(
        self,
        boxname: str,
        idx: int,
        length: int,
        i_begin: int,
        lo: Grid | curses.window | None,
        lo2hi: Grid | curses.window | None,
        hi: Grid | curses.window | None,
        hi2lo: Grid | curses.window | None,
        lo_name: str,
        lo2hi_name: str,
        hi_name: str,
        hi2lo_name: str,
    ) -> tuple[int, int]:
        # pylint: disable=too-many-positional-arguments
        """Returns the length and beginning coordinate of the given dimension.

        `_getmaxbeg` is a portmanteau of `getmaxyx` and `getbegyx`.
        """

        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches

        dimension = ["nlines", "ncols"][idx]
        meta = f"boxname={boxname!r}, dimension={dimension!r}"

        # logger.trace("-" * 80)

        # -------------------------------------------------------------------------------

        if not lo and not lo2hi and not hi and not hi2lo:
            # calling like curses.newwin()
            # logger.trace(f"{meta}, length={length} i_begin={i_begin}")
            return length, i_begin

        # -------------------------------------------------------------------------------

        if lo and lo2hi:
            raise ValueError(f"{meta}, {lo_name!r} and {lo2hi_name!r} are mutually exclusive")

        if hi and hi2lo:
            raise ValueError(f"{meta}, {hi_name!r} and {hi2lo_name!r} are mutually exclusive")

        # -------------------------------------------------------------------------------

        if lo2hi == self:
            raise ValueError(
                f"{meta}, use {lo_name!r} to reference the grid, not {lo2hi_name!r}"
            )

        if hi2lo == self:
            raise ValueError(
                f"{meta}, use {hi_name!r} to reference the grid, not {hi2lo_name!r}"
            )

        # -------------------------------------------------------------------------------

        if (lo or lo2hi) and (hi or hi2lo):
            if length:
                raise ValueError(f"{meta}, non-zero length={length} allows lo or hi, not both")
        elif not length:
            raise ValueError(f"{meta}, zero length={length} requires both lo and hi")

        # -------------------------------------------------------------------------------

        if lo:
            if lo == self:
                begin = self.win.getbegyx()[idx]
                # logger.trace(f"{meta}, begin={self.win.getbegyx()[idx]}")
            else:
                begin = lo.getbegyx()[idx] - 1  # to reach the border
                # logger.trace(f"{meta}, begin={lo.getbegyx()[idx] - 1}")
        elif lo2hi:
            begin = lo2hi.getbegyx()[idx] + lo2hi.getmaxyx()[idx]
            # logger.trace(f"{meta}, begin={lo2hi.getbegyx()[idx]} + {lo2hi.getmaxyx()[idx]}")
        else:
            begin = None
            # logger.trace(f"{meta}, begin=None")

        # -------------------------------------------------------------------------------

        if hi:
            if hi == self:
                last = self.win.getbegyx()[idx] + self.win.getmaxyx()[idx] - 1
                # logger.trace(
                #     f"{meta}, last={self.win.getbegyx()[idx]} + {self.win.getmaxyx()[idx]} - 1"
                # )
            else:
                last = hi.getbegyx()[idx] + hi.getmaxyx()[idx]
                # logger.trace(f"{meta}, last={hi.getbegyx()[idx]} + {hi.getmaxyx()[idx]}")
        elif hi2lo:
            last = hi2lo.getbegyx()[idx] - 1
            # logger.trace(f"{meta}, last={hi2lo.getbegyx()[idx]} - 1")
        else:
            last = None
            # logger.trace(f"{meta}, last=None")

        # -------------------------------------------------------------------------------

        if begin is not None and last is not None:
            assert not length
            length = last - begin + 1
            # logger.trace(f"{meta}, length={length} = {last} - {begin}, begin={begin}")
            return length, i_begin + begin

        assert length
        if begin is not None:
            # logger.trace(f"{meta}, length={length}, begin={begin}")
            return length, i_begin + begin

        assert last
        begin = last - length + 1
        # logger.trace(f"{meta}, length={length}, begin={begin}")
        return length, i_begin + begin

    # -------------------------------------------------------------------------------

    def _render_boxes(self) -> None:

        for y in range(self.nlines):
            for x in range(self.ncols):
                if self.grid[y][x]:
                    symbol, attr = self._get_border_symbol(y, x)

                    try:
                        self.win.addch(y, x, symbol, attr)
                        # logger.trace(f'self={self} y={y} x={x}')

                    except curses.error as err:
                        # expect an error in the lower-right corner.
                        if y != self.nlines - 1 or x != self.ncols - 1:
                            _d1 = y - (self.nlines - 1)
                            _d2 = x - (self.ncols - 1)
                            logger.error(
                                f"y={y} x={x} _d1={_d1} _d2={_d2} err={err} self={self}"
                            )
                            # raise

    def redraw(self) -> None:
        """Redraw grid."""

        with libcurses.core.LOCK:
            self.win.clear()
            self.grid = [[0 for x in range(self.ncols)] for y in range(self.nlines)]

            self._draw_box(self.nlines, self.ncols, 0, 0)

            for win in self.boxes[1:]:
                nlines, ncols = win.getmaxyx()
                begin_y, begin_x = win.getbegyx()
                self._draw_box(nlines + 2, ncols + 2, begin_y - 1, begin_x - 1)

            self._render_boxes()

            for win in self.boxes:
                win.touchwin()
                win.noutrefresh()

            curses.doupdate()

    def refresh(self) -> None:
        """Noutrefresh grid."""

        for win in self.boxes:
            win.touchwin()
            win.noutrefresh()

        with libcurses.core.LOCK:
            curses.doupdate()

    def winyx(self, win: curses.window) -> str:
        """Return string of window coordinates."""

        # pylint: disable=consider-using-f-string
        return "(boxname={!r}, l={} c={} y={} x={})".format(
            self.boxnames[win], *win.getmaxyx(), *win.getbegyx()
        )

    def getwin(self, y: int, x: int) -> curses.window | None:
        """Return window at y, x."""

        for win in self.boxes[1:]:
            if win.enclose(y, x):
                return win
        return None

    # ------------------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------------------

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

    def handle_term_resized_event(self) -> None:
        """Respond to terminal having been resized."""

        # pylint: disable=no-member
        logger.warning(f"old={self.nlines}x{self.ncols} new={curses.LINES}x{curses.COLS}")
        self.nlines, self.ncols = curses.LINES, curses.COLS
        self.win.resize(self.nlines, self.ncols)
        self.grid = [[0 for x in range(self.ncols)] for y in range(self.nlines)]
        self.attrs = [[0 for x in range(self.ncols)] for y in range(self.nlines)]
        self.boxes = self.boxes[:1]
        if self._builder is not None:
            self._builder()
        # self.redraw()

    def _handle_mouse_event(self, mouse: MouseEvent, args: Any) -> bool:
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

    def _resize(
        self,
        mouse: MouseEvent,
        left: curses.window | None = None,
        right: curses.window | None = None,
        upper: curses.window | None = None,
        lower: curses.window | None = None,
    ) -> None:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-positional-arguments
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
