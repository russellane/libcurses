import contextlib
import curses

from loguru import logger

import libcurses
from libcurses.grid import Grid


def test_stub() -> None:
    pass


# -------------------------------------------------------------------------------


def main1(win: curses.window) -> None:

    win.clear()
    win.refresh()
    nlines, ncols = win.getmaxyx()
    grid = Grid(win)
    grid.box("1", 5, 5, begin_y=3, begin_x=3)
    grid.box("2", 3, 3, begin_y=0, begin_x=ncols - 3)
    grid.box("3", 3, 3, begin_y=nlines - 4, begin_x=ncols - 4)  # problem
    grid.box("4", 3, 3, begin_y=nlines - 5, begin_x=2)

    #
    grid.box("5", 5, 10, begin_y=2, begin_x=20)
    grid.box("6", 5, 10, begin_y=4, begin_x=20)

    grid.box("7", 5, 10, begin_y=2, begin_x=40)
    grid.box("8", 5, 10, begin_y=5, begin_x=40)  # problem

    grid.box("9", 5, 10, begin_y=2, begin_x=60)
    grid.box("10", 5, 10, begin_y=6, begin_x=60)

    grid.box("11", 5, 10, begin_y=2, begin_x=80)
    grid.box("12", 5, 10, begin_y=7, begin_x=80)  # problem

    grid.box("13", 5, 10, begin_y=2, begin_x=100)
    grid.box("14", 5, 10, begin_y=8, begin_x=100)

    #
    grid.box("15", 3, 5, begin_y=20, begin_x=4)
    grid.box("16", 3, 5, begin_y=20, begin_x=8)
    grid.box("17", 3, 5, begin_y=20, begin_x=12)

    grid.box("18", 3, 5, begin_y=20, begin_x=20)
    grid.box("19", 3, 5, begin_y=20, begin_x=23)
    grid.box("20", 3, 5, begin_y=20, begin_x=26)  # problem

    grid.box("21", 3, 5, begin_y=20, begin_x=36)
    grid.box("22", 3, 5, begin_y=20, begin_x=40)
    grid.box("23", 3, 5, begin_y=20, begin_x=44)

    grid.box("24", 3, 5, begin_y=20, begin_x=52)
    grid.box("25", 3, 5, begin_y=20, begin_x=57)
    grid.box("26", 3, 5, begin_y=20, begin_x=62)  # problem

    grid.box("27", 3, 5, begin_y=20, begin_x=68)
    grid.box("28", 3, 5, begin_y=20, begin_x=72)
    grid.box("29", 3, 5, begin_y=20, begin_x=76)

    prompt(grid, win)
    curses.endwin()


# -------------------------------------------------------------------------------


def main3(win: curses.window) -> None:

    #    0----+----1----+----2----+----3
    #  0 +--------+--------+--------+
    #  1 |        |        |        |
    #  2 |12345678|12345678|12345678|
    #  3 |        |        |        |
    #  4 +--------+--------+--------+
    #  5 |        |        |        |
    #  6 |12345678|12345678|12345678|
    #  7 |        |        |        |
    #  8 +--------+--------+--------+
    #  9 |        |        |        |
    # 10 |12345678|12345678|12345678|
    # 11 |        |        |        |
    # 12 +--------+--------+--------+

    win.clear()
    win.refresh()
    grid = Grid(win)

    grid.box("a", 5, 10, begin_y=0, begin_x=0)
    grid.box("b", 5, 10, begin_y=0, begin_x=9)
    grid.box("c", 5, 10, begin_y=0, begin_x=18)

    grid.box("d", 5, 10, begin_y=4, begin_x=0)
    grid.box("e", 5, 10, begin_y=4, begin_x=9)
    grid.box("f", 5, 10, begin_y=4, begin_x=18)

    grid.box("g", 5, 10, begin_y=8, begin_x=0)
    grid.box("h", 5, 10, begin_y=8, begin_x=9)
    grid.box("i", 5, 10, begin_y=8, begin_x=18)

    for idx, w in enumerate(grid.boxes):
        w.addstr(str(idx))

    prompt(grid, win)
    curses.endwin()


# -------------------------------------------------------------------------------


