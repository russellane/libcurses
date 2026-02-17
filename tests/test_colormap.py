"""Tests for colormap module."""

import curses
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import libcurses.colormap as colormap_module
from libcurses.colormap import get_colormap


@pytest.fixture(autouse=True)
def reset_colormap():
    """Reset the module-level _COLORMAP cache before each test."""
    colormap_module._COLORMAP = {}
    yield
    colormap_module._COLORMAP = {}


def make_level(name: str, color: str) -> SimpleNamespace:
    """Create a mock loguru level."""
    return SimpleNamespace(name=name, color=color)


# -----------------------------------------------------------------------------
# Foreground color tests (lowercase)
# -----------------------------------------------------------------------------


class TestForegroundColors:
    """Test lowercase color names map to foreground."""

    @pytest.fixture
    def mock_curses(self):
        """Mock curses color functions."""
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", side_effect=lambda x: x * 256) as color_pair,
        ):
            yield {"init_pair": init_pair, "color_pair": color_pair}

    def test_red_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "red")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(1, curses.COLOR_RED, curses.COLOR_BLACK)
        assert "TEST" in result

    def test_green_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "green")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_GREEN, curses.COLOR_BLACK
        )
        assert "TEST" in result

    def test_blue_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "blue")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_BLUE, curses.COLOR_BLACK
        )
        assert "TEST" in result

    def test_cyan_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "cyan")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_CYAN, curses.COLOR_BLACK
        )

    def test_magenta_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "magenta")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_MAGENTA, curses.COLOR_BLACK
        )

    def test_yellow_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "yellow")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_YELLOW, curses.COLOR_BLACK
        )

    def test_white_foreground(self, mock_curses):
        levels = {"TEST": make_level("TEST", "white")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_WHITE, curses.COLOR_BLACK
        )

    def test_black_foreground(self, mock_curses):
        """Note: 'black' as fg doesn't work due to COLOR_BLACK=0 being falsy."""
        levels = {"TEST": make_level("TEST", "black")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        # COLOR_BLACK is 0, which is falsy, so walrus operator skips it
        # and default (white) is used instead
        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_WHITE, curses.COLOR_BLACK
        )


# -----------------------------------------------------------------------------
# Background color tests (UPPERCASE)
# -----------------------------------------------------------------------------


