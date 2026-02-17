"""Tests for getkey function."""

import curses
import curses.ascii
from threading import Lock
from unittest.mock import MagicMock, patch

import pytest

import libcurses.core as core_module
from libcurses.getkey import getkey


@pytest.fixture(autouse=True)
def setup_core_globals():
    """Set up core module globals for testing."""
    original_lock = getattr(core_module, "LOCK", None)
    original_cursorwin = getattr(core_module, "CURSORWIN", None)

    core_module.LOCK = Lock()
    core_module.CURSORWIN = MagicMock()

    yield

    if original_lock is not None:
        core_module.LOCK = original_lock
    if original_cursorwin is not None:
        core_module.CURSORWIN = original_cursorwin


@pytest.fixture
def mock_win():
    """Create mock curses window."""
    win = MagicMock()
    win.getch.return_value = ord("a")
    return win


@pytest.fixture
def mock_keyname():
    """Mock curses.keyname."""

    def fake_keyname(key):
        if key == curses.KEY_MOUSE:
            return b"KEY_MOUSE"
        if key == curses.KEY_RESIZE:
            return b"KEY_RESIZE"
        if 32 <= key <= 126:
            return bytes([key])
        return f"KEY_{key}".encode()

    with patch("curses.keyname", side_effect=fake_keyname):
        yield


# -----------------------------------------------------------------------------
# Basic functionality tests
# -----------------------------------------------------------------------------


class TestGetkeyBasic:
    """Test basic getkey functionality."""

    def test_returns_key_value(self, mock_win, mock_keyname):
        """getkey returns the key value from getch."""
        mock_win.getch.return_value = ord("x")

        with patch("curses.doupdate"):
            result = getkey(mock_win)

        assert result == ord("x")

    def test_returns_negative_in_nodelay_mode(self, mock_win, mock_keyname):
        """getkey returns -1 in no-delay mode when no input."""
        mock_win.getch.return_value = -1

        with patch("curses.doupdate"):
            result = getkey(mock_win)

        assert result == -1

    def test_returns_none_on_eot(self, mock_win, mock_keyname):
        """getkey returns None on EOT (Ctrl-D)."""
        mock_win.getch.return_value = curses.ascii.EOT

        with patch("curses.doupdate"):
            result = getkey(mock_win)

        assert result is None

    def test_returns_none_on_keyboard_interrupt(self, mock_win, mock_keyname):
        """getkey returns None on KeyboardInterrupt."""
        mock_win.getch.side_effect = KeyboardInterrupt()

        with patch("curses.doupdate"):
            result = getkey(mock_win)

        assert result is None

    def test_calls_noutrefresh(self, mock_win, mock_keyname):
        """getkey calls noutrefresh on window."""
        mock_win.getch.return_value = ord("a")

        with patch("curses.doupdate"):
            getkey(mock_win)

        mock_win.noutrefresh.assert_called()

    def test_calls_doupdate(self, mock_win, mock_keyname):
        """getkey calls curses.doupdate."""
        mock_win.getch.return_value = ord("a")

        with patch("curses.doupdate") as mock_doupdate:
            getkey(mock_win)

        mock_doupdate.assert_called()

    def test_logs_trace(self, mock_win, mock_keyname):
        """getkey logs trace message."""
        mock_win.getch.return_value = ord("a")

        with patch("curses.doupdate"), patch("libcurses.getkey.logger") as mock_logger:
            getkey(mock_win)

        mock_logger.trace.assert_called()


# -----------------------------------------------------------------------------
# Window handling tests
# -----------------------------------------------------------------------------


class TestGetkeyWindowHandling:
    """Test getkey window handling."""

    def test_uses_cursorwin_when_win_is_none(self, mock_keyname):
        """getkey uses CURSORWIN when win parameter is None."""
        mock_cursorwin = MagicMock()
        mock_cursorwin.getch.return_value = ord("a")
        core_module.CURSORWIN = mock_cursorwin

        with patch("curses.doupdate"):
            result = getkey(None)

        mock_cursorwin.getch.assert_called()
        assert result == ord("a")

    def test_sets_cursorwin_to_provided_window(self, mock_win, mock_keyname):
        """getkey sets CURSORWIN to the provided window."""
        mock_win.getch.return_value = ord("a")

        with patch("curses.doupdate"):
            getkey(mock_win)

        assert core_module.CURSORWIN is mock_win

    def test_asserts_cursorwin_exists_when_win_none(self, mock_keyname):
        """getkey asserts CURSORWIN exists when win is None."""
        core_module.CURSORWIN = None

        with patch("curses.doupdate"), pytest.raises(AssertionError):
            getkey(None)


# -----------------------------------------------------------------------------
# Mouse handling tests
# -----------------------------------------------------------------------------


