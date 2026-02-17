"""Tests for getline function."""

import curses
import curses.ascii
from unittest.mock import MagicMock, call, patch

import pytest

from libcurses.getline import getline


@pytest.fixture
def mock_win():
    """Create mock curses window."""
    win = MagicMock()
    win.getyx.return_value = (5, 10)
    return win


@pytest.fixture(autouse=True)
def mock_is_fkey():
    """Mock is_fkey to return False by default."""
    with patch("libcurses.getline.is_fkey", return_value=False):
        yield


# -----------------------------------------------------------------------------
# Line termination tests
# -----------------------------------------------------------------------------


class TestGetlineTermination:
    """Test getline line termination."""

    def test_returns_none_on_eof(self, mock_win):
        """getline returns None when getkey returns None."""
        with patch("libcurses.getline.getkey", return_value=None):
            result = getline(mock_win)

        assert result is None

    def test_returns_none_on_zero(self, mock_win):
        """getline returns None when getkey returns 0 (falsy)."""
        with patch("libcurses.getline.getkey", return_value=0):
            result = getline(mock_win)

        assert result is None

    def test_returns_line_on_lf(self, mock_win):
        """getline returns line on LF."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("h"), ord("i"), curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "hi"

    def test_returns_line_on_cr(self, mock_win):
        """getline returns line on CR."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("h"), ord("i"), curses.ascii.CR],
        ):
            result = getline(mock_win)

        assert result == "hi"

    def test_returns_line_on_key_enter(self, mock_win):
        """getline returns line on KEY_ENTER."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("h"), ord("i"), curses.KEY_ENTER],
        ):
            result = getline(mock_win)

        assert result == "hi"

    def test_returns_empty_string_on_immediate_enter(self, mock_win):
        """getline returns empty string when Enter pressed immediately."""
        with patch("libcurses.getline.getkey", return_value=curses.ascii.LF):
            result = getline(mock_win)

        assert result == ""

    def test_clears_line_on_return(self, mock_win):
        """getline clears displayed line before returning."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("a"), ord("b"), ord("c"), curses.ascii.LF],
        ):
            getline(mock_win)

        # Should call addstr(BS) and delch() 3 times to clear "abc"
        bs_calls = [c for c in mock_win.addstr.call_args_list if chr(curses.ascii.BS) in str(c)]
        assert mock_win.delch.call_count >= 3


# -----------------------------------------------------------------------------
# Backspace handling tests
# -----------------------------------------------------------------------------


class TestGetlineBackspace:
    """Test getline backspace handling."""

    def test_backspace_deletes_last_char(self, mock_win):
        """Backspace deletes the last character."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("a"), ord("b"), curses.ascii.BS, curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "a"

    def test_backspace_on_empty_line_ignored(self, mock_win):
        """Backspace on empty line is ignored."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[curses.ascii.BS, ord("x"), curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "x"

    def test_backspace_updates_display(self, mock_win):
        """Backspace updates the display."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("a"), curses.ascii.BS, curses.ascii.LF],
        ):
            getline(mock_win)

        # Should have called addstr with BS character and delch
        assert mock_win.delch.called

    def test_multiple_backspaces(self, mock_win):
        """Multiple backspaces delete multiple characters."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[
                ord("a"),
                ord("b"),
                ord("c"),
                curses.ascii.BS,
                curses.ascii.BS,
                curses.ascii.LF,
            ],
        ):
            result = getline(mock_win)

        assert result == "a"


# -----------------------------------------------------------------------------
# Ctrl-U (NAK) handling tests
# -----------------------------------------------------------------------------


class TestGetlineCtrlU:
    """Test getline Ctrl-U (kill line) handling."""

    def test_ctrl_u_kills_line(self, mock_win):
        """Ctrl-U clears the entire line."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("a"), ord("b"), ord("c"), curses.ascii.NAK, curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == ""

    def test_ctrl_u_on_empty_line(self, mock_win):
        """Ctrl-U on empty line does nothing."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[curses.ascii.NAK, ord("x"), curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "x"

    def test_ctrl_u_updates_display(self, mock_win):
        """Ctrl-U updates the display for each character."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("a"), ord("b"), curses.ascii.NAK, curses.ascii.LF],
        ):
            getline(mock_win)

        # Should have called delch multiple times
        assert mock_win.delch.call_count >= 2

    def test_can_type_after_ctrl_u(self, mock_win):
        """Can type new content after Ctrl-U."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[
                ord("o"),
                ord("l"),
                ord("d"),
                curses.ascii.NAK,
                ord("n"),
                ord("e"),
                ord("w"),
                curses.ascii.LF,
            ],
        ):
            result = getline(mock_win)

        assert result == "new"


# -----------------------------------------------------------------------------
# Mouse handling tests
# -----------------------------------------------------------------------------


class TestGetlineMouse:
    """Test getline mouse event handling."""

    def test_handles_mouse_event(self, mock_win):
        """getline handles KEY_MOUSE by calling Mouse.handle_mouse_event."""
        with (
            patch(
                "libcurses.getline.getkey",
                side_effect=[curses.KEY_MOUSE, ord("x"), curses.ascii.LF],
            ),
            patch("libcurses.getline.Mouse.handle_mouse_event") as mock_handle,
        ):
            result = getline(mock_win)

        mock_handle.assert_called_once()
        assert result == "x"

    def test_multiple_mouse_events(self, mock_win):
        """getline handles multiple mouse events."""
        with (
            patch(
                "libcurses.getline.getkey",
                side_effect=[
                    curses.KEY_MOUSE,
                    curses.KEY_MOUSE,
                    ord("a"),
                    curses.ascii.LF,
                ],
            ),
            patch("libcurses.getline.Mouse.handle_mouse_event") as mock_handle,
        ):
            result = getline(mock_win)

        assert mock_handle.call_count == 2
        assert result == "a"


