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

### Grid - group of resizable windows.

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

* Drag and drop an interior border to resize the windows on either side.

* Double-click an interior border to enter Resize Mode:

    * scroll-wheel and arrow-keys move the border, and
    * click anywhere, Enter and Esc to exit Resize Mode.

* Grids also provide a wrapper around `curses.newwin` that takes positioning
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

For example, this 3x13 grid with three 3x5 boxes may be described a few different ways:

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

### LogSink - Logger sink to curses window.

The `LogSink` class provides a logger destination that writes log
messages to a curses window, and methods that control various
logging features.

### MouseEvent - Wrap `curses.getmouse` with additional, convenience-properties.

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
