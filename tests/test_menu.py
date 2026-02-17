"""Tests for Menu and MenuItem classes."""

import curses
from unittest.mock import MagicMock, patch

import pytest

from libcurses.menu import Menu, MenuItem

# -----------------------------------------------------------------------------
# Helper to mock curses.keyname
# -----------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_keyname():
    """Mock curses.keyname for all tests."""

    def fake_keyname(key):
        """Return mock keyname bytes."""
        if key == curses.KEY_F1:
            return b"KEY_F(1)"
        if key == curses.KEY_MOUSE:
            return b"KEY_MOUSE"
        # For regular characters, return the character
        if 32 <= key <= 126:
            return bytes([key])
        return f"KEY_{key}".encode()

    with patch("curses.keyname", side_effect=fake_keyname):
        yield


# -----------------------------------------------------------------------------
# MenuItem tests
# -----------------------------------------------------------------------------


class TestMenuItem:
    """Test MenuItem dataclass."""

    def test_create_with_string_key(self):
        """String key is converted to int via ord()."""
        item = MenuItem(key="a", text="Option A")

        assert item.key == ord("a")
        assert item.text == "Option A"

    def test_create_with_int_key(self):
        """Int key is kept as-is."""
        item = MenuItem(key=65, text="Option A")

        assert item.key == 65

    def test_keyname_set_from_key(self):
        """keyname is set via curses.keyname."""
        item = MenuItem(key="x", text="Exit")

        assert item.keyname == "x"

    def test_keyname_for_special_key(self):
        """keyname works for special keys."""
        item = MenuItem(key=curses.KEY_F1, text="Help")

        assert item.keyname == "KEY_F(1)"

    def test_payload_default_none(self):
        """payload defaults to None."""
        item = MenuItem(key="a", text="Option A")

        assert item.payload is None

    def test_payload_custom_value(self):
        """payload can be set to custom value."""
        data = {"action": "save", "file": "test.txt"}
        item = MenuItem(key="s", text="Save", payload=data)

        assert item.payload == data

    def test_repr_excludes_payload(self):
        """payload is excluded from repr."""
        item = MenuItem(key="a", text="Test", payload="secret")

        assert "secret" not in repr(item)
        assert "payload" not in repr(item)


# -----------------------------------------------------------------------------
# Menu tests
# -----------------------------------------------------------------------------


class TestMenuInit:
    """Test Menu initialization."""

    def test_create_menu(self):
        """Create menu with title and instructions."""
        menu = Menu(title="Main Menu", instructions="Select option")

        assert menu.title == "Main Menu"
        assert menu.instructions == "Select option"
        assert menu.subtitle is None
        assert menu.win is None
        assert menu.menuitems == {}
        assert menu.max_len_keyname == 0

    def test_create_menu_with_subtitle(self):
        """Create menu with subtitle."""
        menu = Menu(title="Main", instructions="Choose", subtitle="v1.0")

        assert menu.subtitle == "v1.0"

    def test_create_menu_with_window(self):
        """Create menu with window."""
        mock_win = MagicMock()
        menu = Menu(title="Main", instructions="Choose", win=mock_win)

        assert menu.win is mock_win


class TestMenuAddItem:
    """Test Menu.add_item method."""

    def test_add_single_item(self):
        """Add single item to menu."""
        menu = Menu(title="Test", instructions="Choose")

        menu.add_item("a", "Option A")

        assert "a" in menu.menuitems
        assert menu.menuitems["a"].text == "Option A"

    def test_add_item_with_payload(self):
        """Add item with payload."""
        menu = Menu(title="Test", instructions="Choose")

        menu.add_item("s", "Save", payload={"file": "data.txt"})

        assert menu.menuitems["s"].payload == {"file": "data.txt"}

    def test_add_multiple_items(self):
        """Add multiple items."""
        menu = Menu(title="Test", instructions="Choose")

        menu.add_item("a", "Option A")
        menu.add_item("b", "Option B")
        menu.add_item("c", "Option C")

        assert len(menu.menuitems) == 3

    def test_max_len_keyname_updated(self):
        """max_len_keyname tracks longest keyname."""
        menu = Menu(title="Test", instructions="Choose")

        menu.add_item("a", "Short key")  # keyname = "a", len = 1
        assert menu.max_len_keyname == 1

        menu.add_item(curses.KEY_F1, "Function key")  # keyname = "KEY_F(1)", len = 8
        assert menu.max_len_keyname == 8

    def test_add_item_with_int_key(self):
        """Add item with int key."""
        menu = Menu(title="Test", instructions="Choose")

        menu.add_item(ord("x"), "Exit")

        assert "x" in menu.menuitems


class TestMenuHooks:
    """Test Menu hook methods."""

    def test_premenu_default_does_nothing(self):
        """Default premenu does nothing."""
        menu = Menu(title="Test", instructions="Choose")

        # Should not raise
        menu.premenu()

    def test_preprompt_default_does_nothing(self):
        """Default preprompt does nothing."""
        menu = Menu(title="Test", instructions="Choose")

        # Should not raise
        menu.preprompt()

    def test_premenu_can_be_overridden(self):
        """premenu can be overridden in subclass."""
        called = []

        class CustomMenu(Menu):
            def premenu(self):
                called.append("premenu")

        menu = CustomMenu(title="Test", instructions="Choose")
        menu.premenu()

        assert called == ["premenu"]

    def test_preprompt_can_be_overridden(self):
        """preprompt can be overridden in subclass."""
        called = []

        class CustomMenu(Menu):
            def preprompt(self):
                called.append("preprompt")

        menu = CustomMenu(title="Test", instructions="Choose")
        menu.preprompt()

        assert called == ["preprompt"]


