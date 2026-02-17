"""Tests for WindowStack class."""

import curses
from unittest.mock import MagicMock, call, patch

import pytest

from libcurses.border import Border
from libcurses.stack import WindowStack


@pytest.fixture(autouse=True)
def mock_acs_constants():
    """Mock curses ACS constants that require initialization."""
    # These constants don't exist until curses.initscr() is called
    curses.ACS_TTEE = ord("T")  # type: ignore[misc]
    curses.ACS_BTEE = ord("B")  # type: ignore[misc]
    curses.ACS_LTEE = ord("L")  # type: ignore[misc]
    curses.ACS_RTEE = ord("R")  # type: ignore[misc]
    yield
    # Clean up
    del curses.ACS_TTEE
    del curses.ACS_BTEE
    del curses.ACS_LTEE
    del curses.ACS_RTEE


@pytest.fixture
def mock_neighbor():
    """Create mock neighbor BorderedWindow."""
    neighbor = MagicMock()
    neighbor.begin_x = 0
    neighbor.begin_y = 0
    neighbor.ncols = 40
    neighbor.nlines = 24
    return neighbor


@pytest.fixture
def mock_bordered_window():
    """Mock BorderedWindow class."""
    with patch("libcurses.stack.BorderedWindow") as mock_bw:
        # Make each call return a new MagicMock with appropriate attributes
        def create_mock_bw(nlines, ncols, begin_y, begin_x):
            bw = MagicMock()
            bw.nlines = nlines
            bw.ncols = ncols
            bw.begin_y = begin_y
            bw.begin_x = begin_x
            return bw

        mock_bw.side_effect = create_mock_bw
        yield mock_bw


# -----------------------------------------------------------------------------
# Initialization tests
# -----------------------------------------------------------------------------


class TestWindowStackInit:
    """Test WindowStack initialization."""

    def test_stores_neighbor_left(self, mock_neighbor):
        """WindowStack stores neighbor_left."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        assert stack.neighbor_left is mock_neighbor

    def test_stores_padding_y(self, mock_neighbor):
        """WindowStack stores padding_y."""
        stack = WindowStack(mock_neighbor, padding_y=5)

        assert stack.padding_y == 5

    def test_calculates_begin_x(self, mock_neighbor):
        """WindowStack calculates begin_x from neighbor."""
        mock_neighbor.begin_x = 10
        mock_neighbor.ncols = 30

        stack = WindowStack(mock_neighbor, padding_y=2)

        # begin_x = neighbor.begin_x + neighbor.ncols - 1 = 10 + 30 - 1 = 39
        assert stack.begin_x == 39

    def test_initializes_empty_windows_list(self, mock_neighbor):
        """WindowStack initializes empty windows list."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        assert stack.windows == []


# -----------------------------------------------------------------------------
# redraw tests
# -----------------------------------------------------------------------------


class TestWindowStackRedraw:
    """Test WindowStack.redraw method."""

    def test_redraws_all_windows(self, mock_neighbor, mock_bordered_window):
        """redraw calls redraw on all windows."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)

        for w in stack.windows:
            w.reset_mock()

        stack.redraw()

        for w in stack.windows:
            w.redraw.assert_called_once()

    def test_redraw_empty_stack(self, mock_neighbor):
        """redraw on empty stack doesn't raise."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.redraw()  # Should not raise


# -----------------------------------------------------------------------------
# refresh tests
# -----------------------------------------------------------------------------


class TestWindowStackRefresh:
    """Test WindowStack.refresh method."""

    def test_refreshes_all_windows(self, mock_neighbor, mock_bordered_window):
        """refresh calls refresh on all windows."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)

        for w in stack.windows:
            w.reset_mock()

        stack.refresh()

        for w in stack.windows:
            w.refresh.assert_called_once()

    def test_refresh_empty_stack(self, mock_neighbor):
        """refresh on empty stack doesn't raise."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.refresh()  # Should not raise


# -----------------------------------------------------------------------------
# get_border tests
# -----------------------------------------------------------------------------


