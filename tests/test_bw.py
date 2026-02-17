"""Tests for BorderedWindow class."""

import curses
from unittest.mock import MagicMock, call, patch

import pytest

from libcurses.border import Border
from libcurses.bw import BorderedWindow


@pytest.fixture
def mock_newwin():
    """Mock curses.newwin to return mock windows."""
    mock_border_win = MagicMock(name="border_win")
    mock_inner_win = MagicMock(name="inner_win")

    # Set up return values for getyx, getbegyx, getmaxyx
    mock_border_win.getyx.return_value = (0, 0)
    mock_border_win.getbegyx.return_value = (5, 10)
    mock_border_win.getmaxyx.return_value = (20, 40)

    mock_inner_win.getyx.return_value = (0, 0)
    mock_inner_win.getbegyx.return_value = (6, 11)
    mock_inner_win.getmaxyx.return_value = (18, 38)

    windows = [mock_border_win, mock_inner_win]
    call_count = [0]

    def fake_newwin(*args):
        win = windows[call_count[0]]
        call_count[0] += 1
        return win

    with patch("curses.newwin", side_effect=fake_newwin):
        yield {"b": mock_border_win, "w": mock_inner_win}


# -----------------------------------------------------------------------------
# Initialization tests
# -----------------------------------------------------------------------------


class TestBorderedWindowInit:
    """Test BorderedWindow initialization."""

    def test_stores_dimensions(self, mock_newwin):
        """BorderedWindow stores dimensions."""
        bw = BorderedWindow(20, 40, 5, 10)

        assert bw.nlines == 20
        assert bw.ncols == 40
        assert bw.begin_y == 5
        assert bw.begin_x == 10

    def test_creates_border_window(self, mock_newwin):
        """BorderedWindow creates outer border window."""
        with patch("curses.newwin") as mock_new:
            mock_new.return_value = MagicMock()
            bw = BorderedWindow(20, 40, 5, 10)

        # First call should be for border window with full dimensions
        first_call = mock_new.call_args_list[0]
        assert first_call == call(20, 40, 5, 10)

    def test_creates_inner_window(self, mock_newwin):
        """BorderedWindow creates inner window with offset."""
        with patch("curses.newwin") as mock_new:
            mock_new.return_value = MagicMock()
            bw = BorderedWindow(20, 40, 5, 10)

        # Second call should be for inner window (smaller, offset)
        second_call = mock_new.call_args_list[1]
        assert second_call == call(18, 38, 6, 11)  # nlines-2, ncols-2, y+1, x+1

    def test_configures_inner_window(self, mock_newwin):
        """BorderedWindow configures inner window for scrolling."""
        bw = BorderedWindow(20, 40, 5, 10)

        mock_newwin["w"].scrollok.assert_called_with(True)
        mock_newwin["w"].idlok.assert_called_with(True)
        mock_newwin["w"].leaveok.assert_called_with(False)
        mock_newwin["w"].keypad.assert_called_with(True)
        mock_newwin["w"].refresh.assert_called()

    def test_sets_default_border(self, mock_newwin):
        """BorderedWindow sets default border when none specified."""
        bw = BorderedWindow(20, 40, 5, 10)

        mock_newwin["b"].border.assert_called_once()
        # Default Border() has all zeros
        call_args = mock_newwin["b"].border.call_args[0]
        assert call_args == (0, 0, 0, 0, 0, 0, 0, 0)

    def test_sets_custom_border(self, mock_newwin):
        """BorderedWindow sets custom border when specified."""
        custom_border = Border(
            ls=ord("|"),
            rs=ord("|"),
            ts=ord("-"),
            bs=ord("-"),
            tl=ord("+"),
            tr=ord("+"),
            bl=ord("+"),
            br=ord("+"),
        )
        bw = BorderedWindow(20, 40, 5, 10, border=custom_border)

        call_args = mock_newwin["b"].border.call_args[0]
        assert call_args == tuple(custom_border)


# -----------------------------------------------------------------------------
# __repr__ tests
# -----------------------------------------------------------------------------


class TestBorderedWindowRepr:
    """Test BorderedWindow.__repr__ method."""

    def test_repr_contains_class_name(self, mock_newwin):
        """repr contains class name."""
        bw = BorderedWindow(20, 40, 5, 10)

        assert "BorderedWindow(" in repr(bw)

    def test_repr_contains_dimensions(self, mock_newwin):
        """repr contains dimensions."""
        bw = BorderedWindow(20, 40, 5, 10)
        r = repr(bw)

        assert "nlines=20" in r
        assert "ncols=40" in r
        assert "begin_y=5" in r
        assert "begin_x=10" in r

    def test_repr_contains_window_info(self, mock_newwin):
        """repr contains window getbegyx and getmaxyx info."""
        bw = BorderedWindow(20, 40, 5, 10)
        r = repr(bw)

        assert "getbegyx=" in r
        assert "getmaxyx=" in r


