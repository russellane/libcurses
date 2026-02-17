"""Tests for LogSink class."""

import curses
from contextlib import contextmanager
from threading import Lock
from unittest.mock import MagicMock, call, patch

import pytest

import libcurses.core as core_module
from libcurses.logsink import LogSink


@pytest.fixture
def mock_win():
    """Create mock curses window."""
    win = MagicMock()
    win.getyx.return_value = (0, 0)
    return win


@pytest.fixture
def mock_colormap():
    """Mock get_colormap to return test colormap."""
    colormap = {
        "TRACE": 1,
        "DEBUG": 2,
        "INFO": 3,
        "WARNING": 4,
        "ERROR": 5,
        "CRITICAL": 6,
    }
    with patch("libcurses.logsink.get_colormap", return_value=colormap):
        yield colormap


@pytest.fixture
def mock_logger():
    """Mock loguru logger."""
    with patch("libcurses.logsink.logger") as mock:
        mock.add.return_value = 123  # Return fake logger ID
        yield mock


@pytest.fixture
def mock_preserve_cursor():
    """Mock preserve_cursor context manager."""

    @contextmanager
    def fake_preserve():
        yield (0, 0)

    with patch("libcurses.logsink.libcurses.core.preserve_cursor", fake_preserve):
        yield


# -----------------------------------------------------------------------------
# Initialization tests
# -----------------------------------------------------------------------------


class TestLogSinkInit:
    """Test LogSink initialization."""

    def test_sets_logwin(self, mock_win, mock_colormap, mock_logger):
        """LogSink stores the log window."""
        sink = LogSink(mock_win)

        assert sink.logwin is mock_win

    def test_default_level_is_info(self, mock_win, mock_colormap, mock_logger):
        """Default logging level is INFO."""
        sink = LogSink(mock_win)

        assert sink.level == "INFO"

    def test_default_location_format(self, mock_win, mock_colormap, mock_logger):
        """Default location format is name.function:line."""
        sink = LogSink(mock_win)

        assert sink.location == "{name}.{function}:{line}"

    def test_default_delim(self, mock_win, mock_colormap, mock_logger):
        """Default delimiter is pipe."""
        sink = LogSink(mock_win)

        assert sink.delim == "|"

    def test_initial_padding_is_zero(self, mock_win, mock_colormap, mock_logger):
        """Initial padding values are zero."""
        sink = LogSink(mock_win)

        assert sink._padlev == 0
        assert sink._padloc == 0

    def test_configures_window_scrolling(self, mock_win, mock_colormap, mock_logger):
        """LogSink configures window for scrolling."""
        LogSink(mock_win)

        mock_win.idlok.assert_called_with(True)
        mock_win.leaveok.assert_called_with(False)
        mock_win.scrollok.assert_called_with(True)

    def test_gets_colormap(self, mock_win, mock_logger):
        """LogSink gets the colormap."""
        with patch("libcurses.logsink.get_colormap") as mock_get:
            mock_get.return_value = {"INFO": 1}
            sink = LogSink(mock_win)

        mock_get.assert_called_once()
        assert sink._colormap == {"INFO": 1}

    def test_calls_config(self, mock_win, mock_colormap, mock_logger):
        """LogSink calls _config during init."""
        LogSink(mock_win)

        # _config calls logger.add
        mock_logger.add.assert_called_once()

    def test_logger_id_stored(self, mock_win, mock_colormap, mock_logger):
        """Logger ID is stored from logger.add."""
        mock_logger.add.return_value = 456
        sink = LogSink(mock_win)

        assert sink._id == 456


# -----------------------------------------------------------------------------
# reset_padding tests
# -----------------------------------------------------------------------------


class TestLogSinkResetPadding:
    """Test LogSink.reset_padding method."""

    def test_resets_padding(self, mock_win, mock_colormap, mock_logger):
        """reset_padding resets both padding values."""
        sink = LogSink(mock_win)
        sink._padloc = 20
        sink._padlev = 10

        sink.reset_padding()

        assert sink._padloc == 0
        assert sink._padlev == 0


# -----------------------------------------------------------------------------
# set_level tests
# -----------------------------------------------------------------------------


class TestLogSinkSetLevel:
    """Test LogSink.set_level method."""

    def test_sets_level(self, mock_win, mock_colormap, mock_logger):
        """set_level updates the level."""
        sink = LogSink(mock_win)

        sink.set_level("DEBUG")

        assert sink.level == "DEBUG"

    def test_calls_config(self, mock_win, mock_colormap, mock_logger):
        """set_level calls _config to reconfigure logger."""
        sink = LogSink(mock_win)
        mock_logger.reset_mock()

        sink.set_level("DEBUG")

        # Should remove old logger and add new one
        mock_logger.remove.assert_called()
        mock_logger.add.assert_called()

    def test_logs_new_level(self, mock_win, mock_colormap, mock_logger):
        """set_level logs the new level."""
        sink = LogSink(mock_win)

        sink.set_level("WARNING")

        mock_logger.info.assert_called_with("WARNING")

    def test_resets_padding(self, mock_win, mock_colormap, mock_logger):
        """set_level resets padding."""
        sink = LogSink(mock_win)
        sink._padloc = 20
        sink._padlev = 10

        sink.set_level("DEBUG")

        assert sink._padloc == 0
        assert sink._padlev == 0