# -----------------------------------------------------------------------------
# Function key handling tests
# -----------------------------------------------------------------------------


class TestGetlineFkey:
    """Test getline function key handling."""

    def test_fkey_with_empty_line(self, mock_win, mock_is_fkey):
        """Function key with empty line doesn't redraw."""
        with (
            patch(
                "libcurses.getline.getkey",
                side_effect=[curses.KEY_F1, ord("x"), curses.ascii.LF],
            ),
            patch("libcurses.getline.is_fkey", side_effect=[True, False, False]),
        ):
            result = getline(mock_win)

        # Should not call addstr with position when line is empty
        assert result == "x"

    def test_fkey_with_content_redraws_line(self, mock_win, mock_is_fkey):
        """Function key with content redraws the line."""
        mock_win.getyx.return_value = (5, 10)

        with (
            patch(
                "libcurses.getline.getkey",
                side_effect=[ord("a"), ord("b"), curses.KEY_F1, curses.ascii.LF],
            ),
            patch("libcurses.getline.is_fkey", side_effect=[False, False, True, False]),
        ):
            result = getline(mock_win)

        # Should have called addstr(y, x, line) to redraw
        calls = mock_win.addstr.call_args_list
        redraw_calls = [c for c in calls if len(c[0]) == 3]  # (y, x, str) calls
        assert len(redraw_calls) >= 1
        assert result == "ab"


# -----------------------------------------------------------------------------
# Printable character tests
# -----------------------------------------------------------------------------


class TestGetlinePrintable:
    """Test getline printable character handling."""

    def test_printable_chars_added_to_line(self, mock_win):
        """Printable characters are added to the line."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("H"), ord("e"), ord("l"), ord("l"), ord("o"), curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "Hello"

    def test_printable_chars_displayed(self, mock_win):
        """Printable characters are displayed."""
        with patch("libcurses.getline.getkey", side_effect=[ord("X"), curses.ascii.LF]):
            getline(mock_win)

        # Should have called addstr with "X"
        calls = [c for c in mock_win.addstr.call_args_list if "X" in str(c)]
        assert len(calls) >= 1

    def test_handles_curses_error_on_addstr(self, mock_win):
        """getline handles curses.error on addstr gracefully."""
        mock_win.addstr.side_effect = [curses.error("addstr failed"), None, None]

        with (
            patch("libcurses.getline.getkey", side_effect=[ord("a"), ord("b"), curses.ascii.LF]),
            patch("libcurses.getline.logger") as mock_logger,
        ):
            result = getline(mock_win)

        mock_logger.error.assert_called()
        # Line might be partial due to error, but should still return
        assert result == "b"

    def test_spaces_allowed(self, mock_win):
        """Spaces are treated as printable."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("a"), ord(" "), ord("b"), curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "a b"

    def test_digits_allowed(self, mock_win):
        """Digits are treated as printable."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[ord("1"), ord("2"), ord("3"), curses.ascii.LF],
        ):
            result = getline(mock_win)

        assert result == "123"


# -----------------------------------------------------------------------------
# Non-printable character tests
# -----------------------------------------------------------------------------


class TestGetlineNonPrintable:
    """Test getline non-printable character handling."""

    def test_non_printable_ignored(self, mock_win):
        """Non-printable characters are ignored."""
        with (
            patch(
                "libcurses.getline.getkey",
                side_effect=[ord("a"), 1, ord("b"), curses.ascii.LF],  # 1 = Ctrl-A
            ),
            patch("libcurses.getline.is_fkey", return_value=False),
        ):
            result = getline(mock_win)

        assert result == "ab"

    def test_non_printable_logged(self, mock_win):
        """Non-printable characters are logged at trace level."""
        with (
            patch(
                "libcurses.getline.getkey",
                side_effect=[1, curses.ascii.LF],  # 1 = Ctrl-A
            ),
            patch("libcurses.getline.is_fkey", return_value=False),
            patch("libcurses.getline.logger") as mock_logger,
        ):
            getline(mock_win)

        mock_logger.trace.assert_called()


# -----------------------------------------------------------------------------
# Integration-like tests
# -----------------------------------------------------------------------------


class TestGetlineIntegration:
    """Test getline with realistic input sequences."""

    def test_type_edit_submit(self, mock_win):
        """Type, edit with backspace, then submit."""
        with patch(
            "libcurses.getline.getkey",
            side_effect=[
                ord("h"),
                ord("e"),
                ord("l"),
                ord("p"),  # "help"
                curses.ascii.BS,  # delete 'p'
                ord("l"),
                ord("o"),  # "hello"
                curses.ascii.LF,
            ],
        ):
            result = getline(mock_win)

        assert result == "hello"

    def test_calls_getkey_with_no_mouse(self, mock_win):
        """getline calls getkey with no_mouse=True."""
        with patch("libcurses.getline.getkey", return_value=curses.ascii.LF) as mock_getkey:
            getline(mock_win)

        mock_getkey.assert_called_with(mock_win, no_mouse=True)
