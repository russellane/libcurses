import curses

import libcurses
from libcurses.grid import Grid


def test_stub() -> None:
    """Make pytest happy to have a test to run, or pytest will exit non-zero."""


def _test_mouse(win: curses.window) -> None:
    """Docstring."""

    _, c2, c3 = setup_test(win)
    grid = Grid(win, bkgd_grid=(ord("+"), c2), bkgd_box=(ord("."), c3))

    ul = grid.box("ul", grid.nlines // 2, grid.ncols // 2, left=grid, top=grid)
    ur = grid.box("ur", 0, 0, left2r=ul, right=grid, top=ul, bottom=ul)
    ll = grid.box("ll", 0, 0, left=grid, right=ul, top2b=ul, bottom=grid)
    lr = grid.box("lr", 0, 0, left2r=ll, right=grid, top2b=ur, bottom=grid)
    ul.scrollok(True)
    ur.scrollok(True)
    ll.scrollok(True)
    lr.scrollok(True)
    grid.redraw()

    win = ul
    win.keypad(True)

    while (line := libcurses.getline(win)) is not None:
        for w in (ul, ur, ll, lr):
            w.addstr(f"{grid.winyx(w)} line={line!r}\n")
            w.noutrefresh()

    curses.endwin()


def setup_test(win: curses.window) -> tuple[int, int, int]:
    """Docstring."""
    #                   fg                  bg
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
    c1 = curses.color_pair(1)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    c2 = curses.color_pair(2)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_WHITE)
    c3 = curses.color_pair(3)
    win.clear()
    win.bkgd(ord("*"), c1)
    return c1, c2, c3


if __name__ == "__main__":
    libcurses.wrapper(_test_mouse)
