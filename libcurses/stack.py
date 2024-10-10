"""curses utilities."""

import curses

from libcurses.border import Border
from libcurses.bw import BorderedWindow

__all__ = ["WindowStack"]


class WindowStack:
    """Vertical stack of windows."""

    def __init__(self, neighbor_left: BorderedWindow, padding_y: int) -> None:
        """Create a vertical stack of windows with 'border-collapse: collapse'.

        A visual stack, not a push-pop thing... think smokestack or stovepipe.
        """

        self.neighbor_left = neighbor_left
        self.padding_y = padding_y
        self.begin_x = self.neighbor_left.begin_x + self.neighbor_left.ncols - 1
        self.windows: list[BorderedWindow] = []

    def redraw(self) -> None:
        """Redraw stack."""

        for w in self.windows:
            w.redraw()

    def refresh(self) -> None:
        """Refresh stack."""

        for w in self.windows:
            w.refresh()

    def get_border(self, loc: int) -> Border:
        """Return the appropriate Border for a window based on its location in the stack."""

        first = loc == 0
        final = loc == len(self.windows) - 1

        # pylint: disable=no-else-return
        if first:
            if not final:
                # first with more to come
                return Border(tl=curses.ACS_TTEE, bl=curses.ACS_LTEE, br=curses.ACS_RTEE)
            else:
                # first and final
                return Border(tl=curses.ACS_TTEE, bl=curses.ACS_BTEE)
        else:
            if not final:
                # additional with more to come
                return Border(
                    tl=curses.ACS_LTEE,
                    tr=curses.ACS_RTEE,
                    bl=curses.ACS_LTEE,
                    br=curses.ACS_RTEE,
                )
            else:
                # additional and final
                return Border(tl=curses.ACS_LTEE, tr=curses.ACS_RTEE, bl=curses.ACS_BTEE)

    def append(self, nlines: int, ncols: int) -> BorderedWindow:
        """Create window at bottom of stack."""

        first = len(self.windows) == 0
        final = not nlines

        if first:
            # join first window to neighbor on left, aligning tops, overlapping
            # my left and his right sides.
            begin_y = self.neighbor_left.begin_y
        else:
            # join additional windows to neighbor above, overlapping top and bottom sides.
            begin_y = self.windows[-1].begin_y + self.windows[-1].nlines - 1

        if final:
            if first:
                # first and final, full height
                nlines = self.neighbor_left.nlines
            else:
                # additional and final; variable height
                nlines = self.neighbor_left.nlines - (
                    (self.windows[-1].begin_y + self.windows[-1].nlines - 1) - self.padding_y
                )

        bw = BorderedWindow(nlines, ncols, begin_y, self.begin_x)
        self.windows.append(bw)
        bw.border(self.get_border(len(self.windows) - 1))
        return bw

    def insert(self, nlines: int, ncols: int, loc: int = 0) -> None:
        """Insert new BorderedWindow at loc."""

        if len(self.windows) == 0:
            self.append(nlines, ncols)
            return

        # loc 0 or -3 window one
        # loc 1 or -2 window two
        # loc 2 or -1 window three

        min_ = -len(self.windows)
        max_ = len(self.windows) - 1

        if loc < min_ or loc > max_:
            raise ValueError(f"loc {loc} is not {min_}..{max_}")

        if loc < 0:
            loc = len(self.windows) + loc

        # Create new BorderedWindow at this location
        loc_y = self.windows[loc].begin_y
        loc_x = self.windows[loc].begin_x

        # shrink last window by height of new window
        bw = self.windows[-1]
        new_nlines = bw.nlines - nlines
        if new_nlines < 3:
            # pylint: disable=consider-using-f-string
            raise ValueError(
                "Can't shrink: current nlines {} minus {} ({}) is < 3".format(
                    bw.nlines, nlines, new_nlines
                )
            )
        bw.resize(new_nlines + 1, bw.ncols)

        # slide windows down
        for bw in reversed(self.windows[loc:]):
            bw.mvwin(bw.begin_y + nlines - 1, bw.begin_x)

        # insert new window
        bw = BorderedWindow(nlines, ncols, loc_y, loc_x)
        self.windows.insert(loc, bw)

        # adjust borders of all windows
        for idx, _bw in enumerate(self.windows):
            _bw.border(self.get_border(idx))