# -----------------------------------------------------------------------------
# set_location tests
# -----------------------------------------------------------------------------


class TestLogSinkSetLocation:
    """Test LogSink.set_location method."""

    def test_sets_location(self, mock_win, mock_colormap, mock_logger):
        """set_location updates the location format."""
        sink = LogSink(mock_win)

        sink.set_location("{module}")

        assert sink.location == "{module}"

    def test_none_sets_empty_string(self, mock_win, mock_colormap, mock_logger):
        """set_location with None sets empty string."""
        sink = LogSink(mock_win)

        sink.set_location(None)

        assert sink.location == ""

    def test_calls_config(self, mock_win, mock_colormap, mock_logger):
        """set_location calls _config to reconfigure logger."""
        sink = LogSink(mock_win)
        mock_logger.reset_mock()

        sink.set_location("{name}")

        mock_logger.remove.assert_called()
        mock_logger.add.assert_called()

    def test_logs_new_location(self, mock_win, mock_colormap, mock_logger):
        """set_location logs the new location format."""
        sink = LogSink(mock_win)

        sink.set_location("{file}")

        mock_logger.info.assert_called_with(repr("{file}"))

    def test_resets_padding(self, mock_win, mock_colormap, mock_logger):
        """set_location resets padding."""
        sink = LogSink(mock_win)
        sink._padloc = 20
        sink._padlev = 10

        sink.set_location("{name}")

        assert sink._padloc == 0
        assert sink._padlev == 0


# -----------------------------------------------------------------------------
# set_verbose tests
# -----------------------------------------------------------------------------


class TestLogSinkSetVerbose:
    """Test LogSink.set_verbose method."""

    def test_verbose_0_sets_info(self, mock_win, mock_colormap, mock_logger):
        """verbose=0 sets level to INFO."""
        sink = LogSink(mock_win)

        sink.set_verbose(0)

        assert sink.level == "INFO"

    def test_verbose_1_sets_debug(self, mock_win, mock_colormap, mock_logger):
        """verbose=1 sets level to DEBUG."""
        sink = LogSink(mock_win)

        sink.set_verbose(1)

        assert sink.level == "DEBUG"

    def test_verbose_2_sets_trace(self, mock_win, mock_colormap, mock_logger):
        """verbose=2 sets level to TRACE."""
        sink = LogSink(mock_win)

        sink.set_verbose(2)

        assert sink.level == "TRACE"

    def test_verbose_high_clamps_to_trace(self, mock_win, mock_colormap, mock_logger):
        """verbose > 2 clamps to TRACE."""
        sink = LogSink(mock_win)

        sink.set_verbose(10)

        assert sink.level == "TRACE"

    def test_returns_verbose(self, mock_win, mock_colormap, mock_logger):
        """set_verbose returns the verbose value."""
        sink = LogSink(mock_win)

        result = sink.set_verbose(1)

        assert result == 1


# -----------------------------------------------------------------------------
# _config tests
# -----------------------------------------------------------------------------


class TestLogSinkConfig:
    """Test LogSink._config method."""

    def test_adds_logger(self, mock_win, mock_colormap, mock_logger):
        """_config adds a logger with sink."""
        sink = LogSink(mock_win)

        # Called during init
        mock_logger.add.assert_called()
        call_kwargs = mock_logger.add.call_args[1]
        assert call_kwargs["level"] == "INFO"
        assert "format" in call_kwargs

    def test_removes_existing_logger(self, mock_win, mock_colormap, mock_logger):
        """_config removes existing logger before adding new one."""
        mock_logger.add.return_value = 999
        sink = LogSink(mock_win)

        # Trigger another _config call
        sink._config()

        mock_logger.remove.assert_called_with(999)

    def test_format_includes_time(self, mock_win, mock_colormap, mock_logger):
        """Logger format includes time."""
        sink = LogSink(mock_win)

        call_kwargs = mock_logger.add.call_args[1]
        assert "{time:HH:mm:ss.SSS}" in call_kwargs["format"]

    def test_format_includes_location(self, mock_win, mock_colormap, mock_logger):
        """Logger format includes location."""
        sink = LogSink(mock_win)

        call_kwargs = mock_logger.add.call_args[1]
        assert sink.location in call_kwargs["format"]

    def test_format_includes_level(self, mock_win, mock_colormap, mock_logger):
        """Logger format includes level."""
        sink = LogSink(mock_win)

        call_kwargs = mock_logger.add.call_args[1]
        assert "{level}" in call_kwargs["format"]

    def test_format_includes_message(self, mock_win, mock_colormap, mock_logger):
        """Logger format includes message and exception."""
        sink = LogSink(mock_win)

        call_kwargs = mock_logger.add.call_args[1]
        assert "{message}" in call_kwargs["format"]
        assert "{exception}" in call_kwargs["format"]