@logger.catch
def main4(win: curses.window) -> None:

    _, c2, c3 = setup_test(win)

    _test_backgrounds(win, c2, c3, msg="win")

    nlines, ncols = win.getmaxyx()
    for i in range(0, 10, 2):
        logger.success(f"iteration {i}")
        begin_y = i
        begin_x = i
        win = curses.newwin(nlines - (2 * begin_y), ncols - (2 * begin_x), begin_y, begin_x)
        _test_backgrounds(win, c2, c3, msg=f"i={i}")
        grid = Grid(win)
        _test_outside_ltor_ttob(grid)
        _test_outside_rtol_btot(grid)
        _test_outside_plus(grid)
        prompt(grid, win, msg=f"i={i} bkgd default {grid}")

    curses.endwin()


# -------------------------------------------------------------------------------


@logger.catch
def main5(win: curses.window) -> None:

    # pylint: disable=too-many-locals

    c1, c2, c3 = setup_test(win)

    grid = Grid(win, bkgd_grid=(ord("+"), c2), bkgd_box=(ord("."), c3))
    # grid = Grid(win, bkgd_grid=('.', c2))
    # grid = Grid(win, bkgd_grid=('.', c3))
    # grid = Grid(win, bkgd_box=('.', c2))
    # grid = Grid(win, bkgd_box=('.', c3))
    # grid = Grid(win)

    # check screen size!! 36x146

    _test_crossing_x = False
    if _test_crossing_x:
        for i in range(0, 18, 2):
            grid.box(
                f"{i}:ul", nlines=4, ncols=5, begin_y=2 * i, begin_x=3 * i, left=grid, top=grid
            )
            grid.box(
                f"{i}:ur", nlines=4, ncols=5, begin_y=2 * i, begin_x=-3 * i, right=grid, top=grid
            )
            grid.box(
                f"{i}:lr",
                nlines=4,
                ncols=5,
                begin_y=-2 * i,
                begin_x=-3 * i,
                right=grid,
                bottom=grid,
            )
            grid.box(
                f"{i}:ll",
                nlines=4,
                ncols=5,
                begin_y=-2 * i,
                begin_x=3 * i,
                left=grid,
                bottom=grid,
            )
            prompt(grid, win)
        curses.endwin()
        return

    _test_corners = True
    if _test_corners:
        # corners
        ul = grid.box("ul", 5, 20, top=grid, left=grid)
        ur = grid.box("ur", 5, 20, top=grid, right=grid)
        lr = grid.box("lr", 5, 20, right=grid, bottom=grid)
        ll = grid.box("ll", 5, 20, bottom=grid, left=grid)
        prompt(grid, win)

    _test_fillers_none_to_grid = True
    if _test_fillers_none_to_grid:
        # fillers, none to grid
        # pylint: disable=possibly-used-before-assignment
        tf = grid.box("tf", 5, 0, top=grid, right2l=ur, bottom=None, left2r=ul)
        rf = grid.box("rf", 0, 20, top2b=ur, right=grid, bottom2t=lr, left2r=None)
        bf = grid.box("bf", 5, 0, top2b=None, right2l=lr, bottom=grid, left2r=ll)
        lf = grid.box("lf", 0, 20, top2b=ul, right2l=None, bottom2t=ll, left=grid)
        prompt(grid, win)

    # pylint: disable=using-constant-test
    if False:
        # fillers to grid
        grid.box("full", 0, 0, left=grid, right=grid, top=grid, bottom=grid)
        grid.box("box", 5, 20, begin_y=10, begin_x=10, bkgd_box=("@", c1))
        # prompt(grid, win)

    if True:
        for i in range(0, 14, 2):
            grid.box(
                f"{i}:ul", nlines=4, ncols=5, begin_y=2 * i, begin_x=3 * i, left2r=lf, top2b=tf
            )
            grid.box(
                f"{i}:ur", nlines=4, ncols=5, begin_y=2 * i, begin_x=-3 * i, right2l=rf, top2b=tf
            )
            grid.box(
                f"{i}:lr",
                nlines=4,
                ncols=5,
                begin_y=-2 * i,
                begin_x=-3 * i,
                right2l=rf,
                bottom2t=bf,
            )
            grid.box(
                f"{i}:ll",
                nlines=4,
                ncols=5,
                begin_y=-2 * i,
                begin_x=3 * i,
                left2r=lf,
                bottom2t=bf,
            )
        prompt(grid, win, "check screen size!! 36x146")
        curses.endwin()
        return

    if True:
        _test_outside_ltor_ttob(grid)
        _test_outside_rtol_btot(grid)
        _test_outside_plus(grid)
        prompt(grid, win, "check screen size!! 36x146")
        # _test_backgrounds(win, c2, c3, 'hello')
        curses.endwin()
        return

    # center
    # cntr = grid.box('cntr', 0, 0, top2b=tf, right2l=rf, bottom2t=bf, left2r=lf)
    # _ = cntr

    # split the center vertically
    # vs = grid.box('vs', 0, int(cntr.getmaxyx()[1] / 2),
    #               top=cntr, right=None, bottom=cntr, left=cntr)
    # vs = grid.box('vs', 0, 7, top=cntr, right=None, bottom=cntr, left=cntr)

    #
    prompt(grid, win)
    curses.endwin()


