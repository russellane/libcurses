"""Tests for MouseEvent class."""

import curses
from unittest.mock import patch

import pytest

from libcurses.mouseevent import MouseEvent


@pytest.fixture(autouse=True)
def reset_last_mouse():
    """Reset the class-level _last_mouse before each test."""
    MouseEvent._last_mouse = None
    yield
    MouseEvent._last_mouse = None


def make_event(x: int, y: int, bstate: int) -> MouseEvent:
    """Create a MouseEvent with mocked curses.getmouse."""
    with patch("curses.getmouse", return_value=(0, x, y, 0, bstate)):
        return MouseEvent()


# -----------------------------------------------------------------------------
# Button detection tests
# -----------------------------------------------------------------------------


class TestButtonDetection:
    """Test button number detection (1-5)."""

    def test_button1_pressed(self):
        event = make_event(10, 5, curses.BUTTON1_PRESSED)
        assert event.button == 1

    def test_button1_clicked(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert event.button == 1

    def test_button1_released(self):
        event = make_event(10, 5, curses.BUTTON1_RELEASED)
        assert event.button == 1

    def test_button2_pressed(self):
        event = make_event(10, 5, curses.BUTTON2_PRESSED)
        assert event.button == 2

    def test_button2_clicked(self):
        event = make_event(10, 5, curses.BUTTON2_CLICKED)
        assert event.button == 2

    def test_button2_released(self):
        event = make_event(10, 5, curses.BUTTON2_RELEASED)
        assert event.button == 2

    def test_button3_pressed(self):
        event = make_event(10, 5, curses.BUTTON3_PRESSED)
        assert event.button == 3

    def test_button3_clicked(self):
        event = make_event(10, 5, curses.BUTTON3_CLICKED)
        assert event.button == 3

    def test_button3_released(self):
        event = make_event(10, 5, curses.BUTTON3_RELEASED)
        assert event.button == 3

    def test_button4_pressed(self):
        event = make_event(10, 5, curses.BUTTON4_PRESSED)
        assert event.button == 4

    def test_button4_clicked(self):
        event = make_event(10, 5, curses.BUTTON4_CLICKED)
        assert event.button == 4

    def test_button5_fallback(self):
        """Button 5 is the fallback when no other button matches."""
        # Use a bstate that doesn't match buttons 1-4
        # BUTTON5 constants may not exist, so test the fallback
        event = make_event(10, 5, 0)
        assert event.button == 5


# -----------------------------------------------------------------------------
# Click count tests
# -----------------------------------------------------------------------------


class TestClickCount:
    """Test click count detection (1-3)."""

    def test_single_click_button1(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert event.nclicks == 1

    def test_double_click_button1(self):
        event = make_event(10, 5, curses.BUTTON1_DOUBLE_CLICKED)
        assert event.nclicks == 2

    def test_triple_click_button1(self):
        event = make_event(10, 5, curses.BUTTON1_TRIPLE_CLICKED)
        assert event.nclicks == 3

    def test_single_click_button2(self):
        event = make_event(10, 5, curses.BUTTON2_CLICKED)
        assert event.nclicks == 1

    def test_double_click_button2(self):
        event = make_event(10, 5, curses.BUTTON2_DOUBLE_CLICKED)
        assert event.nclicks == 2

    def test_triple_click_button2(self):
        event = make_event(10, 5, curses.BUTTON2_TRIPLE_CLICKED)
        assert event.nclicks == 3

    def test_single_click_button3(self):
        event = make_event(10, 5, curses.BUTTON3_CLICKED)
        assert event.nclicks == 1

    def test_double_click_button3(self):
        event = make_event(10, 5, curses.BUTTON3_DOUBLE_CLICKED)
        assert event.nclicks == 2

    def test_triple_click_button3(self):
        event = make_event(10, 5, curses.BUTTON3_TRIPLE_CLICKED)
        assert event.nclicks == 3

    def test_pressed_has_zero_clicks(self):
        event = make_event(10, 5, curses.BUTTON1_PRESSED)
        assert event.nclicks == 0

    def test_released_has_zero_clicks(self):
        event = make_event(10, 5, curses.BUTTON1_RELEASED)
        assert event.nclicks == 0


# -----------------------------------------------------------------------------
# Pressed/Released state tests
# -----------------------------------------------------------------------------


class TestPressedReleased:
    """Test pressed and released state detection."""

    def test_button1_pressed_state(self):
        event = make_event(10, 5, curses.BUTTON1_PRESSED)
        assert event.is_pressed is True
        assert event.is_released is False

    def test_button1_released_state(self):
        event = make_event(10, 5, curses.BUTTON1_RELEASED)
        assert event.is_pressed is False
        assert event.is_released is True

    def test_button2_pressed_state(self):
        event = make_event(10, 5, curses.BUTTON2_PRESSED)
        assert event.is_pressed is True
        assert event.is_released is False

    def test_button2_released_state(self):
        event = make_event(10, 5, curses.BUTTON2_RELEASED)
        assert event.is_pressed is False
        assert event.is_released is True

    def test_button3_pressed_state(self):
        event = make_event(10, 5, curses.BUTTON3_PRESSED)
        assert event.is_pressed is True
        assert event.is_released is False

    def test_button3_released_state(self):
        event = make_event(10, 5, curses.BUTTON3_RELEASED)
        assert event.is_pressed is False
        assert event.is_released is True

    def test_clicked_not_pressed_or_released(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert event.is_pressed is False
        assert event.is_released is False


# -----------------------------------------------------------------------------
# Modifier key tests
# -----------------------------------------------------------------------------


class TestModifierKeys:
    """Test modifier key detection (Alt, Ctrl, Shift)."""

    def test_alt_modifier(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_ALT)
        assert event.is_alt is True
        assert event.is_ctrl is False
        assert event.is_shift is False

    def test_ctrl_modifier(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_CTRL)
        assert event.is_alt is False
        assert event.is_ctrl is True
        assert event.is_shift is False

    def test_shift_modifier(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_SHIFT)
        assert event.is_alt is False
        assert event.is_ctrl is False
        assert event.is_shift is True

    def test_multiple_modifiers(self):
        event = make_event(
            10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_ALT | curses.BUTTON_CTRL
        )
        assert event.is_alt is True
        assert event.is_ctrl is True
        assert event.is_shift is False

    def test_all_modifiers(self):
        event = make_event(
            10,
            5,
            curses.BUTTON1_CLICKED
            | curses.BUTTON_ALT
            | curses.BUTTON_CTRL
            | curses.BUTTON_SHIFT,
        )
        assert event.is_alt is True
        assert event.is_ctrl is True
        assert event.is_shift is True

    def test_no_modifiers(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert event.is_alt is False
        assert event.is_ctrl is False
        assert event.is_shift is False


# -----------------------------------------------------------------------------
# Mouse movement tests
# -----------------------------------------------------------------------------


class TestMouseMovement:
    """Test mouse movement detection."""

    def test_report_mouse_position_sets_is_moving(self):
        event = make_event(10, 5, curses.REPORT_MOUSE_POSITION)
        assert event.is_moving is True

    def test_click_not_moving(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert event.is_moving is False

    def test_movement_with_last_mouse_inherits_state(self):
        """When moving, inherit button/modifiers from last mouse event."""
        # First event: press button 1 with shift
        first = make_event(10, 5, curses.BUTTON1_PRESSED | curses.BUTTON_SHIFT)
        assert first.button == 1
        assert first.is_shift is True

        # Second event: mouse movement (should inherit from first)
        second = make_event(15, 8, curses.REPORT_MOUSE_POSITION)
        assert second.is_moving is True
        assert second.button == 1  # inherited
        assert second.is_shift is True  # inherited
        assert second.is_pressed is True  # set by movement logic
        assert second.is_released is False

    def test_movement_without_last_mouse(self):
        """Movement without prior event doesn't crash."""
        MouseEvent._last_mouse = None
        event = make_event(10, 5, curses.REPORT_MOUSE_POSITION)
        assert event.is_moving is True
        # Without last_mouse, falls through to normal detection
        assert event.button == 5  # fallback


# -----------------------------------------------------------------------------
# Coordinate tests
# -----------------------------------------------------------------------------


class TestCoordinates:
    """Test x, y coordinate capture."""

    def test_coordinates_captured(self):
        event = make_event(42, 17, curses.BUTTON1_CLICKED)
        assert event.x == 42
        assert event.y == 17

    def test_zero_coordinates(self):
        event = make_event(0, 0, curses.BUTTON1_CLICKED)
        assert event.x == 0
        assert event.y == 0


# -----------------------------------------------------------------------------
# String representation tests
# -----------------------------------------------------------------------------


class TestStringRepresentation:
    """Test __str__ and __repr__ methods."""

    def test_str_simple_click(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert str(event) == "M1"

    def test_str_button2(self):
        event = make_event(10, 5, curses.BUTTON2_CLICKED)
        assert str(event) == "M2"

    def test_str_button3(self):
        event = make_event(10, 5, curses.BUTTON3_CLICKED)
        assert str(event) == "M3"

    def test_str_with_alt(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_ALT)
        assert str(event) == "Alt+M1"

    def test_str_with_ctrl(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_CTRL)
        assert str(event) == "Ctrl+M1"

    def test_str_with_shift(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED | curses.BUTTON_SHIFT)
        assert str(event) == "Shift+M1"

    def test_str_with_all_modifiers(self):
        event = make_event(
            10,
            5,
            curses.BUTTON1_CLICKED
            | curses.BUTTON_ALT
            | curses.BUTTON_CTRL
            | curses.BUTTON_SHIFT,
        )
        assert str(event) == "Alt+Ctrl+Shift+M1"

    def test_str_double_click(self):
        event = make_event(10, 5, curses.BUTTON1_DOUBLE_CLICKED)
        assert str(event) == "M1*2"

    def test_str_triple_click(self):
        event = make_event(10, 5, curses.BUTTON1_TRIPLE_CLICKED)
        assert str(event) == "M1*3"

    def test_str_modifier_and_double_click(self):
        event = make_event(10, 5, curses.BUTTON1_DOUBLE_CLICKED | curses.BUTTON_SHIFT)
        assert str(event) == "Shift+M1*2"

    def test_repr_contains_class_name(self):
        event = make_event(10, 5, curses.BUTTON1_CLICKED)
        assert "MouseEvent(" in repr(event)

    def test_repr_contains_coordinates(self):
        event = make_event(42, 17, curses.BUTTON1_CLICKED)
        r = repr(event)
        assert "x=42" in r
        assert "y=17" in r

    def test_repr_contains_state_info(self):
        event = make_event(10, 5, curses.BUTTON1_PRESSED)
        r = repr(event)
        assert "is_pressed=True" in r
        assert "is_released=False" in r
        assert "is_moving=False" in r


# -----------------------------------------------------------------------------
# bstate preservation test
# -----------------------------------------------------------------------------


class TestBstatePreservation:
    """Test that bstate is preserved."""

    def test_bstate_stored(self):
        bstate = curses.BUTTON1_CLICKED | curses.BUTTON_SHIFT
        event = make_event(10, 5, bstate)
        assert event.bstate == bstate