class TestWindowStackGetBorder:
    """Test WindowStack.get_border method."""

    def test_first_not_final(self, mock_neighbor, mock_bordered_window):
        """get_border for first window with more to come."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)  # Add second so first is not final

        border = stack.get_border(0)

        assert border.tl == curses.ACS_TTEE
        assert border.bl == curses.ACS_LTEE
        assert border.br == curses.ACS_RTEE

    def test_first_and_final(self, mock_neighbor, mock_bordered_window):
        """get_border for first and only window."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)

        border = stack.get_border(0)

        assert border.tl == curses.ACS_TTEE
        assert border.bl == curses.ACS_BTEE

    def test_middle_window(self, mock_neighbor, mock_bordered_window):
        """get_border for middle window (not first, not final)."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(8, 20)
        stack.append(8, 20)
        stack.append(8, 20)

        border = stack.get_border(1)  # Middle window

        assert border.tl == curses.ACS_LTEE
        assert border.tr == curses.ACS_RTEE
        assert border.bl == curses.ACS_LTEE
        assert border.br == curses.ACS_RTEE

    def test_additional_and_final(self, mock_neighbor, mock_bordered_window):
        """get_border for last window (not first)."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)

        border = stack.get_border(1)  # Second/last window

        assert border.tl == curses.ACS_LTEE
        assert border.tr == curses.ACS_RTEE
        assert border.bl == curses.ACS_BTEE


# -----------------------------------------------------------------------------
# append tests
# -----------------------------------------------------------------------------


class TestWindowStackAppend:
    """Test WindowStack.append method."""

    def test_first_window_aligns_with_neighbor_top(self, mock_neighbor, mock_bordered_window):
        """First window aligns with neighbor's top."""
        mock_neighbor.begin_y = 5
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.append(10, 20)

        # BorderedWindow called with begin_y = neighbor.begin_y
        mock_bordered_window.assert_called_once()
        call_args = mock_bordered_window.call_args[0]
        assert call_args[2] == 5  # begin_y

    def test_additional_window_joins_above(self, mock_neighbor, mock_bordered_window):
        """Additional windows join to window above."""
        mock_neighbor.begin_y = 0
        stack = WindowStack(mock_neighbor, padding_y=2)

        # First window at y=0, height=10
        stack.append(10, 20)
        first_win = stack.windows[0]
        first_win.begin_y = 0
        first_win.nlines = 10

        # Second window should start at y = 0 + 10 - 1 = 9
        stack.append(8, 20)

        second_call = mock_bordered_window.call_args_list[1]
        assert second_call[0][2] == 9  # begin_y

    def test_first_and_final_full_height(self, mock_neighbor, mock_bordered_window):
        """First and final window gets full height."""
        mock_neighbor.nlines = 24
        stack = WindowStack(mock_neighbor, padding_y=2)

        # nlines=0 means final
        stack.append(0, 20)

        call_args = mock_bordered_window.call_args[0]
        assert call_args[0] == 24  # nlines = neighbor.nlines

    def test_additional_and_final_variable_height(self, mock_neighbor, mock_bordered_window):
        """Additional final window gets remaining height."""
        mock_neighbor.begin_y = 0
        mock_neighbor.nlines = 24
        stack = WindowStack(mock_neighbor, padding_y=2)

        # First window
        stack.append(10, 20)
        first_win = stack.windows[0]
        first_win.begin_y = 0
        first_win.nlines = 10

        # Final window (nlines=0)
        stack.append(0, 20)

        # Height should be calculated based on remaining space
        second_call = mock_bordered_window.call_args_list[1]
        # nlines = neighbor.nlines - ((prev.begin_y + prev.nlines - 1) - padding_y)
        # = 24 - ((0 + 10 - 1) - 2) = 24 - 7 = 17
        assert second_call[0][0] == 17

    def test_returns_bordered_window(self, mock_neighbor, mock_bordered_window):
        """append returns the created BorderedWindow."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        result = stack.append(10, 20)

        assert result is stack.windows[0]

    def test_adds_to_windows_list(self, mock_neighbor, mock_bordered_window):
        """append adds window to windows list."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.append(10, 20)
        stack.append(8, 20)

        assert len(stack.windows) == 2

    def test_sets_border(self, mock_neighbor, mock_bordered_window):
        """append sets appropriate border on window."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.append(10, 20)

        stack.windows[0].border.assert_called()

    def test_uses_calculated_begin_x(self, mock_neighbor, mock_bordered_window):
        """append uses stack's begin_x."""
        mock_neighbor.begin_x = 10
        mock_neighbor.ncols = 30
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.append(10, 20)

        call_args = mock_bordered_window.call_args[0]
        assert call_args[3] == 39  # begin_x = 10 + 30 - 1