# -------------------------------------------------------------------------------


@logger.catch
def main6(win: curses.window) -> None:

    _, c2, c3 = setup_test(win)

    grid = Grid(win, bkgd_grid=(ord("+"), c2), bkgd_box=(ord("."), c3))

    top = grid.box("hsplit-top", 5, 0, left=grid, right=grid, top=grid)
    grid.box("hsplit-bot", 0, 0, left=grid, right=grid, top2b=top, bottom=grid)
    prompt(grid, win)

    bot = grid.box("hsplit-bot", 5, 0, left=grid, right=grid, bottom=grid)
    grid.box("hsplit-top", 0, 0, left=grid, right=grid, bottom2t=bot, top=grid)
    prompt(grid, win)

    left = grid.box("vsplit-left", 0, 20, left=grid, top=grid, bottom=grid)
    grid.box("vsplit-right", 0, 0, left2r=left, right=grid, top=grid, bottom=grid)
    prompt(grid, win)

    right = grid.box("vsplit-right", 0, 20, right=grid, top=grid, bottom=grid)
    grid.box("vsplit-left", 0, 0, left=grid, right2l=right, top=grid, bottom=grid)
    prompt(grid, win)


# -------------------------------------------------------------------------------


def setup_test(win: curses.window) -> tuple[int, int, int]:
    #                   fg                  bg
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
    c1 = curses.color_pair(1)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    c2 = curses.color_pair(2)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_WHITE)
    c3 = curses.color_pair(3)
    win.clear()
    win.bkgd(ord("*"), c1)
    # prompt(None, win, msg=f'win setup {winyx(win)}')
    return c1, c2, c3


# -------------------------------------------------------------------------------


def _test_backgrounds(win: curses.window, c2: int, c3: int, msg: str) -> None:

    grid = Grid(win)
    _test_outside_ltor_ttob(grid)
    _test_outside_rtol_btot(grid)
    _test_outside_plus(grid)
    prompt(grid, win, msg=f"{msg} bkgd default {grid}")

    grid = Grid(win, bkgd_box=(ord("."), c3))
    _test_outside_ltor_ttob(grid)
    _test_outside_rtol_btot(grid)
    _test_outside_plus(grid)
    prompt(grid, win, msg=f"{msg} bkgd_box {grid}")

    grid = Grid(win, bkgd_grid=(ord("."), c2))
    _test_outside_ltor_ttob(grid)
    _test_outside_rtol_btot(grid)
    _test_outside_plus(grid)
    prompt(grid, win, msg=f"{msg} bkgd_grid {grid}")

    grid = Grid(win, bkgd_grid=(ord("."), c2), bkgd_box=(ord("."), c3))
    _test_outside_ltor_ttob(grid)
    _test_outside_rtol_btot(grid)
    _test_outside_plus(grid)
    prompt(grid, win, msg=f"{msg} bkgd_box bkgd_grid {grid}")


# -------------------------------------------------------------------------------
#     +---+
#     | t |
# +---+---+---+
# | l | c | r |
# +---+---+---+
#     | b |
#     +---+


