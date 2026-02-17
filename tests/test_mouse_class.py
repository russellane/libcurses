"""Tests for Mouse class."""

import curses
from collections import defaultdict
from unittest.mock import MagicMock, patch

import pytest

from libcurses.mouse import Mouse, add_mouse_handler, clear_mouse_handlers


@pytest.fixture(autouse=True)
def reset_mouse_state():
    """Reset Mouse class state before each test."""
    Mouse._handlers = []
    Mouse._yxhandlers_by_row = defaultdict(list)
    yield
    Mouse._handlers = []
    Mouse._yxhandlers_by_row = defaultdict(list)


# -----------------------------------------------------------------------------
# enable tests
# -----------------------------------------------------------------------------


class TestMouseEnable:
    """Test Mouse.enable method."""

    def test_enable_calls_mousemask(self):
        """enable() calls curses.mousemask with correct flags."""
        with patch("curses.mousemask", return_value=(0xFFFF, 0)) as mock_mousemask:
            Mouse.enable()

        expected_mask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
        mock_mousemask.assert_called_once_with(expected_mask)

    def test_enable_logs_trace(self):
        """enable() logs trace message."""
        with (
            patch("curses.mousemask", return_value=(0x1234, 0x5678)),
            patch("libcurses.mouse.logger") as mock_logger,
        ):
            Mouse.enable()

        mock_logger.trace.assert_called_once()
        call_args = mock_logger.trace.call_args[0][0]
        assert "availmask" in call_args
        assert "oldmask" in call_args


# -----------------------------------------------------------------------------
# add_internal_mouse_handler tests
# -----------------------------------------------------------------------------