# -----------------------------------------------------------------------------
# insert tests
# -----------------------------------------------------------------------------


class TestWindowStackInsert:
    """Test WindowStack.insert method."""

    def test_insert_empty_stack_calls_append(self, mock_neighbor, mock_bordered_window):
        """insert on empty stack calls append."""
        stack = WindowStack(mock_neighbor, padding_y=2)

        stack.insert(10, 20, loc=0)

        assert len(stack.windows) == 1

    def test_insert_validates_loc_too_low(self, mock_neighbor, mock_bordered_window):
        """insert raises ValueError if loc too low."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)

        with pytest.raises(ValueError, match="loc .* is not"):
            stack.insert(5, 20, loc=-3)  # Only -2 to 1 valid for 2 windows

    def test_insert_validates_loc_too_high(self, mock_neighbor, mock_bordered_window):
        """insert raises ValueError if loc too high."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)

        with pytest.raises(ValueError, match="loc .* is not"):
            stack.insert(5, 20, loc=2)  # Only -2 to 1 valid for 2 windows

    def test_insert_handles_negative_loc(self, mock_neighbor, mock_bordered_window):
        """insert handles negative loc correctly."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        stack.append(10, 20)

        # -1 should be last window position (index 1)
        # -2 should be first window position (index 0)
        stack.insert(5, 20, loc=-2)

        # Should have 3 windows now
        assert len(stack.windows) == 3

    def test_insert_validates_minimum_size(self, mock_neighbor, mock_bordered_window):
        """insert raises ValueError if last window would be too small."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        last_win = stack.windows[-1]
        last_win.nlines = 5  # Only 5 lines

        with pytest.raises(ValueError, match="Can't shrink"):
            stack.insert(4, 20, loc=0)  # Would leave only 2 lines

    def test_insert_shrinks_last_window(self, mock_neighbor, mock_bordered_window):
        """insert shrinks the last window."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(20, 20)
        last_win = stack.windows[-1]
        last_win.nlines = 20
        last_win.ncols = 20

        stack.insert(5, 20, loc=0)

        # Last window should be resized
        last_win.resize.assert_called()

    def test_insert_slides_windows_down(self, mock_neighbor, mock_bordered_window):
        """insert slides existing windows down."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(10, 20)
        first_win = stack.windows[0]
        first_win.begin_y = 0
        first_win.begin_x = 39
        first_win.nlines = 20

        stack.insert(5, 20, loc=0)

        # First window should have been moved
        first_win.mvwin.assert_called()

    def test_insert_creates_new_window(self, mock_neighbor, mock_bordered_window):
        """insert creates new BorderedWindow at location."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(20, 20)
        first_win = stack.windows[0]
        first_win.begin_y = 0
        first_win.begin_x = 39
        first_win.nlines = 20

        stack.insert(5, 25, loc=0)

        # Should have 2 windows now
        assert len(stack.windows) == 2
        # New window should be at index 0
        assert stack.windows[0] != first_win

    def test_insert_adjusts_all_borders(self, mock_neighbor, mock_bordered_window):
        """insert adjusts borders of all windows."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(20, 20)
        first_win = stack.windows[0]
        first_win.nlines = 20

        stack.insert(5, 20, loc=0)

        # Both windows should have border called
        for w in stack.windows:
            w.border.assert_called()

    def test_insert_at_zero(self, mock_neighbor, mock_bordered_window):
        """insert at loc=0 inserts at beginning."""
        stack = WindowStack(mock_neighbor, padding_y=2)
        stack.append(20, 20)
        original_first = stack.windows[0]
        original_first.nlines = 20
        original_first.begin_y = 0
        original_first.begin_x = 39

        stack.insert(5, 20, loc=0)

        # Original first should now be second
        assert stack.windows[1] is original_first
