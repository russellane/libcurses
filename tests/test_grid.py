"""Tests for Grid class."""

import copy
import curses
import curses.ascii
from threading import Lock
from unittest.mock import MagicMock, call, patch

import pytest

import libcurses.core as core_module
from libcurses.grid import Grid


@pytest.fixture(autouse=True)
def mock_acs_constants():
    """Mock curses ACS constants that require initialization."""
    curses.ACS_ULCORNER = ord("1")  # type: ignore[misc]
    curses.ACS_URCORNER = ord("2")  # type: ignore[misc]
    curses.ACS_LLCORNER = ord("3")  # type: ignore[misc]
    curses.ACS_LRCORNER = ord("4")  # type: ignore[misc]
    curses.ACS_HLINE = ord("5")  # type: ignore[misc]
    curses.ACS_VLINE = ord("6")  # type: ignore[misc]
    curses.ACS_TTEE = ord("7")  # type: ignore[misc]
    curses.ACS_BTEE = ord("8")  # type: ignore[misc]
    curses.ACS_LTEE = ord("9")  # type: ignore[misc]
    curses.ACS_RTEE = ord("A")  # type: ignore[misc]
    curses.ACS_PLUS = ord("B")  # type: ignore[misc]
    yield
    del curses.ACS_ULCORNER
    del curses.ACS_URCORNER
    del curses.ACS_LLCORNER
    del curses.ACS_LRCORNER
    del curses.ACS_HLINE
    del curses.ACS_VLINE
    del curses.ACS_TTEE
    del curses.ACS_BTEE
    del curses.ACS_LTEE
    del curses.ACS_RTEE
    del curses.ACS_PLUS


@pytest.fixture(autouse=True)
def reset_grid_init_called():  # noqa: PT022
    """Reset Grid._init_called between tests."""
    Grid._init_called = False
    yield


@pytest.fixture(autouse=True)
def setup_core_globals():
    """Set up core module globals for testing."""
    original_lock = getattr(core_module, "LOCK", None)
    core_module.LOCK = Lock()
    yield
    if original_lock is not None:
        core_module.LOCK = original_lock


@pytest.fixture
def mock_win():
    """Create mock curses window."""
    win = MagicMock()
    win.getmaxyx.return_value = (24, 80)
    win.getbegyx.return_value = (0, 0)
    return win


@pytest.fixture
def mock_mouse():
    """Mock Mouse class."""
    with patch("libcurses.grid.Mouse") as mock:
        yield mock


@pytest.fixture
def mock_register_fkey():
    """Mock register_fkey function."""
    with patch("libcurses.core.register_fkey") as mock:
        yield mock


@pytest.fixture
def mock_logger():
    """Mock logger."""
    with patch("libcurses.grid.logger") as mock:
        yield mock


# -----------------------------------------------------------------------------
# N IntFlag tests
# -----------------------------------------------------------------------------


class TestGridN:
    """Test Grid.N IntFlag enum."""

    def test_n_values(self):
        """N IntFlag has correct values."""
        assert Grid.N.T == 1
        assert Grid.N.R == 2
        assert Grid.N.B == 4
        assert Grid.N.L == 8

    def test_n_combinations(self):
        """N IntFlag supports combinations."""
        combined = Grid.N.T | Grid.N.R
        assert combined == 3

        combined = Grid.N.T | Grid.N.R | Grid.N.B | Grid.N.L
        assert combined == 15


# -----------------------------------------------------------------------------
# _init_borders tests
# -----------------------------------------------------------------------------