# -----------------------------------------------------------------------------
# _sink tests
# -----------------------------------------------------------------------------


class TestLogSinkSink:
    """Test LogSink._sink method."""

    def test_parses_message(self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor):
        """_sink parses the log message."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|test.func:10|INFO|Hello world")

        # Should write to window
        assert mock_win.addstr.called

    def test_uses_colormap(self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor):
        """_sink uses colormap for the level."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|test.func:10|INFO|Hello")

        # Should call addstr with INFO's color (3)
        calls = mock_win.addstr.call_args_list
        colors_used = [c[0][1] for c in calls if len(c[0]) >= 2]
        assert 3 in colors_used  # INFO color

    def test_pads_location_column(
        self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor
    ):
        """_sink pads the location column."""
        sink = LogSink(mock_win)
        sink._padloc = 0

        sink._sink("12:34:56.789|short|INFO|msg")

        assert sink._padloc == 5  # len("short")

        sink._sink("12:34:56.789|longer_loc|INFO|msg")

        assert sink._padloc == 10  # len("longer_loc")

    def test_pads_level_column(self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor):
        """_sink pads the level column."""
        sink = LogSink(mock_win)
        sink._padlev = 0

        sink._sink("12:34:56.789|loc|INFO|msg")

        assert sink._padlev == 4  # len("INFO")

        sink._sink("12:34:56.789|loc|WARNING|msg")

        assert sink._padlev == 7  # len("WARNING")

    def test_adds_newline_if_not_at_origin(
        self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor
    ):
        """_sink adds newline if cursor not at (0, 0)."""
        mock_win.getyx.return_value = (5, 10)
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|loc|INFO|msg")

        # Should call addch with newline
        calls = [c for c in mock_win.addch.call_args_list if c[0][0] == "\n"]
        assert len(calls) >= 1

    def test_no_newline_at_origin(
        self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor
    ):
        """_sink doesn't add newline if cursor at (0, 0)."""
        mock_win.getyx.return_value = (0, 0)
        sink = LogSink(mock_win)
        mock_win.reset_mock()

        sink._sink("12:34:56.789|loc|INFO|msg")

        # First addch should be delimiter, not newline
        first_addch = mock_win.addch.call_args_list[0]
        assert first_addch[0][0] != "\n"

    def test_writes_time(self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor):
        """_sink writes the time."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|loc|INFO|msg")

        calls = [str(c) for c in mock_win.addstr.call_args_list]
        assert any("12:34:56.789" in c for c in calls)

    def test_writes_location_when_present(
        self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor
    ):
        """_sink writes location when not empty."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|my_location|INFO|msg")

        calls = [str(c) for c in mock_win.addstr.call_args_list]
        assert any("my_location" in c for c in calls)

    def test_skips_location_when_empty(
        self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor
    ):
        """_sink skips location column when empty."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789||INFO|msg")

        # Count addch calls for delimiters - should be fewer without location
        delim_calls = [c for c in mock_win.addch.call_args_list if c[0][0] == "|"]
        # With location: time|loc|level|, without: time|level|
        # Actually location being empty means we don't write it
        calls = [str(c) for c in mock_win.addstr.call_args_list]
        # Empty location shouldn't appear
        assert not any(c == "call('')" for c in calls)

    def test_writes_message(self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor):
        """_sink writes the message."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|loc|INFO|Hello world!")

        calls = [str(c) for c in mock_win.addstr.call_args_list]
        assert any("Hello world!" in c for c in calls)

    def test_strips_message_trailing_whitespace(
        self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor
    ):
        """_sink strips trailing whitespace from message."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|loc|INFO|message with spaces   \n")

        calls = [str(c) for c in mock_win.addstr.call_args_list]
        # Should have stripped trailing spaces and newline
        assert any("message with spaces" in c for c in calls)
        assert not any("spaces   " in c for c in calls)

    def test_refreshes_window(self, mock_win, mock_colormap, mock_logger, mock_preserve_cursor):
        """_sink refreshes the window."""
        sink = LogSink(mock_win)

        sink._sink("12:34:56.789|loc|INFO|msg")

        mock_win.refresh.assert_called()

    def test_uses_preserve_cursor(self, mock_win, mock_colormap, mock_logger):
        """_sink uses preserve_cursor context manager."""
        preserve_called = []

        @contextmanager
        def tracking_preserve():
            preserve_called.append(True)
            yield (0, 0)

        with patch("libcurses.logsink.libcurses.core.preserve_cursor", tracking_preserve):
            sink = LogSink(mock_win)
            sink._sink("12:34:56.789|loc|INFO|msg")

        assert len(preserve_called) >= 1
