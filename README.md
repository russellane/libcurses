## libcurses

Framework and tools for multi-threaded, curses(3)-based, terminal applications.

* Write to screen from multiple threads.

    * Use `libcurses.wrapper` instead of `curses.wrapper`.
    * Use `libcurses.getkey` instead of `curses.getch`.
    * Use `libcurses.getline` instead of `curses.getstr`.
    * Preserve the cursor with context manager `libcurses.preserve_cursor`.

* Register callbacks with `register_fkey` to handle function-keys pressed
  during `getkey` and `getline` processing.

* Register callbacks with `add_mouse_handler` to handle mouse events
  during `getkey` and `getline` processing.

* Manage a logger destination, `LogSink`, to write to a curses window.

* A `Grid` framework.


### class Grid

Grid of windows.

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


### class LogSink

Logger sink to curses window.

The `LogSink` class provides a logger destination that writes log
messages to a curses window, and methods that control various
logging features.


### class MouseEvent

Wrap `curses.getmouse` with additional, convenience-properties.

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


### method add_mouse_handler

Call `func` with `args` when mouse event happens at (y, x).

### method clear_mouse_handlers

Remove all mouse handlers.

### function get_colormap

Return map of `loguru-level-name` to `curses-color/attr`.

Call after creating all custom levels with `logger.level()`.
Map is build once and cached; repeated calls return same map.


### function getkey

Read and return a character from window.

Args:
    win: curses window to read from.
    no_mouse: ignore mouse events (for internal use).

Return:
    -1 when no-input in no-delay mode, or
    None on end of file, or
    >=0 int character read.


### function getline

Read and return a line of input from window.

A line is terminated with CR, LF or KEY_ENTER.
Backspace deletes the previous character.
NAK (ctrl-U) kills the line.
Mouse events are handled.


### function preserve_cursor

Context manager to save and restore the cursor.

### function register_fkey

Register `func` to be called when `key` is pressed.

Args:
    func: callable, to be called on receipt of `key`.
    key: the key to be captured, e.g., `curses.KEY_F1`,
    or zero (0) for all keys.

`func` is appended to a list for the `key`;
pass func=None to remove list of funcs for `key` from registry.


### function wrapper

Use instead of `curses.wrapper`.