class TestBackgroundColors:
    """Test uppercase color names map to background."""

    @pytest.fixture
    def mock_curses(self):
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", side_effect=lambda x: x * 256),
        ):
            yield {"init_pair": init_pair}

    def test_red_background(self, mock_curses):
        levels = {"TEST": make_level("TEST", "RED")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(1, curses.COLOR_WHITE, curses.COLOR_RED)

    def test_green_background(self, mock_curses):
        levels = {"TEST": make_level("TEST", "GREEN")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_WHITE, curses.COLOR_GREEN
        )

    def test_blue_background(self, mock_curses):
        levels = {"TEST": make_level("TEST", "BLUE")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_WHITE, curses.COLOR_BLUE
        )

    def test_white_background(self, mock_curses):
        levels = {"TEST": make_level("TEST", "WHITE")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_WHITE, curses.COLOR_WHITE
        )


# -----------------------------------------------------------------------------
# Combined foreground and background
# -----------------------------------------------------------------------------


class TestCombinedColors:
    """Test combined foreground and background colors."""

    @pytest.fixture
    def mock_curses(self):
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", side_effect=lambda x: x * 256),
        ):
            yield {"init_pair": init_pair}

    def test_red_on_white(self, mock_curses):
        levels = {"TEST": make_level("TEST", "red WHITE")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(1, curses.COLOR_RED, curses.COLOR_WHITE)

    def test_blue_on_yellow(self, mock_curses):
        levels = {"TEST": make_level("TEST", "blue YELLOW")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_BLUE, curses.COLOR_YELLOW
        )

    def test_angle_bracket_format(self, mock_curses):
        """Test parsing format like '<blue><WHITE>'."""
        levels = {"TEST": make_level("TEST", "<green><RED>")}
        with patch("loguru.logger._core.levels", levels):
            get_colormap()

        mock_curses["init_pair"].assert_called_once_with(1, curses.COLOR_GREEN, curses.COLOR_RED)


# -----------------------------------------------------------------------------
# Attribute tests
# -----------------------------------------------------------------------------


class TestAttributes:
    """Test attribute parsing (bold, dim, italic, etc.)."""

    @pytest.fixture
    def mock_curses(self):
        with (
            patch.object(curses, "init_pair"),
            patch.object(curses, "color_pair", return_value=0),
        ):
            yield

    def test_bold_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "bold")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_BOLD

    def test_dim_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "dim")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_DIM

    def test_italic_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "italic")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_ITALIC

    def test_underline_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "underline")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_UNDERLINE

    def test_reverse_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "reverse")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_REVERSE

    def test_blink_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "blink")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_BLINK

    def test_hide_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "hide")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_INVIS

    def test_normal_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "normal")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        # A_NORMAL is 0, so we check the color pair is set but no other attrs
        assert result["TEST"] == 0  # color_pair returns 0 in mock

    def test_strike_attribute(self, mock_curses):
        levels = {"TEST": make_level("TEST", "strike")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_HORIZONTAL


# -----------------------------------------------------------------------------
# Combined colors and attributes
# -----------------------------------------------------------------------------


class TestCombinedColorsAndAttributes:
    """Test combined color and attribute specifications."""

    @pytest.fixture
    def mock_curses(self):
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", return_value=256),
        ):
            yield {"init_pair": init_pair}

    def test_red_bold(self, mock_curses):
        levels = {"TEST": make_level("TEST", "red bold")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(1, curses.COLOR_RED, curses.COLOR_BLACK)
        assert result["TEST"] & curses.A_BOLD

    def test_green_reverse(self, mock_curses):
        levels = {"TEST": make_level("TEST", "green, reverse")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_GREEN, curses.COLOR_BLACK
        )
        assert result["TEST"] & curses.A_REVERSE

    def test_blue_italic_white_bg(self, mock_curses):
        levels = {"TEST": make_level("TEST", "<blue><italic><WHITE>")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        mock_curses["init_pair"].assert_called_once_with(
            1, curses.COLOR_BLUE, curses.COLOR_WHITE
        )
        assert result["TEST"] & curses.A_ITALIC

    def test_multiple_attributes(self, mock_curses):
        levels = {"TEST": make_level("TEST", "bold underline")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert result["TEST"] & curses.A_BOLD
        assert result["TEST"] & curses.A_UNDERLINE


# -----------------------------------------------------------------------------
# Multiple levels
# -----------------------------------------------------------------------------


class TestMultipleLevels:
    """Test handling multiple log levels."""

    @pytest.fixture
    def mock_curses(self):
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", side_effect=lambda x: x * 256),
        ):
            yield {"init_pair": init_pair}

    def test_multiple_levels(self, mock_curses):
        levels = {
            "DEBUG": make_level("DEBUG", "blue"),
            "INFO": make_level("INFO", "green"),
            "WARNING": make_level("WARNING", "yellow"),
        }
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert len(result) == 3
        assert "DEBUG" in result
        assert "INFO" in result
        assert "WARNING" in result
        assert mock_curses["init_pair"].call_count == 3


# -----------------------------------------------------------------------------
# Caching behavior
# -----------------------------------------------------------------------------


class TestCaching:
    """Test that colormap is cached."""

    def test_second_call_returns_cached(self):
        """Second call should return same cached dict."""
        levels = {"TEST": make_level("TEST", "red")}
        with (
            patch.object(curses, "init_pair"),
            patch.object(curses, "color_pair", return_value=256),
            patch("loguru.logger._core.levels", levels),
        ):
            result1 = get_colormap()
            result2 = get_colormap()

        assert result1 is result2

    def test_init_pair_called_only_once(self):
        """init_pair should only be called on first invocation."""
        levels = {"TEST": make_level("TEST", "red")}
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", return_value=256),
            patch("loguru.logger._core.levels", levels),
        ):
            get_colormap()
            get_colormap()
            get_colormap()

        assert init_pair.call_count == 1


# -----------------------------------------------------------------------------
# Edge cases
# -----------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def mock_curses(self):
        with (
            patch.object(curses, "init_pair"),
            patch.object(curses, "color_pair", return_value=0),
        ):
            yield

    def test_empty_color_string(self, mock_curses):
        """Empty color string should use defaults (white on black)."""
        levels = {"TEST": make_level("TEST", "")}
        with patch("loguru.logger._core.levels", levels):
            result = get_colormap()

        assert "TEST" in result

    def test_unknown_word_ignored(self, mock_curses):
        """Unknown words in color string should be ignored."""
        levels = {"TEST": make_level("TEST", "red foobar bold")}
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", return_value=0),
            patch("loguru.logger._core.levels", levels),
        ):
            result = get_colormap()

        # Should still parse red and bold, ignore foobar
        init_pair.assert_called_once_with(1, curses.COLOR_RED, curses.COLOR_BLACK)
        assert result["TEST"] & curses.A_BOLD

    def test_no_levels(self, mock_curses):
        """Empty levels dict should return empty colormap."""
        with patch("loguru.logger._core.levels", {}):
            result = get_colormap()

        assert result == {}

    def test_mixed_case_ignored(self, mock_curses):
        """Mixed case words (not all upper or lower) should be ignored."""
        levels = {"TEST": make_level("TEST", "Red")}  # Mixed case
        with (
            patch.object(curses, "init_pair") as init_pair,
            patch.object(curses, "color_pair", return_value=0),
            patch("loguru.logger._core.levels", levels),
        ):
            get_colormap()

        # "Red" is neither all lower nor all upper, so defaults apply
        init_pair.assert_called_once_with(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