class TestMenuPrompt:
    """Test Menu.prompt method."""

    @pytest.fixture
    def mock_win(self):
        """Create mock curses window."""
        win = MagicMock()
        return win

    @pytest.fixture
    def menu_with_items(self, mock_win):
        """Create menu with items and window."""
        menu = Menu(title="Test Menu", instructions="Select", win=mock_win)
        menu.add_item("a", "Option A", payload="payload_a")
        menu.add_item("b", "Option B", payload="payload_b")
        return menu

    def test_prompt_returns_selected_item(self, menu_with_items):
        """prompt returns MenuItem when valid key pressed."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            result = menu_with_items.prompt()

        assert result is not None
        assert result.keyname == "a"
        assert result.payload == "payload_a"

    def test_prompt_returns_none_on_eof(self, menu_with_items):
        """prompt returns None when getkey returns None/0."""
        with patch("libcurses.menu.getkey", return_value=None):
            result = menu_with_items.prompt()

        assert result is None

    def test_prompt_enables_keypad(self, menu_with_items):
        """prompt enables keypad mode on window."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        menu_with_items.win.keypad.assert_called_with(True)

    def test_prompt_clears_window(self, menu_with_items):
        """prompt clears window at start of loop."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        menu_with_items.win.clear.assert_called()

    def test_prompt_displays_title(self, menu_with_items):
        """prompt displays title."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        calls = menu_with_items.win.addstr.call_args_list
        assert any("Test Menu" in str(c) for c in calls)

    def test_prompt_displays_subtitle(self, mock_win):
        """prompt displays subtitle when set."""
        menu = Menu(title="Main", instructions="Choose", subtitle="Version 1.0", win=mock_win)
        menu.add_item("q", "Quit")

        with (
            patch("libcurses.menu.getkey", return_value=ord("q")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu.prompt()

        calls = mock_win.addstr.call_args_list
        assert any("Version 1.0" in str(c) for c in calls)

    def test_prompt_displays_menu_items(self, menu_with_items):
        """prompt displays menu items."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        calls = menu_with_items.win.addstr.call_args_list
        call_strs = [str(c) for c in calls]
        assert any("Option A" in s for s in call_strs)
        assert any("Option B" in s for s in call_strs)

    def test_prompt_displays_instructions(self, menu_with_items):
        """prompt displays instructions."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        calls = menu_with_items.win.addstr.call_args_list
        assert any("Select" in str(c) for c in calls)

    def test_prompt_handles_mouse_event(self, menu_with_items):
        """prompt handles KEY_MOUSE by calling Mouse.handle_mouse_event."""
        # First return KEY_MOUSE, then valid key
        with (
            patch("libcurses.menu.getkey", side_effect=[curses.KEY_MOUSE, ord("a")]),
            patch("libcurses.menu.Mouse.handle_mouse_event") as mock_handle,
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            result = menu_with_items.prompt()

        mock_handle.assert_called_once()
        assert result.keyname == "a"

    def test_prompt_handles_fkey(self, menu_with_items):
        """prompt handles registered function keys."""
        # First return F1 (handled as fkey), then valid key
        with (
            patch("libcurses.menu.getkey", side_effect=[curses.KEY_F1, ord("a")]),
            patch("libcurses.menu.is_fkey", side_effect=[True, False]),
        ):
            result = menu_with_items.prompt()

        assert result.keyname == "a"

    def test_prompt_logs_invalid_key(self, menu_with_items):
        """prompt logs error for invalid key."""
        # First return invalid key 'z', then valid key 'a'
        with (
            patch("libcurses.menu.getkey", side_effect=[ord("z"), ord("a")]),
            patch("libcurses.menu.is_fkey", return_value=False),
            patch("libcurses.menu.logger") as mock_logger,
        ):
            result = menu_with_items.prompt()

        mock_logger.error.assert_called_once()
        assert result.keyname == "a"

    def test_prompt_calls_premenu(self, menu_with_items):
        """prompt calls premenu hook."""
        called = []
        menu_with_items.premenu = lambda: called.append("premenu")

        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        assert "premenu" in called

    def test_prompt_calls_preprompt(self, menu_with_items):
        """prompt calls preprompt hook."""
        called = []
        menu_with_items.preprompt = lambda: called.append("preprompt")

        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        assert "preprompt" in called

    def test_prompt_calls_getkey_with_no_mouse(self, menu_with_items):
        """prompt calls getkey with no_mouse=True."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")) as mock_getkey,
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        mock_getkey.assert_called_with(menu_with_items.win, no_mouse=True)

    def test_prompt_displays_pressed_key(self, menu_with_items):
        """prompt displays the pressed key."""
        with (
            patch("libcurses.menu.getkey", return_value=ord("a")),
            patch("libcurses.menu.is_fkey", return_value=False),
        ):
            menu_with_items.prompt()

        calls = menu_with_items.win.addstr.call_args_list
        # Should have call with "a\n"
        assert any("a" in str(c) for c in calls)
