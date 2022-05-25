"""Bordered Window."""

import curses

from libcurses.border import Border


class BorderedWindow:
    """Bordered Window."""

    def __init__(self, nlines, ncols, begin_y, begin_x, _border=None):
        """Create new bordered window with the given dimensions and optional border stylings.

        A bordered window is composed of two windows:
            1. an outer (border) window, which draws a box around
            2. an inner (working) window.

        border=None means use default border stylings, not no border.
        """

        self.nlines = nlines
        self.ncols = ncols
        self.begin_y = begin_y
        self.begin_x = begin_x

        self.b = curses.newwin(nlines, ncols, begin_y, begin_x)
        self.w = curses.newwin(
            self.nlines - 2, self.ncols - 2, self.begin_y + 1, self.begin_x + 1
        )

        self.w.scrollok(True)
        self.w.idlok(True)
        self.w.leaveok(False)
        self.w.keypad(True)
        self.w.refresh()

        self.border(_border or Border())

    def __repr__(self):

        # getmaxyx does not return the maximum values for y and x, as the name indicates.
        # https://docs.python.org/3/library/curses.html#curses.window.getmaxyx
        # Return a tuple (y, x) of the height and width of the window.

        return (
            self.__class__.__name__
            + "("
            + ", ".join(
                [
                    f"nlines={self.nlines}",
                    f"ncols={self.ncols}",
                    f"begin_y={self.begin_y}",
                    f"begin_x={self.begin_x}",
                    f"b=(getbegyx={self.b.getbegyx()}, getmaxyx={self.b.getmaxyx()})",
                    f"w=(getbegyx={self.w.getbegyx()}, getmaxyx={self.w.getmaxyx()})",
                ]
            )
            + ")"
        )

    def redraw(self):
        """Redraw window."""

        self.b.redrawwin()
        self.w.redrawwin()

    def refresh(self):
        """Refresh window."""

        self.b.refresh()
        self.w.refresh()

    def border(self, _border):
        """Set window border."""

        self.b.border(*_border)

    def resize(self, nlines, ncols):
        """Resize window."""

        # constrain cursor to new dimensions
        for w in (self.b, self.w):
            y, x = w.getyx()
            w.move(min(y, nlines - 1), min(x, ncols - 1))

        # before resizing windows ;)
        self.b.resize(nlines, ncols)
        self.w.resize(nlines - 2, ncols - 2)

        self.nlines = nlines
        self.ncols = ncols

    def mvwin(self, new_y, new_x):
        """Move window."""

        self.b.mvwin(new_y, new_x)
        self.w.mvwin(new_y + 1, new_x + 1)
        self.begin_y, self.begin_x = new_y, new_x
        self.refresh()

    def addstr(self, *args):
        """Add strings to window."""

        self.w.addstr(*args)