class TestAddInternalMouseHandler:
    """Test Mouse.add_internal_mouse_handler method."""

    def test_add_single_handler(self):
        """Add a single internal handler."""
        handler = MagicMock()

        Mouse.add_internal_mouse_handler(handler)

        assert len(Mouse._handlers) == 1
        assert Mouse._handlers[0].func is handler
        assert Mouse._handlers[0].args is None

    def test_add_handler_with_args(self):
        """Add handler with additional args."""
        handler = MagicMock()
        args = {"key": "value"}

        Mouse.add_internal_mouse_handler(handler, args)

        assert Mouse._handlers[0].func is handler
        assert Mouse._handlers[0].args == args

    def test_add_multiple_handlers(self):
        """Add multiple internal handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        Mouse.add_internal_mouse_handler(handler1)
        Mouse.add_internal_mouse_handler(handler2, "arg2")
        Mouse.add_internal_mouse_handler(handler3, "arg3")

        assert len(Mouse._handlers) == 3
        assert Mouse._handlers[0].func is handler1
        assert Mouse._handlers[1].func is handler2
        assert Mouse._handlers[2].func is handler3


# -----------------------------------------------------------------------------
# add_mouse_handler tests
# -----------------------------------------------------------------------------


class TestAddMouseHandler:
    """Test Mouse.add_mouse_handler method."""

    def test_add_handler_at_coordinates(self):
        """Add handler at specific coordinates."""
        handler = MagicMock()

        Mouse.add_mouse_handler(handler, y=5, x=10, ncols=5)

        assert 5 in Mouse._yxhandlers_by_row
        h = Mouse._yxhandlers_by_row[5][0]
        assert h.func is handler
        assert h.begin_x == 10
        assert h.last_x == 14  # x + ncols - 1 = 10 + 5 - 1

    def test_add_handler_with_args(self):
        """Add handler with additional args."""
        handler = MagicMock()
        args = "my_args"

        Mouse.add_mouse_handler(handler, y=3, x=0, ncols=10, args=args)

        h = Mouse._yxhandlers_by_row[3][0]
        assert h.args == args

    def test_add_multiple_handlers_same_row(self):
        """Add multiple handlers on same row."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        Mouse.add_mouse_handler(handler1, y=5, x=0, ncols=10)
        Mouse.add_mouse_handler(handler2, y=5, x=20, ncols=10)

        assert len(Mouse._yxhandlers_by_row[5]) == 2

    def test_add_handlers_different_rows(self):
        """Add handlers on different rows."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        Mouse.add_mouse_handler(handler1, y=1, x=0, ncols=10)
        Mouse.add_mouse_handler(handler2, y=5, x=0, ncols=10)

        assert 1 in Mouse._yxhandlers_by_row
        assert 5 in Mouse._yxhandlers_by_row

    def test_module_level_add_mouse_handler(self):
        """Test module-level add_mouse_handler function."""
        handler = MagicMock()

        add_mouse_handler(handler, y=7, x=5, ncols=3)

        assert 7 in Mouse._yxhandlers_by_row
        h = Mouse._yxhandlers_by_row[7][0]
        assert h.func is handler


# -----------------------------------------------------------------------------
# clear_mouse_handlers tests
# -----------------------------------------------------------------------------


class TestClearMouseHandlers:
    """Test Mouse.clear_mouse_handlers method."""

    def test_clear_removes_all_handlers(self):
        """clear_mouse_handlers removes all registered handlers."""
        handler = MagicMock()
        Mouse.add_mouse_handler(handler, y=1, x=0, ncols=10)
        Mouse.add_mouse_handler(handler, y=2, x=0, ncols=10)
        Mouse.add_mouse_handler(handler, y=3, x=0, ncols=10)

        assert len(Mouse._yxhandlers_by_row) == 3

        Mouse.clear_mouse_handlers()

        assert len(Mouse._yxhandlers_by_row) == 0

    def test_clear_on_empty_is_safe(self):
        """Clearing when already empty is safe."""
        Mouse.clear_mouse_handlers()
        Mouse.clear_mouse_handlers()  # Should not raise

        assert len(Mouse._yxhandlers_by_row) == 0

    def test_module_level_clear_mouse_handlers(self):
        """Test module-level clear_mouse_handlers function."""
        handler = MagicMock()
        Mouse.add_mouse_handler(handler, y=1, x=0, ncols=10)

        clear_mouse_handlers()

        assert len(Mouse._yxhandlers_by_row) == 0


# -----------------------------------------------------------------------------
# handle_mouse_event tests
# -----------------------------------------------------------------------------


class TestHandleMouseEvent:
    """Test Mouse.handle_mouse_event method."""

    def make_mock_mouse_event(self, x=0, y=0):
        """Create a mock MouseEvent."""
        mock_event = MagicMock()
        mock_event.x = x
        mock_event.y = y
        return mock_event

    def test_no_handlers_returns_false(self):
        """Returns False when no handlers registered."""
        mock_event = self.make_mock_mouse_event()

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        assert result is False

    def test_internal_handler_called(self):
        """Internal handler is called with event and args."""
        mock_event = self.make_mock_mouse_event()
        handler = MagicMock(return_value=True)
        args = "test_args"

        Mouse.add_internal_mouse_handler(handler, args)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_called_once_with(mock_event, args)
        assert result is True

    def test_internal_handler_returns_false_continues(self):
        """If internal handler returns False, continues to next."""
        mock_event = self.make_mock_mouse_event()
        handler1 = MagicMock(return_value=False)
        handler2 = MagicMock(return_value=True)

        Mouse.add_internal_mouse_handler(handler1)
        Mouse.add_internal_mouse_handler(handler2)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler1.assert_called_once()
        handler2.assert_called_once()
        assert result is True

    def test_internal_handler_stops_on_true(self):
        """Stops checking handlers after one returns True."""
        mock_event = self.make_mock_mouse_event()
        handler1 = MagicMock(return_value=True)
        handler2 = MagicMock(return_value=True)

        Mouse.add_internal_mouse_handler(handler1)
        Mouse.add_internal_mouse_handler(handler2)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler1.assert_called_once()
        handler2.assert_not_called()
        assert result is True

    def test_yx_handler_called_at_coordinates(self):
        """Handler at coordinates is called when mouse is in range."""
        mock_event = self.make_mock_mouse_event(x=15, y=5)
        handler = MagicMock(return_value=True)

        # Handler covers x=10 to x=19 on row 5
        Mouse.add_mouse_handler(handler, y=5, x=10, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_called_once_with(mock_event, None)
        assert result is True

    def test_yx_handler_with_args(self):
        """Handler receives its registered args."""
        mock_event = self.make_mock_mouse_event(x=5, y=3)
        handler = MagicMock(return_value=True)
        args = {"button": "submit"}

        Mouse.add_mouse_handler(handler, y=3, x=0, ncols=10, args=args)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            Mouse.handle_mouse_event()

        handler.assert_called_once_with(mock_event, args)

    def test_yx_handler_not_called_wrong_row(self):
        """Handler not called when mouse is on different row."""
        mock_event = self.make_mock_mouse_event(x=5, y=10)
        handler = MagicMock(return_value=True)

        Mouse.add_mouse_handler(handler, y=5, x=0, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_not_called()
        assert result is False

    def test_yx_handler_not_called_x_too_low(self):
        """Handler not called when x is below range."""
        mock_event = self.make_mock_mouse_event(x=5, y=3)
        handler = MagicMock(return_value=True)

        # Handler covers x=10 to x=19
        Mouse.add_mouse_handler(handler, y=3, x=10, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_not_called()
        assert result is False

    def test_yx_handler_not_called_x_too_high(self):
        """Handler not called when x is above range."""
        mock_event = self.make_mock_mouse_event(x=25, y=3)
        handler = MagicMock(return_value=True)

        # Handler covers x=10 to x=19
        Mouse.add_mouse_handler(handler, y=3, x=10, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_not_called()
        assert result is False

    def test_yx_handler_at_begin_x(self):
        """Handler called when x equals begin_x."""
        mock_event = self.make_mock_mouse_event(x=10, y=3)
        handler = MagicMock(return_value=True)

        Mouse.add_mouse_handler(handler, y=3, x=10, ncols=5)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_called_once()
        assert result is True

    def test_yx_handler_at_last_x(self):
        """Handler called when x equals last_x."""
        mock_event = self.make_mock_mouse_event(x=14, y=3)
        handler = MagicMock(return_value=True)

        # last_x = 10 + 5 - 1 = 14
        Mouse.add_mouse_handler(handler, y=3, x=10, ncols=5)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler.assert_called_once()
        assert result is True

    def test_internal_handlers_checked_before_yx(self):
        """Internal handlers are checked before coordinate handlers."""
        mock_event = self.make_mock_mouse_event(x=5, y=3)
        internal_handler = MagicMock(return_value=True)
        yx_handler = MagicMock(return_value=True)

        Mouse.add_internal_mouse_handler(internal_handler)
        Mouse.add_mouse_handler(yx_handler, y=3, x=0, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        internal_handler.assert_called_once()
        yx_handler.assert_not_called()
        assert result is True

    def test_yx_handlers_checked_if_internal_returns_false(self):
        """Coordinate handlers checked if internal handlers return False."""
        mock_event = self.make_mock_mouse_event(x=5, y=3)
        internal_handler = MagicMock(return_value=False)
        yx_handler = MagicMock(return_value=True)

        Mouse.add_internal_mouse_handler(internal_handler)
        Mouse.add_mouse_handler(yx_handler, y=3, x=0, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        internal_handler.assert_called_once()
        yx_handler.assert_called_once()
        assert result is True

    def test_multiple_yx_handlers_same_row(self):
        """First matching handler on row that returns True wins."""
        mock_event = self.make_mock_mouse_event(x=5, y=3)
        handler1 = MagicMock(return_value=False)  # x=0-9, returns False
        handler2 = MagicMock(return_value=True)  # x=0-9, returns True

        Mouse.add_mouse_handler(handler1, y=3, x=0, ncols=10)
        Mouse.add_mouse_handler(handler2, y=3, x=0, ncols=10)

        with patch("libcurses.mouse.MouseEvent", return_value=mock_event):
            result = Mouse.handle_mouse_event()

        handler1.assert_called_once()
        handler2.assert_called_once()
        assert result is True

    def test_logs_trace_message(self):
        """handle_mouse_event logs trace with event repr."""
        mock_event = self.make_mock_mouse_event()

        with (
            patch("libcurses.mouse.MouseEvent", return_value=mock_event),
            patch("libcurses.mouse.logger") as mock_logger,
        ):
            Mouse.handle_mouse_event()

        mock_logger.trace.assert_called_once()
