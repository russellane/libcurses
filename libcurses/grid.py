"""Group of resizable windows.

This module provides the `Grid` class.
"""

from __future__ import annotations

import copy
import curses
import curses.ascii
from dataclasses import dataclass
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

# Border offset constants
BORDER_WIDTH = 1
WINDOW_BORDER_TOTAL = 2  # 1 border on each side


@dataclass
class ResizeContext:
    """Context for an interactive resize operation."""

    mouse: MouseEvent
    left: curses.window | None = None
    right: curses.window | None = None
    upper: curses.window | None = None
    lower: curses.window | None = None
    kb_resize_mode: bool = False

    @property
    def is_horizontal(self) -> bool:
        """True if resizing left/right windows."""
        return self.left is not None or self.right is not None

    @property
    def is_vertical(self) -> bool:
        """True if resizing upper/lower windows."""
        return self.upper is not None or self.lower is not None


@dataclass
class DimensionParams:
    """Parameters for calculating a dimension (either horizontal or vertical)."""

    lo: "Grid | curses.window | None" = None
    lo2hi: "Grid | curses.window | None" = None
    hi: "Grid | curses.window | None" = None
    hi2lo: "Grid | curses.window | None" = None
    lo_name: str = ""
    lo2hi_name: str = ""
    hi_name: str = ""
    hi2lo_name: str = ""


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

        self._draw_box(nlines, ncols, begin_y, begin_x)

        # If this box is known, then resize (instead of creating) the window.

        if known := [k for k, v in self.boxnames.items() if v == boxname]:
            win = known[0]
            win.resize(nlines - WINDOW_BORDER_TOTAL, ncols - WINDOW_BORDER_TOTAL)
            win.move(0, 0)
            win.mvwin(begin_y + BORDER_WIDTH, begin_x + BORDER_WIDTH)
            self.boxes.append(win)
        else:
            # create window inside the box
            win = curses.newwin(
                nlines - WINDOW_BORDER_TOTAL,
                ncols - WINDOW_BORDER_TOTAL,
                begin_y + BORDER_WIDTH,
                begin_x + BORDER_WIDTH,
            )

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
    # Dimension calculation helpers
    # -------------------------------------------------------------------------------

    def _validate_dimension_refs(self, meta: str, length: int, params: DimensionParams) -> None:
        """Validate spatial reference parameters for a dimension."""
        if params.lo and params.lo2hi:
            raise ValueError(
                f"{meta}, {params.lo_name!r} and {params.lo2hi_name!r} are mutually exclusive"
            )

        if params.hi and params.hi2lo:
            raise ValueError(
                f"{meta}, {params.hi_name!r} and {params.hi2lo_name!r} are mutually exclusive"
            )

        if params.lo2hi == self:
            raise ValueError(
                f"{meta}, use {params.lo_name!r} to reference grid, not {params.lo2hi_name!r}"
            )

        if params.hi2lo == self:
            raise ValueError(
                f"{meta}, use {params.hi_name!r} to reference grid, not {params.hi2lo_name!r}"
            )

        has_lo = params.lo or params.lo2hi
        has_hi = params.hi or params.hi2lo

        if has_lo and has_hi:
            if length:
                raise ValueError(f"{meta}, non-zero length={length} allows lo or hi, not both")
        elif not length:
            raise ValueError(f"{meta}, zero length={length} requires both lo and hi")

    def _calculate_begin_from_refs(self, idx: int, params: DimensionParams) -> int | None:
        """Calculate begin coordinate from low-side references."""
        if params.lo:
            if params.lo == self:
                return self.win.getbegyx()[idx]
            return params.lo.getbegyx()[idx] - BORDER_WIDTH
        if params.lo2hi:
            return params.lo2hi.getbegyx()[idx] + params.lo2hi.getmaxyx()[idx]
        return None

    def _calculate_end_from_refs(self, idx: int, params: DimensionParams) -> int | None:
        """Calculate end coordinate from high-side references."""
        if params.hi:
            if params.hi == self:
                return self.win.getbegyx()[idx] + self.win.getmaxyx()[idx] - 1
            return params.hi.getbegyx()[idx] + params.hi.getmaxyx()[idx]
        if params.hi2lo:
            return params.hi2lo.getbegyx()[idx] - 1
        return None

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
        """Returns the length and beginning coordinate of the given dimension.

        `_getmaxbeg` is a portmanteau of `getmaxyx` and `getbegyx`.
        """
        # No references - use input values directly
        if not lo and not lo2hi and not hi and not hi2lo:
            return length, i_begin

        dimension = ["nlines", "ncols"][idx]
        meta = f"boxname={boxname!r}, dimension={dimension!r}"

        params = DimensionParams(
            lo=lo,
            lo2hi=lo2hi,
            hi=hi,
            hi2lo=hi2lo,
            lo_name=lo_name,
            lo2hi_name=lo2hi_name,
            hi_name=hi_name,
            hi2lo_name=hi2lo_name,
        )

        # Validate reference combinations
        self._validate_dimension_refs(meta, length, params)

        # Calculate begin and end from references
        begin = self._calculate_begin_from_refs(idx, params)
        end = self._calculate_end_from_refs(idx, params)

        # Resolve length and begin
        if begin is not None and end is not None:
            assert not length
            length = end - begin + 1
            return length, i_begin + begin

        assert length
        if begin is not None:
            return length, i_begin + begin

        assert end is not None
        begin = end - length + 1
        return length, i_begin + begin

    # -------------------------------------------------------------------------------

    def _render_boxes(self) -> None:

        for y in range(self.nlines):
            for x in range(self.ncols):
                if self.grid[y][x]:
                    symbol, attr = self._get_border_symbol(y, x)

                    try:
                        self.win.addch(y, x, symbol, attr)
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
                self._draw_box(
                    nlines + WINDOW_BORDER_TOTAL,
                    ncols + WINDOW_BORDER_TOTAL,
                    begin_y - BORDER_WIDTH,
                    begin_x - BORDER_WIDTH,
                )

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
        nlines, ncols = win.getmaxyx()
        begin_y, begin_x = win.getbegyx()
        return f"(boxname={self.boxnames[win]!r}, l={nlines} c={ncols} y={begin_y} x={begin_x})"

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
            return False

        char = self.win.inch(mouse.y, mouse.x) & ~curses.A_COLOR

        if char == curses.ACS_VLINE:
            left = self.getwin(mouse.y, mouse.x - 1)
            right = self.getwin(mouse.y, mouse.x + 1)
            self._resize(mouse, left=left, right=right)
            return True

        if char == curses.ACS_HLINE:
            upper = self.getwin(mouse.y - 1, mouse.x)
            lower = self.getwin(mouse.y + 1, mouse.x)
            self._resize(mouse, upper=upper, lower=lower)
            return True

        return False

    # --------------------------------------------------------------------------
    # Resize helper methods
    # --------------------------------------------------------------------------

    def _highlight_resize_border(self, ctx: ResizeContext, highlight: bool) -> None:
        """Set or clear highlight on the active resize border."""
        if ctx.left:
            self.border_attr(ctx.left, self.N.R, highlight)
        elif ctx.right:
            self.border_attr(ctx.right, self.N.L, highlight)
        if ctx.upper:
            self.border_attr(ctx.upper, self.N.B, highlight)
        elif ctx.lower:
            self.border_attr(ctx.lower, self.N.T, highlight)

    def _is_resize_exit_key(self, key: int | None) -> bool:
        """Return True if key should exit resize mode."""
        if not key:
            return True
        if key in (curses.ascii.LF, curses.ascii.CR, curses.ascii.ESC, curses.KEY_ENTER):
            return True
        return False

    def _handle_mouse_drag_input(self, key: int) -> tuple[MouseEvent | None, bool]:
        """Handle mouse input in drag mode.

        Returns (mouse_event, should_exit). If should_exit is True, exit resize.
        If mouse_event is None and should_exit is False, continue to next iteration.
        """
        if key != curses.KEY_MOUSE:
            return None, False  # Continue to next iteration

        mouse = MouseEvent()
        logger.trace(f"mouse={mouse!r}")

        if mouse.is_released:
            return None, True  # Exit resize

        if not mouse.is_moving:
            return None, False  # Continue to next iteration

        return mouse, False

    def _emulate_key_from_scroll(self, ctx: ResizeContext, mouse: MouseEvent) -> int | None:
        """Convert scroll wheel events to arrow key codes.

        Returns key code, None to exit, or 0 for no action.
        """
        if mouse.button == 4:
            # Scroll up - emulate left and up arrows
            if ctx.is_horizontal:
                return curses.KEY_LEFT
            if ctx.is_vertical:
                return curses.KEY_UP
        if mouse.button == 5:
            # Scroll down - emulate right and down arrows
            if ctx.is_horizontal:
                return curses.KEY_RIGHT
            if ctx.is_vertical:
                return curses.KEY_DOWN
        if mouse.nclicks or mouse.is_released:
            return None  # Signal to exit resize
        return 0  # No action

    def _emulate_mouse_from_arrow(self, key: int, last_mouse: MouseEvent) -> MouseEvent | None:
        """Convert arrow key to mouse movement. Returns new MouseEvent or None."""
        if key == curses.KEY_LEFT:
            if last_mouse.x <= self._mouse_min_x:
                return None
            mouse = copy.copy(last_mouse)
            mouse.x -= 1
        elif key == curses.KEY_RIGHT:
            if last_mouse.x >= self._mouse_max_x - 1:
                return None
            mouse = copy.copy(last_mouse)
            mouse.x += 1
        elif key == curses.KEY_UP:
            if last_mouse.y <= self._mouse_min_y:
                return None
            mouse = copy.copy(last_mouse)
            mouse.y -= 1
        elif key == curses.KEY_DOWN:
            if last_mouse.y >= self._mouse_max_y:
                return None
            mouse = copy.copy(last_mouse)
            mouse.y += 1
        else:
            return None

        mouse.bstate = curses.REPORT_MOUSE_POSITION
        mouse.is_moving = True
        mouse.nclicks = 0
        return mouse

    def _can_shrink_windows(
        self, ctx: ResizeContext, mouse: MouseEvent, last_mouse: MouseEvent
    ) -> bool:
        """Check if the proposed resize operation is allowed."""
        if mouse.x < last_mouse.x and ctx.left:
            _, ncols = ctx.left.getmaxyx()
            if ncols <= 1:
                logger.trace(f"cannot shrink left={self.winyx(ctx.left)}")
                return False

        if mouse.x > last_mouse.x and ctx.right:
            _, ncols = ctx.right.getmaxyx()
            if ncols <= 1:
                logger.trace(f"cannot shrink right={self.winyx(ctx.right)}")
                return False

        if mouse.y < last_mouse.y and ctx.upper:
            nlines, _ = ctx.upper.getmaxyx()
            if nlines <= 1:
                logger.trace(f"cannot shrink upper={self.winyx(ctx.upper)}")
                return False

        if mouse.y > last_mouse.y and ctx.lower:
            nlines, _ = ctx.lower.getmaxyx()
            if nlines <= 1:
                logger.trace(f"cannot shrink lower={self.winyx(ctx.lower)}")
                return False

        return True

    def _perform_horizontal_resize(
        self, ctx: ResizeContext, mouse: MouseEvent, last_mouse: MouseEvent
    ) -> bool:
        """Perform horizontal resize. Returns True if resize occurred."""
        resized = False

        if mouse.x < last_mouse.x:
            if ctx.left:
                nlines, ncols = ctx.left.getmaxyx()
                ctx.left.resize(nlines, ncols - 1)
                resized = True
            if ctx.right:
                begin_y, begin_x = ctx.right.getbegyx()
                ctx.right.mvwin(begin_y, begin_x - 1)
                nlines, ncols = ctx.right.getmaxyx()
                ctx.right.resize(nlines, ncols + 1)

        elif mouse.x > last_mouse.x:
            if ctx.right:
                nlines, ncols = ctx.right.getmaxyx()
                ctx.right.resize(nlines, ncols - 1)
                resized = True
                begin_y, begin_x = ctx.right.getbegyx()
                ctx.right.mvwin(begin_y, begin_x + 1)
            if ctx.left:
                nlines, ncols = ctx.left.getmaxyx()
                ctx.left.resize(nlines, ncols + 1)

        return resized

    def _perform_vertical_resize(
        self, ctx: ResizeContext, mouse: MouseEvent, last_mouse: MouseEvent
    ) -> bool:
        """Perform vertical resize. Returns True if resize occurred."""
        resized = False

        if mouse.y < last_mouse.y:
            if ctx.upper:
                nlines, ncols = ctx.upper.getmaxyx()
                ctx.upper.resize(nlines - 1, ncols)
                resized = True
            if ctx.lower:
                begin_y, begin_x = ctx.lower.getbegyx()
                nlines, ncols = ctx.lower.getmaxyx()
                ctx.lower.mvwin(begin_y - 1, begin_x)
                ctx.lower.resize(nlines + 1, ncols)

        elif mouse.y > last_mouse.y:
            if ctx.lower:
                nlines, ncols = ctx.lower.getmaxyx()
                ctx.lower.resize(nlines - 1, ncols)
                resized = True
                begin_y, begin_x = ctx.lower.getbegyx()
                ctx.lower.mvwin(begin_y + 1, begin_x)
            if ctx.upper:
                nlines, ncols = ctx.upper.getmaxyx()
                ctx.upper.resize(nlines + 1, ncols)

        return resized

    def _process_kb_resize_input(
        self, ctx: ResizeContext, key: int, last_mouse: MouseEvent
    ) -> tuple[MouseEvent | None, bool]:
        """Process input in keyboard resize mode.

        Returns (mouse_event, should_exit).
        """
        if key == curses.KEY_MOUSE:
            mouse = MouseEvent()
            logger.trace(f"mouse={mouse!r}")

            emulated_key = self._emulate_key_from_scroll(ctx, mouse)
            if emulated_key is None:
                return None, True  # Exit
            if emulated_key == 0:
                return None, False  # Continue
            key = emulated_key

        new_mouse = self._emulate_mouse_from_arrow(key, last_mouse)
        if new_mouse is None:
            return None, False  # Continue
        return new_mouse, False

    # --------------------------------------------------------------------------
    # Main resize method
    # --------------------------------------------------------------------------

    def _resize(
        self,
        mouse: MouseEvent,
        left: curses.window | None = None,
        right: curses.window | None = None,
        upper: curses.window | None = None,
        lower: curses.window | None = None,
    ) -> None:
        """Interactive resize of windows adjacent to a border."""
        ctx = ResizeContext(
            mouse=mouse,
            left=left,
            right=right,
            upper=upper,
            lower=lower,
            kb_resize_mode=mouse.is_ctrl or (mouse.nclicks == 2),
        )
        resized = False

        while True:
            last_mouse = ctx.mouse

            if resized:
                self.redraw()
                resized = False

            # Highlight active border
            self._highlight_resize_border(ctx, highlight=True)
            self.redraw()

            key = getkey(None, no_mouse=True)

            # Clear highlight
            self._highlight_resize_border(ctx, highlight=False)
            self.redraw()

            # Check for exit
            if self._is_resize_exit_key(key):
                return

            if key is None:
                continue

            if key == curses.ascii.FF:
                self.redraw()
                continue

            # Get new mouse position from input
            if not ctx.kb_resize_mode:
                new_mouse, should_exit = self._handle_mouse_drag_input(key)
                if should_exit:
                    return
                if new_mouse is None:
                    continue
                ctx.mouse = new_mouse
            else:
                new_mouse, should_exit = self._process_kb_resize_input(ctx, key, last_mouse)
                if should_exit:
                    return
                if new_mouse is None:
                    continue
                ctx.mouse = new_mouse

            # Validate resize is possible
            if not self._can_shrink_windows(ctx, ctx.mouse, last_mouse):
                continue

            # Perform the resize
            resized = self._perform_horizontal_resize(ctx, ctx.mouse, last_mouse)
            resized = self._perform_vertical_resize(ctx, ctx.mouse, last_mouse) or resized
