"""Tests for core module."""

import curses
from collections import defaultdict
from threading import Lock
from unittest.mock import MagicMock, call, patch

import pytest

import libcurses.core as core_module
from libcurses.core import is_fkey, preserve_cursor, register_fkey, wrapper

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def setup_fkeys():
    """Set up FKEYS global for testing."""
    original = getattr(core_module, "FKEYS", None)
    core_module.FKEYS = defaultdict(list)
    yield core_module.FKEYS
    if original is not None:
        core_module.FKEYS = original


@pytest.fixture
def setup_lock():
    """Set up LOCK global for testing."""
    original = getattr(core_module, "LOCK", None)
    core_module.LOCK = Lock()
    yield core_module.LOCK
    if original is not None:
        core_module.LOCK = original


@pytest.fixture
def mock_cursorwin():
    """Set up mock CURSORWIN for testing."""
    original = getattr(core_module, "CURSORWIN", None)
    mock_win = MagicMock()
    mock_win.getyx.return_value = (5, 10)
    core_module.CURSORWIN = mock_win
    yield mock_win
    if original is not None:
        core_module.CURSORWIN = original


# -----------------------------------------------------------------------------
# register_fkey tests
# -----------------------------------------------------------------------------


class TestRegisterFkey:
    """Test register_fkey function."""

    def test_register_single_handler(self, setup_fkeys):
        """Register a single handler for a key."""
        handler = MagicMock()
        register_fkey(handler, curses.KEY_F1)

        assert curses.KEY_F1 in setup_fkeys
        assert handler in setup_fkeys[curses.KEY_F1]

    def test_register_multiple_handlers_same_key(self, setup_fkeys):
        """Register multiple handlers for the same key."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        register_fkey(handler1, curses.KEY_F1)
        register_fkey(handler2, curses.KEY_F1)

        assert len(setup_fkeys[curses.KEY_F1]) == 2
        assert handler1 in setup_fkeys[curses.KEY_F1]
        assert handler2 in setup_fkeys[curses.KEY_F1]

    def test_register_handlers_different_keys(self, setup_fkeys):
        """Register handlers for different keys."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        register_fkey(handler1, curses.KEY_F1)
        register_fkey(handler2, curses.KEY_F2)

        assert handler1 in setup_fkeys[curses.KEY_F1]
        assert handler2 in setup_fkeys[curses.KEY_F2]

    def test_register_handler_for_all_keys(self, setup_fkeys):
        """Register a handler for key=0 (all keys)."""
        handler = MagicMock()
        register_fkey(handler, 0)

        assert 0 in setup_fkeys
        assert handler in setup_fkeys[0]

    def test_register_handler_default_key_zero(self, setup_fkeys):
        """Default key is 0 when not specified."""
        handler = MagicMock()
        register_fkey(handler)

        assert handler in setup_fkeys[0]

    def test_unregister_handler_with_none(self, setup_fkeys):
        """Passing func=None removes handlers for that key."""
        handler = MagicMock()
        register_fkey(handler, curses.KEY_F1)

        assert curses.KEY_F1 in setup_fkeys

        register_fkey(None, curses.KEY_F1)

        assert curses.KEY_F1 not in setup_fkeys

    def test_unregister_nonexistent_key_raises(self, setup_fkeys):
        """Unregistering a non-existent key raises KeyError."""
        with pytest.raises(KeyError):
            register_fkey(None, curses.KEY_F5)


# -----------------------------------------------------------------------------
# is_fkey tests
# -----------------------------------------------------------------------------


class TestIsFkey:
    """Test is_fkey function."""

    def test_registered_key_returns_true(self, setup_fkeys):
        """is_fkey returns True for registered key."""
        handler = MagicMock()
        register_fkey(handler, curses.KEY_F1)

        result = is_fkey(curses.KEY_F1)

        assert result is True

    def test_registered_key_calls_handler(self, setup_fkeys):
        """is_fkey calls the registered handler with the key."""
        handler = MagicMock()
        register_fkey(handler, curses.KEY_F1)

        is_fkey(curses.KEY_F1)

        handler.assert_called_once_with(curses.KEY_F1)

    def test_multiple_handlers_all_called(self, setup_fkeys):
        """All registered handlers are called in order."""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        register_fkey(handler1, curses.KEY_F1)
        register_fkey(handler2, curses.KEY_F1)
        register_fkey(handler3, curses.KEY_F1)

        is_fkey(curses.KEY_F1)

        handler1.assert_called_once_with(curses.KEY_F1)
        handler2.assert_called_once_with(curses.KEY_F1)
        handler3.assert_called_once_with(curses.KEY_F1)

    def test_unregistered_key_returns_false(self, setup_fkeys):
        """is_fkey returns False for unregistered key with no fallback."""
        result = is_fkey(curses.KEY_F1)

        assert result is False

    def test_fallback_to_key_zero(self, setup_fkeys):
        """Unregistered key falls back to key=0 handler."""
        handler = MagicMock()
        register_fkey(handler, 0)  # Register for all keys

        # KEY_F5 is not registered, but should fall back to key=0
        result = is_fkey(curses.KEY_F5)

        assert result is True
        handler.assert_called_once_with(curses.KEY_F5)

    def test_specific_key_takes_precedence_over_zero(self, setup_fkeys):
        """Specific key handler takes precedence over key=0."""
        all_handler = MagicMock()
        specific_handler = MagicMock()

        register_fkey(all_handler, 0)
        register_fkey(specific_handler, curses.KEY_F1)

        is_fkey(curses.KEY_F1)

        specific_handler.assert_called_once_with(curses.KEY_F1)
        all_handler.assert_not_called()

    def test_key_zero_not_called_when_specific_registered(self, setup_fkeys):
        """Key 0 handler not called when specific key is registered."""
        all_handler = MagicMock()
        specific_handler = MagicMock()

        register_fkey(all_handler, 0)
        register_fkey(specific_handler, curses.KEY_F1)

        is_fkey(curses.KEY_F1)

        all_handler.assert_not_called()