# -----------------------------------------------------------------------------
# redraw tests
# -----------------------------------------------------------------------------


class TestBorderedWindowRedraw:
    """Test BorderedWindow.redraw method."""

    def test_redraws_both_windows(self, mock_newwin):
        """redraw calls redrawwin on both windows."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.redraw()

        mock_newwin["b"].redrawwin.assert_called_once()
        mock_newwin["w"].redrawwin.assert_called_once()


# -----------------------------------------------------------------------------
# refresh tests
# -----------------------------------------------------------------------------


class TestBorderedWindowRefresh:
    """Test BorderedWindow.refresh method."""

    def test_refreshes_both_windows(self, mock_newwin):
        """refresh calls refresh on both windows."""
        bw = BorderedWindow(20, 40, 5, 10)
        mock_newwin["b"].reset_mock()
        mock_newwin["w"].reset_mock()

        bw.refresh()

        mock_newwin["b"].refresh.assert_called_once()
        mock_newwin["w"].refresh.assert_called_once()


# -----------------------------------------------------------------------------
# border tests
# -----------------------------------------------------------------------------


class TestBorderedWindowBorder:
    """Test BorderedWindow.border method."""

    def test_sets_border(self, mock_newwin):
        """border sets the border on the outer window."""
        bw = BorderedWindow(20, 40, 5, 10)
        mock_newwin["b"].reset_mock()

        new_border = Border(1, 2, 3, 4, 5, 6, 7, 8)
        bw.border(new_border)

        mock_newwin["b"].border.assert_called_once_with(1, 2, 3, 4, 5, 6, 7, 8)


# -----------------------------------------------------------------------------
# resize tests
# -----------------------------------------------------------------------------


class TestBorderedWindowResize:
    """Test BorderedWindow.resize method."""

    def test_resizes_both_windows(self, mock_newwin):
        """resize resizes both windows."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.resize(30, 50)

        mock_newwin["b"].resize.assert_called_with(30, 50)
        mock_newwin["w"].resize.assert_called_with(28, 48)  # -2 for border

    def test_updates_dimensions(self, mock_newwin):
        """resize updates stored dimensions."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.resize(30, 50)

        assert bw.nlines == 30
        assert bw.ncols == 50

    def test_constrains_cursor_position(self, mock_newwin):
        """resize moves cursor to fit within new dimensions."""
        mock_newwin["b"].getyx.return_value = (25, 45)
        mock_newwin["w"].getyx.return_value = (20, 40)
        bw = BorderedWindow(20, 40, 5, 10)

        bw.resize(15, 30)

        # Cursor should be moved to fit within new dimensions
        mock_newwin["b"].move.assert_called()
        mock_newwin["w"].move.assert_called()


# -----------------------------------------------------------------------------
# mvwin tests
# -----------------------------------------------------------------------------


class TestBorderedWindowMvwin:
    """Test BorderedWindow.mvwin method."""

    def test_moves_both_windows(self, mock_newwin):
        """mvwin moves both windows."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.mvwin(15, 20)

        mock_newwin["b"].mvwin.assert_called_with(15, 20)
        mock_newwin["w"].mvwin.assert_called_with(16, 21)  # +1 for border offset

    def test_updates_position(self, mock_newwin):
        """mvwin updates stored position."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.mvwin(15, 20)

        assert bw.begin_y == 15
        assert bw.begin_x == 20

    def test_refreshes_after_move(self, mock_newwin):
        """mvwin refreshes windows after moving."""
        bw = BorderedWindow(20, 40, 5, 10)
        mock_newwin["b"].reset_mock()
        mock_newwin["w"].reset_mock()

        bw.mvwin(15, 20)

        mock_newwin["b"].refresh.assert_called()
        mock_newwin["w"].refresh.assert_called()


# -----------------------------------------------------------------------------
# addstr tests
# -----------------------------------------------------------------------------


class TestBorderedWindowAddstr:
    """Test BorderedWindow.addstr method."""

    def test_addstr_without_attr(self, mock_newwin):
        """addstr without attr calls w.addstr with just string."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.addstr("Hello")

        mock_newwin["w"].addstr.assert_called_with("Hello")

    def test_addstr_with_attr(self, mock_newwin):
        """addstr with attr calls w.addstr with string and attr."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.addstr("Hello", curses.A_BOLD)

        mock_newwin["w"].addstr.assert_called_with("Hello", curses.A_BOLD)

    def test_addstr_with_zero_attr(self, mock_newwin):
        """addstr with attr=0 still passes the attr."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.addstr("Hello", 0)

        # 0 is falsy but not None, so should still be passed
        mock_newwin["w"].addstr.assert_called_with("Hello", 0)

    def test_addstr_with_none_attr(self, mock_newwin):
        """addstr with attr=None doesn't pass attr."""
        bw = BorderedWindow(20, 40, 5, 10)

        bw.addstr("Hello", None)

        mock_newwin["w"].addstr.assert_called_with("Hello")
