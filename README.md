# grid - group of resizable windows.

A rectangular collection of windows with shared (collapsed) borders that
resize the windows to either side (syncronized shrink/expand) when moused upon.

```
        +-------+---+------+    example `Grid`, 9 windows.
        |       |   |      |
        +-------+---+------+
        |           |      |
        +------+----+------+
        |      |           |
        +------+--+--------+
        |         |        |
        +---------+--------+
```

Drag and drop an interior border to resize the windows on either side.

Double-click an interior border to enter Resize Mode:
    * scroll-wheel and arrow-keys move the border, and
    * click anywhere, Enter and Esc to exit Resize Mode.

Grids also provide a wrapper around `curses.newwin` that takes positioning
parameters that describe the spatial-relationship to other windows on the
screen, instead of (y,x) coordinates:

```
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
```

For example, this 3x13 grid with three 3x5 boxes may be described three
different ways:

```
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
```

If two endpoints are given (such as 3b), the length will be calculated to
fill the gap between the endpoints.