# -----------------------------------------------------------------------------
# preserve_cursor tests
# -----------------------------------------------------------------------------


class TestPreserveCursor:
    """Test preserve_cursor context manager."""

    def test_yields_cursor_position(self, setup_lock, mock_cursorwin):
        """Context manager yields current cursor position."""
        mock_cursorwin.getyx.return_value = (7, 15)

        with preserve_cursor() as pos:
            assert pos == (7, 15)

    def test_restores_cursor_position(self, setup_lock, mock_cursorwin):
        """Cursor position is restored after context."""
        mock_cursorwin.getyx.return_value = (7, 15)

        with preserve_cursor():
            pass

        mock_cursorwin.move.assert_called_with(7, 15)
        mock_cursorwin.refresh.assert_called_once()

    def test_restores_cursor_even_on_exception(self, setup_lock, mock_cursorwin):
        """Cursor is restored even if exception is raised."""
        mock_cursorwin.getyx.return_value = (3, 8)

        with pytest.raises(ValueError, match="test error"), preserve_cursor():
            raise ValueError("test error")

        mock_cursorwin.move.assert_called_with(3, 8)
        mock_cursorwin.refresh.assert_called_once()

    def test_handles_move_error(self, setup_lock, mock_cursorwin, capsys):
        """Handles curses.error during move gracefully."""
        mock_cursorwin.getyx.return_value = (5, 10)
        mock_cursorwin.move.side_effect = curses.error("move failed")

        with preserve_cursor():
            pass

        # Should print error to stderr but not raise
        captured = capsys.readouterr()
        assert "move(5, 10)" in captured.err
        assert "move failed" in captured.err

    def test_uses_setsyx_when_no_cursorwin(self, setup_lock):
        """Uses curses.setsyx when CURSORWIN is None."""
        core_module.CURSORWIN = None

        with (
            patch("curses.getsyx", return_value=(2, 4)),
            patch("curses.setsyx") as mock_setsyx,
            patch("curses.doupdate") as mock_doupdate,
        ):
            with preserve_cursor() as pos:
                assert pos == (2, 4)

            mock_setsyx.assert_called_with(2, 4)
            mock_doupdate.assert_called_once()

    def test_lock_is_held_during_context(self, setup_lock, mock_cursorwin):
        """Lock is held during the context."""
        lock_held = []

        def check_lock():
            # Try to acquire without blocking - should fail if held
            acquired = setup_lock.acquire(blocking=False)
            if acquired:
                setup_lock.release()
            lock_held.append(not acquired)

        with preserve_cursor():
            check_lock()

        assert lock_held[0] is True  # Lock was held during context


# -----------------------------------------------------------------------------
# wrapper tests
# -----------------------------------------------------------------------------


class TestWrapper:
    """Test wrapper function."""

    def test_wrapper_calls_curses_wrapper(self):
        """wrapper calls curses.wrapper with inner function."""
        user_func = MagicMock()

        with patch("curses.wrapper") as mock_curses_wrapper:
            wrapper(user_func)

        mock_curses_wrapper.assert_called_once()

    def test_wrapper_initializes_globals(self):
        """wrapper initializes CURSORWIN, LOCK, and FKEYS."""
        user_func = MagicMock()
        mock_stdscr = MagicMock()

        def fake_curses_wrapper(func):
            func(mock_stdscr)

        with patch("curses.wrapper", side_effect=fake_curses_wrapper):
            wrapper(user_func)

        assert core_module.CURSORWIN is mock_stdscr
        assert isinstance(core_module.LOCK, Lock)  # noqa: PLW116
        assert isinstance(core_module.FKEYS, defaultdict)

    def test_wrapper_calls_user_function(self):
        """wrapper calls the user's function with stdscr."""
        user_func = MagicMock()
        mock_stdscr = MagicMock()

        def fake_curses_wrapper(func):
            func(mock_stdscr)

        with patch("curses.wrapper", side_effect=fake_curses_wrapper):
            wrapper(user_func)

        user_func.assert_called_once_with(mock_stdscr)

    def test_fkeys_is_defaultdict_of_lists(self):
        """FKEYS is initialized as defaultdict(list)."""
        user_func = MagicMock()
        mock_stdscr = MagicMock()

        def fake_curses_wrapper(func):
            func(mock_stdscr)

        with patch("curses.wrapper", side_effect=fake_curses_wrapper):
            wrapper(user_func)

        # Access a non-existent key - should return empty list
        assert core_module.FKEYS[999] == []