class TestGridInitBorders:
    """Test Grid._init_borders class method."""

    def test_init_borders_creates_mapping(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_init_borders creates border character mapping."""
        Grid(mock_win)

        assert hasattr(Grid, "_borders")
        assert isinstance(Grid._borders, dict)

    def test_init_borders_has_all_combinations(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_init_borders maps all 16 neighbor combinations."""
        Grid(mock_win)

        # All 16 combinations (0-15)
        assert len(Grid._borders) == 16

    def test_init_borders_corner_characters(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_init_borders maps corner characters correctly."""
        Grid(mock_win)

        # Bottom-left corner (neighbors to right and top)
        assert Grid._borders[Grid.N.R | Grid.N.T] == curses.ACS_LLCORNER
        # Top-left corner (neighbors to right and bottom)
        assert Grid._borders[Grid.N.B | Grid.N.R] == curses.ACS_ULCORNER
        # Top-right corner (neighbors to left and bottom)
        assert Grid._borders[Grid.N.L | Grid.N.B] == curses.ACS_URCORNER
        # Bottom-right corner (neighbors to left and top)
        assert Grid._borders[Grid.N.L | Grid.N.T] == curses.ACS_LRCORNER

    def test_init_borders_tee_characters(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_init_borders maps T-junction characters correctly."""
        Grid(mock_win)

        # Left tee (neighbors to right, bottom, and top)
        assert Grid._borders[Grid.N.B | Grid.N.R | Grid.N.T] == curses.ACS_LTEE
        # Right tee (neighbors to left, bottom, and top)
        assert Grid._borders[Grid.N.L | Grid.N.B | Grid.N.T] == curses.ACS_RTEE
        # Top tee (neighbors to left, right, and bottom)
        assert Grid._borders[Grid.N.L | Grid.N.B | Grid.N.R] == curses.ACS_TTEE
        # Bottom tee (neighbors to left, right, and top)
        assert Grid._borders[Grid.N.L | Grid.N.R | Grid.N.T] == curses.ACS_BTEE

    def test_init_borders_plus_character(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_init_borders maps plus/cross character."""
        Grid(mock_win)

        # Plus (all four neighbors)
        assert Grid._borders[Grid.N.L | Grid.N.B | Grid.N.R | Grid.N.T] == curses.ACS_PLUS


# -----------------------------------------------------------------------------
# Initialization tests
# -----------------------------------------------------------------------------


class TestGridInit:
    """Test Grid initialization."""

    def test_stores_window(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid stores the window."""
        grid = Grid(mock_win)

        assert grid.win is mock_win

    def test_gets_dimensions_from_window(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """Grid gets dimensions from window."""
        mock_win.getmaxyx.return_value = (30, 100)
        mock_win.getbegyx.return_value = (0, 0)

        grid = Grid(mock_win)

        assert grid.nlines == 30
        assert grid.ncols == 100
        assert grid.begin_y == 0
        assert grid.begin_x == 0

    def test_creates_grid_array(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid creates 2D grid array."""
        mock_win.getmaxyx.return_value = (10, 20)

        grid = Grid(mock_win)

        assert len(grid.grid) == 10
        assert len(grid.grid[0]) == 20

    def test_creates_attrs_array(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid creates 2D attrs array."""
        mock_win.getmaxyx.return_value = (10, 20)

        grid = Grid(mock_win)

        assert len(grid.attrs) == 10
        assert len(grid.attrs[0]) == 20

    def test_initializes_boxes_list(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid initializes boxes list with main window."""
        grid = Grid(mock_win)

        assert grid.boxes == [mock_win]

    def test_initializes_boxnames_dict(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """Grid initializes boxnames dict."""
        grid = Grid(mock_win)

        assert grid.boxnames[mock_win] == "grid"

    def test_applies_bkgd_grid(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid applies background to grid window."""
        grid = Grid(mock_win, bkgd_grid=(ord(" "), curses.A_NORMAL))

        mock_win.bkgd.assert_called_with(ord(" "), curses.A_NORMAL)

    def test_stores_bkgd_box(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid stores bkgd_box for later use."""
        bkgd = (ord("."), curses.A_DIM)
        grid = Grid(mock_win, bkgd_box=bkgd)

        assert grid.bkgd_box == bkgd

    def test_enables_mouse(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid enables mouse."""
        Grid(mock_win)

        mock_mouse.enable.assert_called_once()

    def test_adds_internal_mouse_handler(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """Grid adds internal mouse handler."""
        grid = Grid(mock_win)

        mock_mouse.add_internal_mouse_handler.assert_called_once()
        # Verify the handler is the grid's _handle_mouse_event method
        call_args = mock_mouse.add_internal_mouse_handler.call_args[0]
        assert call_args[0] == grid._handle_mouse_event  # noqa: PLW143

    def test_registers_fkeys_first_time(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """Grid registers function keys on first initialization."""
        Grid(mock_win)

        # Should register KEY_REFRESH, FF, and KEY_RESIZE
        assert mock_register_fkey.call_count >= 3

    def test_init_called_only_once(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """Grid._init_called prevents duplicate initialization."""
        Grid._init_called = False

        grid1 = Grid(mock_win)
        initial_call_count = mock_register_fkey.call_count

        Grid(mock_win)
        # Should register KEY_RESIZE again but not KEY_REFRESH and FF
        # The key point is _init_borders is not called twice


# -----------------------------------------------------------------------------
# __repr__ tests
# -----------------------------------------------------------------------------


class TestGridRepr:
    """Test Grid.__repr__ method."""

    def test_repr_contains_class_name(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """repr contains class name."""
        grid = Grid(mock_win)

        assert "Grid(" in repr(grid)

    def test_repr_contains_dimensions(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """repr contains dimensions."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        grid = Grid(mock_win)
        r = repr(grid)

        assert "nlines=24" in r
        assert "ncols=80" in r
        assert "begin_y=0" in r
        assert "begin_x=0" in r


# -----------------------------------------------------------------------------
# register_builder tests
# -----------------------------------------------------------------------------


class TestGridRegisterBuilder:
    """Test Grid.register_builder method."""

    def test_stores_builder(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """register_builder stores the builder function."""
        grid = Grid(mock_win)
        builder = MagicMock()

        grid.register_builder(builder)

        assert grid._builder is builder

    def test_calls_builder_immediately(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """register_builder calls the builder function."""
        grid = Grid(mock_win)
        builder = MagicMock()

        grid.register_builder(builder)

        builder.assert_called_once()


# -----------------------------------------------------------------------------
# _draw_box tests
# -----------------------------------------------------------------------------


class TestGridDrawBox:
    """Test Grid._draw_box method."""

    def test_draws_box_corners(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_draw_box sets corner positions."""
        mock_win.getmaxyx.return_value = (20, 40)
        mock_win.getbegyx.return_value = (0, 0)

        grid = Grid(mock_win)
        # Initial draw_box is called in __init__
        # Check that corners are set (values 5-8)
        assert grid.grid[0][0] == 5  # top-left
        assert grid.grid[0][39] == 6  # top-right
        assert grid.grid[19][39] == 7  # bottom-right
        assert grid.grid[19][0] == 8  # bottom-left

    def test_draws_box_edges(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_draw_box sets edge positions."""
        mock_win.getmaxyx.return_value = (20, 40)
        mock_win.getbegyx.return_value = (0, 0)

        grid = Grid(mock_win)
        # Top and bottom edges
        assert grid.grid[0][1] == 1  # top edge
        assert grid.grid[19][1] == 3  # bottom edge
        # Left and right edges
        assert grid.grid[1][0] == 4  # left edge
        assert grid.grid[1][39] == 2  # right edge


# -----------------------------------------------------------------------------
# border_attr tests
# -----------------------------------------------------------------------------


class TestGridBorderAttr:
    """Test Grid.border_attr method."""

    def test_sets_left_border_attr(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """border_attr sets left border attributes."""
        mock_win.getmaxyx.return_value = (20, 40)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        inner_win = MagicMock()
        inner_win.getmaxyx.return_value = (5, 10)
        inner_win.getbegyx.return_value = (2, 5)

        grid.border_attr(inner_win, Grid.N.L, 1)

        # Left border is at x=4 (begin_x - 1)
        for y in range(5):
            assert grid.attrs[2 + y][4] == 1

    def test_sets_right_border_attr(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """border_attr sets right border attributes."""
        mock_win.getmaxyx.return_value = (20, 40)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        inner_win = MagicMock()
        inner_win.getmaxyx.return_value = (5, 10)
        inner_win.getbegyx.return_value = (2, 5)

        grid.border_attr(inner_win, Grid.N.R, 1)

        # Right border is at x=15 (begin_x + ncols)
        for y in range(5):
            assert grid.attrs[2 + y][15] == 1

    def test_sets_top_border_attr(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """border_attr sets top border attributes."""
        mock_win.getmaxyx.return_value = (20, 40)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        inner_win = MagicMock()
        inner_win.getmaxyx.return_value = (5, 10)
        inner_win.getbegyx.return_value = (2, 5)

        grid.border_attr(inner_win, Grid.N.T, 1)

        # Top border is at y=1 (begin_y - 1)
        for x in range(10):
            assert grid.attrs[1][5 + x] == 1

    def test_sets_bottom_border_attr(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """border_attr sets bottom border attributes."""
        mock_win.getmaxyx.return_value = (20, 40)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        inner_win = MagicMock()
        inner_win.getmaxyx.return_value = (5, 10)
        inner_win.getbegyx.return_value = (2, 5)

        grid.border_attr(inner_win, Grid.N.B, 1)

        # Bottom border is at y=7 (begin_y + nlines)
        for x in range(10):
            assert grid.attrs[7][5 + x] == 1


# -----------------------------------------------------------------------------
# box tests
# -----------------------------------------------------------------------------


def _make_box_win(nlines=8, ncols=18, begin_y=1, begin_x=1):
    """Create a mock window for box tests."""
    win = MagicMock()
    win.getmaxyx.return_value = (nlines, ncols)
    win.getbegyx.return_value = (begin_y, begin_x)
    return win


class TestGridBox:
    """Test Grid.box method."""

    def test_creates_new_window(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box creates a new curses window."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("test", 10, 20)

            mock_newwin.assert_called_once()
            # Window should be 2 smaller in each dimension (for border)
            call_args = mock_newwin.call_args[0]
            assert call_args[0] == 8  # nlines - 2
            assert call_args[1] == 18  # ncols - 2

    def test_adds_to_boxes_list(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box adds window to boxes list."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("test", 10, 20)

            assert len(grid.boxes) == 2
            assert result in grid.boxes

    def test_stores_boxname(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box stores the boxname."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("mybox", 10, 20)

            assert grid.boxnames[result] == "mybox"

    def test_applies_bkgd_box(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box applies background when specified."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            new_win = _make_box_win()
            mock_newwin.return_value = new_win
            grid = Grid(mock_win)
            grid.box("test", 10, 20, bkgd_box=(ord("X"), curses.A_DIM))

            new_win.bkgd.assert_called_with(ord("X"), curses.A_DIM)

    def test_applies_default_bkgd_box(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """box applies grid's default bkgd_box."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            new_win = _make_box_win()
            mock_newwin.return_value = new_win
            grid = Grid(mock_win, bkgd_box=(ord("."), curses.A_DIM))
            grid.box("test", 10, 20)

            new_win.bkgd.assert_called_with(ord("."), curses.A_DIM)

    def test_resizes_existing_window(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """box resizes existing window with same name."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            existing_win = _make_box_win()
            mock_newwin.return_value = existing_win
            grid = Grid(mock_win)
            grid.box("test", 10, 20)

            # Reset and create another box with same name
            mock_newwin.reset_mock()
            grid.box("test", 15, 25)

            # Should not create new window
            mock_newwin.assert_not_called()
            # Should resize existing
            existing_win.resize.assert_called()

    def test_left_reference(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box aligns with left of reference window."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("test", 10, 20, left=grid)

            # Should align with grid's left edge
            call_args = mock_newwin.call_args[0]
            assert call_args[3] == 1  # begin_x = 0 + 1 (inside border)

    def test_right_reference(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box aligns with right of reference."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("test", 10, 20, right=grid)

            # Should align with grid's right edge
            call_args = mock_newwin.call_args[0]
            # begin_x = 79 - 20 + 1 + 1 = 61
            assert call_args[3] == 61

    def test_top_reference(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box aligns with top of reference."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("test", 10, 20, top=grid)

            call_args = mock_newwin.call_args[0]
            assert call_args[2] == 1  # begin_y = 0 + 1

    def test_bottom_reference(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box aligns with bottom of reference."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            mock_newwin.return_value = _make_box_win()
            grid = Grid(mock_win)
            result = grid.box("test", 10, 20, bottom=grid)

            call_args = mock_newwin.call_args[0]
            # begin_y = 23 - 10 + 1 + 1 = 15
            assert call_args[2] == 15

    def test_left2r_reference(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box aligns left edge with right of reference window."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            ref_win = _make_box_win(nlines=8, ncols=18, begin_y=1, begin_x=1)
            mock_newwin.return_value = ref_win

            grid = Grid(mock_win)
            first_box = grid.box("first", 10, 20)

            new_win = _make_box_win()
            mock_newwin.return_value = new_win
            second_box = grid.box("second", 10, 20, left2r=first_box)

            # Second box should start after first box
            # begin_x = first.begin_x + first.ncols = 1 + 18 + 1 = 20
            last_call = mock_newwin.call_args_list[-1]
            assert last_call[0][3] == 20

    def test_top2b_reference(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """box aligns top edge with bottom of reference window."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            ref_win = _make_box_win(nlines=8, ncols=18, begin_y=1, begin_x=1)
            mock_newwin.return_value = ref_win

            grid = Grid(mock_win)
            first_box = grid.box("first", 10, 20)

            new_win = _make_box_win()
            mock_newwin.return_value = new_win
            second_box = grid.box("second", 10, 20, top2b=first_box)

            # Second box should start below first box
            last_call = mock_newwin.call_args_list[-1]
            assert last_call[0][2] == 10  # begin_y = 1 + 8 + 1 = 10


# -----------------------------------------------------------------------------
# _getmaxbeg tests
# -----------------------------------------------------------------------------


class TestGridGetmaxbeg:
    """Test Grid._getmaxbeg method."""

    def test_no_references_returns_input(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg returns input when no references."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        length, begin = grid._getmaxbeg("test", 0, 10, 5, None, None, None, None, "", "", "", "")

        assert length == 10
        assert begin == 5

    def test_raises_on_mutually_exclusive_lo(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg raises on mutually exclusive lo references."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        ref1 = MagicMock()
        ref2 = MagicMock()

        with pytest.raises(ValueError, match="mutually exclusive"):
            grid._getmaxbeg(
                "test", 0, 10, 0, ref1, ref2, None, None, "left", "left2r", "right", "right2l"
            )

    def test_raises_on_mutually_exclusive_hi(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg raises on mutually exclusive hi references."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        ref1 = MagicMock()
        ref2 = MagicMock()

        with pytest.raises(ValueError, match="mutually exclusive"):
            grid._getmaxbeg(
                "test", 0, 10, 0, None, None, ref1, ref2, "left", "left2r", "right", "right2l"
            )

    def test_raises_on_self_reference_lo2hi(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg raises when lo2hi references self."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        with pytest.raises(ValueError, match="use .* to reference grid"):
            grid._getmaxbeg(
                "test", 0, 10, 0, None, grid, None, None, "left", "left2r", "right", "right2l"
            )

    def test_raises_on_self_reference_hi2lo(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg raises when hi2lo references self."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        with pytest.raises(ValueError, match="use .* to reference grid"):
            grid._getmaxbeg(
                "test", 0, 10, 0, None, None, None, grid, "left", "left2r", "right", "right2l"
            )

    def test_raises_on_nonzero_length_with_both(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg raises when non-zero length with both lo and hi."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        ref = MagicMock()
        ref.getbegyx.return_value = (5, 5)
        ref.getmaxyx.return_value = (10, 10)

        with pytest.raises(ValueError, match="non-zero length"):
            grid._getmaxbeg(
                "test", 0, 10, 0, ref, None, ref, None, "left", "left2r", "right", "right2l"
            )

    def test_raises_on_zero_length_without_both(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg raises when zero length without both lo and hi."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        ref = MagicMock()
        ref.getbegyx.return_value = (5, 5)

        with pytest.raises(ValueError, match="zero length"):
            grid._getmaxbeg(
                "test", 0, 0, 0, ref, None, None, None, "left", "left2r", "right", "right2l"
            )

    def test_calculates_length_from_both_references(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg calculates length when both lo and hi are given."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        lo_ref = MagicMock()
        lo_ref.getbegyx.return_value = (0, 5)
        lo_ref.getmaxyx.return_value = (10, 10)

        hi_ref = MagicMock()
        hi_ref.getbegyx.return_value = (0, 30)
        hi_ref.getmaxyx.return_value = (10, 10)

        # lo2hi gives begin = 5 + 10 = 15
        # hi2lo gives last = 30 - 1 = 29
        # length = 29 - 15 + 1 = 15
        length, begin = grid._getmaxbeg(
            "test", 1, 0, 0, None, lo_ref, None, hi_ref, "left", "left2r", "right", "right2l"
        )

        assert length == 15
        assert begin == 15

    def test_uses_hi_reference_for_end_calculation(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg uses hi reference to calculate begin from end."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        hi_ref = MagicMock()
        hi_ref.getbegyx.return_value = (0, 50)
        hi_ref.getmaxyx.return_value = (10, 10)

        # hi (not self) gives last = 50 + 10 = 60
        # begin = 60 - 20 + 1 = 41
        length, begin = grid._getmaxbeg(
            "test", 1, 20, 0, None, None, hi_ref, None, "left", "left2r", "right", "right2l"
        )

        assert length == 20
        assert begin == 41

    def test_uses_lo_non_self_reference(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_getmaxbeg uses lo reference when it's not self."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        lo_ref = MagicMock()
        lo_ref.getbegyx.return_value = (0, 10)
        lo_ref.getmaxyx.return_value = (10, 20)

        # lo (not self) gives begin = 10 - 1 = 9
        length, begin = grid._getmaxbeg(
            "test", 1, 15, 0, lo_ref, None, None, None, "left", "left2r", "right", "right2l"
        )

        assert length == 15
        assert begin == 9


# -----------------------------------------------------------------------------
# getbegyx/getmaxyx tests
# -----------------------------------------------------------------------------


class TestGridGetters:
    """Test Grid.getbegyx and getmaxyx methods."""

    def test_getbegyx(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """getbegyx returns window's getbegyx."""
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # After init, call getbegyx which delegates to win
        mock_win.getbegyx.return_value = (10, 20)
        assert grid.getbegyx() == (10, 20)

    def test_getmaxyx(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """getmaxyx returns window's getmaxyx."""
        mock_win.getmaxyx.return_value = (24, 80)
        grid = Grid(mock_win)

        assert grid.getmaxyx() == (24, 80)


# -----------------------------------------------------------------------------
# redraw tests
# -----------------------------------------------------------------------------


class TestGridRedraw:
    """Test Grid.redraw method."""

    def test_clears_window(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """redraw clears the window."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        with patch("curses.doupdate"):
            grid.redraw()

        mock_win.clear.assert_called()

    def test_calls_doupdate(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """redraw calls curses.doupdate."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        with patch("curses.doupdate") as mock_doupdate:
            grid.redraw()

        mock_doupdate.assert_called()

    def test_touches_all_windows(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """redraw touches all windows."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        with patch("curses.doupdate"):
            grid.redraw()

        mock_win.touchwin.assert_called()
        mock_win.noutrefresh.assert_called()

    def test_redraws_multiple_boxes(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """redraw draws borders for all boxes."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            box_win = _make_box_win(nlines=8, ncols=18, begin_y=1, begin_x=1)
            mock_newwin.return_value = box_win
            grid = Grid(mock_win)

            # Add a box
            grid.box("test", 10, 20)

            # redraw should now iterate through boxes[1:]
            with patch("curses.doupdate"):
                grid.redraw()

            # The box window should have been touched
            box_win.touchwin.assert_called()


# -----------------------------------------------------------------------------
# refresh tests
# -----------------------------------------------------------------------------


class TestGridRefresh:
    """Test Grid.refresh method."""

    def test_touches_all_windows(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """refresh touches all windows."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)
        mock_win.reset_mock()

        with patch("curses.doupdate"):
            grid.refresh()

        mock_win.touchwin.assert_called()
        mock_win.noutrefresh.assert_called()

    def test_calls_doupdate(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """refresh calls curses.doupdate."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        with patch("curses.doupdate") as mock_doupdate:
            grid.refresh()

        mock_doupdate.assert_called()


# -----------------------------------------------------------------------------
# winyx tests
# -----------------------------------------------------------------------------


class TestGridWinyx:
    """Test Grid.winyx method."""

    def test_returns_window_info(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """winyx returns window coordinates string."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        result = grid.winyx(mock_win)

        assert "boxname='grid'" in result
        assert "l=24" in result
        assert "c=80" in result
        assert "y=0" in result
        assert "x=0" in result


# -----------------------------------------------------------------------------
# getwin tests
# -----------------------------------------------------------------------------


class TestGridGetwin:
    """Test Grid.getwin method."""

    def test_returns_none_for_no_match(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """getwin returns None when no window at coordinates."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        result = grid.getwin(100, 100)

        assert result is None

    def test_returns_window_at_coordinates(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """getwin returns window that encloses coordinates."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        with patch("libcurses.grid.curses.newwin") as mock_newwin:
            box_win = _make_box_win()
            box_win.enclose.return_value = True
            mock_newwin.return_value = box_win
            grid = Grid(mock_win)
            grid.box("test", 10, 20)

            result = grid.getwin(5, 5)

            assert result is box_win


# -----------------------------------------------------------------------------
# mouse property tests
# -----------------------------------------------------------------------------


class TestGridMouseProperties:
    """Test Grid mouse boundary properties."""

    def test_mouse_min_y(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_mouse_min_y returns begin_y + 1."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # Manually set begin_y after init to test property
        grid.begin_y = 5
        assert grid._mouse_min_y == 6

    def test_mouse_max_y(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_mouse_max_y returns begin_y + nlines - 2."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # Manually set begin_y after init to test property
        grid.begin_y = 5
        assert grid._mouse_max_y == 27  # 5 + 24 - 2

    def test_mouse_min_x(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_mouse_min_x returns begin_x + 1."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # Manually set begin_x after init to test property
        grid.begin_x = 10
        assert grid._mouse_min_x == 11

    def test_mouse_max_x(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_mouse_max_x returns begin_x + ncols - 2."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # Manually set begin_x after init to test property
        grid.begin_x = 10
        assert grid._mouse_max_x == 88  # 10 + 80 - 2


# -----------------------------------------------------------------------------
# handle_term_resized_event tests
# -----------------------------------------------------------------------------


class TestGridHandleTermResizedEvent:
    """Test Grid.handle_term_resized_event method."""

    def test_updates_dimensions(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """handle_term_resized_event updates grid dimensions."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        # Ensure curses.LINES and curses.COLS exist before creating grid
        curses.LINES = 24
        curses.COLS = 80

        try:
            grid = Grid(mock_win)
            grid._builder = None  # Initialize _builder to avoid AttributeError

            curses.LINES = 40
            curses.COLS = 120

            grid.handle_term_resized_event()

            assert grid.nlines == 40
            assert grid.ncols == 120
        finally:
            del curses.LINES
            del curses.COLS

    def test_resizes_window(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """handle_term_resized_event resizes the main window."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        curses.LINES = 24
        curses.COLS = 80

        try:
            grid = Grid(mock_win)
            grid._builder = None  # Initialize _builder to avoid AttributeError

            curses.LINES = 40
            curses.COLS = 120

            grid.handle_term_resized_event()

            mock_win.resize.assert_called_with(40, 120)
        finally:
            del curses.LINES
            del curses.COLS

    def test_reinitializes_grid_arrays(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """handle_term_resized_event reinitializes grid arrays."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)

        curses.LINES = 24
        curses.COLS = 80

        try:
            grid = Grid(mock_win)
            grid._builder = None  # Initialize _builder to avoid AttributeError

            curses.LINES = 40
            curses.COLS = 120

            grid.handle_term_resized_event()

            assert len(grid.grid) == 40
            assert len(grid.grid[0]) == 120
            assert len(grid.attrs) == 40
            assert len(grid.attrs[0]) == 120
        finally:
            del curses.LINES
            del curses.COLS

    def test_calls_builder(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """handle_term_resized_event calls builder if set."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        builder = MagicMock()
        grid.register_builder(builder)
        builder.reset_mock()

        curses.LINES = 40
        curses.COLS = 120

        try:
            grid.handle_term_resized_event()

            builder.assert_called_once()
        finally:
            del curses.LINES
            del curses.COLS


# -----------------------------------------------------------------------------
# _handle_mouse_event tests
# -----------------------------------------------------------------------------


class TestGridHandleMouseEvent:
    """Test Grid._handle_mouse_event method."""

    def test_ignores_non_button1(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_handle_mouse_event ignores non-button1 events."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.button = 2
        mouse_event.is_pressed = True

        result = grid._handle_mouse_event(mouse_event, None)

        assert result is False

    def test_ignores_button1_not_pressed_not_double_click(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_handle_mouse_event ignores button1 that isn't pressed or double-clicked."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.button = 1
        mouse_event.is_pressed = False
        mouse_event.nclicks = 0

        result = grid._handle_mouse_event(mouse_event, None)

        assert result is False

    def test_ignores_outside_grid(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_handle_mouse_event ignores events outside grid."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.button = 1
        mouse_event.is_pressed = True
        mouse_event.nclicks = 0
        mouse_event.x = 0  # On border, not inside
        mouse_event.y = 5

        result = grid._handle_mouse_event(mouse_event, None)

        assert result is False

    def test_handles_vline_click(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_handle_mouse_event handles click on vertical border."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        # Return ACS_VLINE - the code does & ~curses.A_COLOR, so just return the char value
        mock_win.inch.return_value = curses.ACS_VLINE
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.button = 1
        mouse_event.is_pressed = True
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        # Mock getwin to return windows
        grid.getwin = MagicMock(return_value=MagicMock())

        with patch.object(grid, "_resize") as mock_resize:
            result = grid._handle_mouse_event(mouse_event, None)
            assert result is True
            mock_resize.assert_called_once()

    def test_handles_hline_click(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_handle_mouse_event handles click on horizontal border."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        # Return ACS_HLINE - the code does & ~curses.A_COLOR
        mock_win.inch.return_value = curses.ACS_HLINE
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.button = 1
        mouse_event.is_pressed = True
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        # Mock getwin to return windows
        grid.getwin = MagicMock(return_value=MagicMock())

        with patch.object(grid, "_resize") as mock_resize:
            result = grid._handle_mouse_event(mouse_event, None)
            assert result is True
            mock_resize.assert_called_once()

    def test_ignores_non_border_char(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_handle_mouse_event ignores clicks not on border characters."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        mock_win.inch.return_value = ord(" ")  # Not a border char
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.button = 1
        mouse_event.is_pressed = True
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        result = grid._handle_mouse_event(mouse_event, None)

        assert result is False


# -----------------------------------------------------------------------------
# _resize tests
# -----------------------------------------------------------------------------


class TestGridResize:
    """Test Grid._resize method."""

    def test_exits_on_enter(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_resize exits when Enter is pressed."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.LF),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

        # Should have returned without error

    def test_exits_on_escape(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_resize exits when Escape is pressed."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.ESC),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

        # Should have returned without error

    def test_exits_on_none_key(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_resize exits when None key is returned."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=None),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

        # Should have returned without error

    def test_exits_on_cr(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_resize exits when CR is pressed."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.CR),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

    def test_exits_on_key_enter(self, mock_win, mock_mouse, mock_register_fkey, mock_logger):
        """_resize exits when KEY_ENTER is pressed."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.KEY_ENTER),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

    def test_ctrl_click_enters_kb_mode(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize enters keyboard mode on ctrl+click."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = True
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.ESC),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

        # Should have been in keyboard resize mode

    def test_double_click_enters_kb_mode(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize enters keyboard mode on double-click."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 2
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.ESC),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

        # Should have been in keyboard resize mode

    def test_mouse_released_exits_drag_mode(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize exits when mouse is released in drag mode."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        released_mouse = MagicMock()
        released_mouse.is_released = True

        with (
            patch("libcurses.grid.getkey", return_value=curses.KEY_MOUSE),
            patch("libcurses.grid.MouseEvent", return_value=released_mouse),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

    def test_ff_key_redraws_and_continues(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize redraws on FF (form feed) and continues."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = True  # kb mode
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        left_win = MagicMock()
        left_win.getmaxyx.return_value = (10, 20)
        left_win.getbegyx.return_value = (1, 1)

        # First FF, then ESC to exit
        with (
            patch("libcurses.grid.getkey", side_effect=[curses.ascii.FF, curses.ascii.ESC]),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, left=left_win)

    def test_resize_with_right_window(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize works with right window parameter."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        right_win = MagicMock()
        right_win.getmaxyx.return_value = (10, 20)
        right_win.getbegyx.return_value = (1, 21)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.ESC),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, right=right_win)

    def test_resize_with_upper_window(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize works with upper window parameter."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        upper_win = MagicMock()
        upper_win.getmaxyx.return_value = (10, 20)
        upper_win.getbegyx.return_value = (1, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.ESC),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, upper=upper_win)

    def test_resize_with_lower_window(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_resize works with lower window parameter."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        mouse_event = MagicMock()
        mouse_event.is_ctrl = False
        mouse_event.nclicks = 0
        mouse_event.x = 40
        mouse_event.y = 12

        lower_win = MagicMock()
        lower_win.getmaxyx.return_value = (10, 20)
        lower_win.getbegyx.return_value = (12, 1)

        with (
            patch("libcurses.grid.getkey", return_value=curses.ascii.ESC),
            patch("curses.doupdate"),
            patch.object(grid, "redraw"),
        ):
            grid._resize(mouse_event, lower=lower_win)


# -----------------------------------------------------------------------------
# _get_border_symbol tests
# -----------------------------------------------------------------------------


class TestGridGetBorderSymbol:
    """Test Grid._get_border_symbol method."""

    def test_returns_correct_corner_symbol(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_get_border_symbol returns correct corner symbol."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # Top-left corner at (0,0) has neighbors to right and bottom
        char, attr = grid._get_border_symbol(0, 0)

        assert char == curses.ACS_ULCORNER
        assert attr == curses.A_NORMAL

    def test_returns_reverse_attr_when_set(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_get_border_symbol returns reverse attribute when set."""
        mock_win.getmaxyx.return_value = (24, 80)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        # Set attribute
        grid.attrs[0][0] = 1

        char, attr = grid._get_border_symbol(0, 0)

        assert attr == curses.A_REVERSE


# -----------------------------------------------------------------------------
# _render_boxes tests
# -----------------------------------------------------------------------------


class TestGridRenderBoxes:
    """Test Grid._render_boxes method."""

    def test_renders_border_characters(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_render_boxes renders border characters to window."""
        mock_win.getmaxyx.return_value = (10, 20)
        mock_win.getbegyx.return_value = (0, 0)
        grid = Grid(mock_win)

        grid._render_boxes()

        # Should have called addch for border positions
        assert mock_win.addch.called

    def test_handles_curses_error_at_corner(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_render_boxes handles curses error at lower-right corner gracefully."""
        mock_win.getmaxyx.return_value = (10, 20)
        mock_win.getbegyx.return_value = (0, 0)

        # Only fail at the lower-right corner
        def selective_error(y, x, *args):
            if y == 9 and x == 19:
                raise curses.error("addch failed")

        mock_win.addch.side_effect = selective_error
        grid = Grid(mock_win)

        # Should not raise
        grid._render_boxes()

    def test_logs_error_for_non_corner_failure(
        self, mock_win, mock_mouse, mock_register_fkey, mock_logger
    ):
        """_render_boxes logs error for non-corner failures."""
        mock_win.getmaxyx.return_value = (10, 20)
        mock_win.getbegyx.return_value = (0, 0)

        # Fail on a non-corner position (top edge)
        def selective_error(y, x, *args):
            if y == 0 and x == 5:
                raise curses.error("addch failed")

        mock_win.addch.side_effect = selective_error
        grid = Grid(mock_win)

        grid._render_boxes()

        # Should have logged error
        mock_logger.error.assert_called()