def _test_outside_plus(grid: Grid, centered: bool = True) -> None:

    if centered:
        c = grid.box(
            "c", 3, 5, begin_y=int(grid.nlines / 2 - 3), begin_x=int(grid.ncols / 2 - 3)
        )
    else:
        c = grid.box("c", 3, 5, begin_y=2, begin_x=4)
        c = grid.box("c", 3, 5, begin_y=3, begin_x=5)
        c = grid.box("c", 3, 5, begin_y=4, begin_x=6)

    _ = grid.box("t", 3, 5, bottom2t=c, left=c)
    _ = grid.box("r", 3, 5, top=c, left2r=c)
    _ = grid.box("b", 3, 5, top2b=c, left=c)
    _ = grid.box("l", 3, 5, top=c, right2l=c)


# -------------------------------------------------------------------------------
# +---+---+---+
# | a | b | c |
# +---+---+---+
# | d | e | f |
# +---+---+---+
# | g | h | i |
# +---+---+---+


def _test_outside_ltor_ttob(grid: Grid) -> None:
    logger.success("left to right, from top to bottom")

    a = grid.box("a", 5, 10, top=grid, left=grid)
    b = grid.box("b", 5, 10, top=a, left2r=a)
    _ = grid.box("c", 5, 10, top=a, left2r=b)

    d = grid.box("d", 5, 10, top2b=a, left=a)
    e = grid.box("e", 5, 10, top2b=a, left2r=d)
    _ = grid.box("f", 5, 10, top2b=a, left2r=e)

    g = grid.box("g", 5, 10, top2b=d, left=d)
    h = grid.box("h", 5, 10, top2b=d, left2r=g)
    _ = grid.box("i", 5, 10, top2b=d, left2r=h)


# -------------------------------------------------------------------------------
# +---+---+---+
# | i | h | g |
# +---+---+---+
# | f | e | d |
# +---+---+---+
# | c | b | a |
# +---+---+---+


def _test_outside_rtol_btot(grid: Grid) -> None:
    logger.success("right to left, from bottom to top")

    a = grid.box("a", 5, 10, bottom=grid, right=grid)
    b = grid.box("b", 5, 10, top=a, right2l=a)
    _ = grid.box("c", 5, 10, top=a, right2l=b)

    d = grid.box("d", 5, 10, bottom2t=a, right=grid)
    e = grid.box("e", 5, 10, bottom2t=a, right2l=d)
    _ = grid.box("f", 5, 10, bottom2t=a, right2l=e)

    g = grid.box("g", 5, 10, bottom2t=d, right=grid)
    h = grid.box("h", 5, 10, bottom2t=d, right2l=g)
    _ = grid.box("i", 5, 10, bottom2t=d, right2l=h)


# -------------------------------------------------------------------------------

#
# j = grid.box('j', 5, -10, right2l=win)
# k = grid.box('k', 5, 10, right2l=j)
# l = grid.box('l', 5, 10, right2l=k)

#
# m = grid.box('m', -5, -10, bottom2t=win, right2l=win)
# n = grid.box('n', -5, 10, bottom2t=win, right2l=m)
# o = grid.box('o', -5, 10, bottom2t=win, right2l=n)

#
# p = grid.box('p', -5, 10, bottom2t=win)
# q = grid.box('q', -5, 10, bottom2t=win, left2r=p)
# r = grid.box('r', -5, 10, bottom2t=win, left2r=q)

# -------------------------------------------------------------------------------


def prompt(grid: Grid, win: curses.window, msg: str = "Press any key to continue") -> None:

    # win.erase()

    if grid:
        for idx, w in enumerate(grid.boxes):
            with contextlib.suppress(curses.error):
                w.addstr(0, 0, str(idx))

        grid.redraw()

    win = grid.win
    nlines = win.getmaxyx()[0]
    win.addstr(nlines - 6, 20, msg)
    while libcurses.getkey(win) == curses.KEY_RESIZE:
        logger.success("resized!")


# -------------------------------------------------------------------------------

if __name__ == "__main__":
    # logger.remove(0)
    # import sys
    # logger.add(sys.stderr,
    #            format="{level} {function} {line} {message}",
    #            colorize=True, level='TRACE')
    # curses.wrapper(main1)
    # curses.wrapper(main3)
    # curses.wrapper(main4)
    libcurses.wrapper(main5)
    # curses.wrapper(main6)