class TestGetkeyMouseHandling:
    """Test getkey mouse event handling."""

    def test_handles_mouse_event_by_default(self, mock_win, mock_keyname):
        """getkey handles KEY_MOUSE and continues loop."""
        # First return KEY_MOUSE, then a regular key
        mock_win.getch.side_effect = [curses.KEY_MOUSE, ord("a")]

        with (
            patch("curses.doupdate"),
            patch("libcurses.getkey.Mouse.handle_mouse_event") as mock_handle,
        ):
            result = getkey(mock_win)

        mock_handle.assert_called_once()
        assert result == ord("a")

    def test_no_mouse_skips_mouse_handling(self, mock_win, mock_keyname):
        """getkey with no_mouse=True returns KEY_MOUSE directly."""
        mock_win.getch.return_value = curses.KEY_MOUSE

        with (
            patch("curses.doupdate"),
            patch("libcurses.getkey.Mouse.handle_mouse_event") as mock_handle,
        ):
            result = getkey(mock_win, no_mouse=True)

        mock_handle.assert_not_called()
        assert result == curses.KEY_MOUSE

    def test_mouse_event_loops_until_non_mouse(self, mock_win, mock_keyname):
        """getkey loops on multiple mouse events until non-mouse key."""
        # Return multiple KEY_MOUSE, then a regular key
        mock_win.getch.side_effect = [
            curses.KEY_MOUSE,
            curses.KEY_MOUSE,
            curses.KEY_MOUSE,
            ord("b"),
        ]

        with (
            patch("curses.doupdate"),
            patch("libcurses.getkey.Mouse.handle_mouse_event") as mock_handle,
        ):
            result = getkey(mock_win)

        assert mock_handle.call_count == 3
        assert result == ord("b")


# -----------------------------------------------------------------------------
# Resize handling tests
# -----------------------------------------------------------------------------


class TestGetkeyResizeHandling:
    """Test getkey terminal resize handling."""

    def test_handles_resize_when_term_resized(self, mock_win, mock_keyname):
        """getkey updates lines/cols on KEY_RESIZE when terminal resized."""
        mock_win.getch.return_value = curses.KEY_RESIZE

        # Set up curses.LINES and curses.COLS
        curses.LINES = 24
        curses.COLS = 80

        try:
            with (
                patch("curses.doupdate"),
                patch("curses.is_term_resized", return_value=True) as mock_is_resized,
                patch("curses.update_lines_cols") as mock_update,
            ):
                result = getkey(mock_win)

            mock_is_resized.assert_called_once_with(24, 80)
            mock_update.assert_called_once()
            assert result == curses.KEY_RESIZE
        finally:
            del curses.LINES
            del curses.COLS

    def test_skips_update_when_not_resized(self, mock_win, mock_keyname):
        """getkey skips update_lines_cols when terminal not actually resized."""
        mock_win.getch.return_value = curses.KEY_RESIZE

        # Set up curses.LINES and curses.COLS
        curses.LINES = 24
        curses.COLS = 80

        try:
            with (
                patch("curses.doupdate"),
                patch("curses.is_term_resized", return_value=False),
                patch("curses.update_lines_cols") as mock_update,
            ):
                result = getkey(mock_win)

            mock_update.assert_not_called()
            assert result == curses.KEY_RESIZE
        finally:
            del curses.LINES
            del curses.COLS


# -----------------------------------------------------------------------------
# Edge cases
# -----------------------------------------------------------------------------


class TestGetkeyEdgeCases:
    """Test getkey edge cases."""

    def test_returns_special_keys(self, mock_win, mock_keyname):
        """getkey returns special key codes."""
        mock_win.getch.return_value = curses.KEY_UP

        with patch("curses.doupdate"):
            result = getkey(mock_win)

        assert result == curses.KEY_UP

    def test_returns_function_keys(self, mock_win, mock_keyname):
        """getkey returns function key codes."""
        mock_win.getch.return_value = curses.KEY_F1

        with patch("curses.doupdate"):
            result = getkey(mock_win)

        assert result == curses.KEY_F1

    def test_lock_is_used(self, mock_win, mock_keyname):
        """getkey uses the LOCK for thread safety."""
        mock_win.getch.return_value = ord("a")
        lock_acquired = []

        original_lock = core_module.LOCK

        class TrackingLock:
            def __enter__(self):
                lock_acquired.append(True)
                return original_lock.__enter__()

            def __exit__(self, *args):
                return original_lock.__exit__(*args)

        core_module.LOCK = TrackingLock()

        with patch("curses.doupdate"):
            getkey(mock_win)

        assert len(lock_acquired) >= 1  # Lock should be acquired at least once
