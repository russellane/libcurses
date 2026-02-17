"""Tests for Border namedtuple."""

from libcurses.border import Border


class TestBorder:
    """Test Border namedtuple."""

    def test_all_defaults(self):
        """Border can be created with all defaults (zeros)."""
        border = Border()

        assert border.ls == 0
        assert border.rs == 0
        assert border.ts == 0
        assert border.bs == 0
        assert border.tl == 0
        assert border.tr == 0
        assert border.bl == 0
        assert border.br == 0

    def test_custom_values(self):
        """Border can be created with custom values."""
        border = Border(
            ls=ord("|"),
            rs=ord("|"),
            ts=ord("-"),
            bs=ord("-"),
            tl=ord("+"),
            tr=ord("+"),
            bl=ord("+"),
            br=ord("+"),
        )

        assert border.ls == ord("|")
        assert border.rs == ord("|")
        assert border.ts == ord("-")
        assert border.bs == ord("-")
        assert border.tl == ord("+")
        assert border.tr == ord("+")
        assert border.bl == ord("+")
        assert border.br == ord("+")

    def test_partial_defaults(self):
        """Border uses defaults for unspecified fields."""
        border = Border(ls=1, rs=2)

        assert border.ls == 1
        assert border.rs == 2
        assert border.ts == 0  # default
        assert border.bs == 0  # default

    def test_positional_args(self):
        """Border accepts positional arguments."""
        border = Border(1, 2, 3, 4, 5, 6, 7, 8)

        assert border.ls == 1
        assert border.rs == 2
        assert border.ts == 3
        assert border.bs == 4
        assert border.tl == 5
        assert border.tr == 6
        assert border.bl == 7
        assert border.br == 8

    def test_field_names(self):
        """Border has correct field names."""
        assert Border._fields == ("ls", "rs", "ts", "bs", "tl", "tr", "bl", "br")

    def test_is_tuple(self):
        """Border is a tuple subclass."""
        border = Border()
        assert isinstance(border, tuple)

    def test_indexable(self):
        """Border fields are indexable."""
        border = Border(1, 2, 3, 4, 5, 6, 7, 8)

        assert border[0] == 1  # ls
        assert border[7] == 8  # br

    def test_iterable(self):
        """Border is iterable."""
        border = Border(1, 2, 3, 4, 5, 6, 7, 8)

        assert list(border) == [1, 2, 3, 4, 5, 6, 7, 8]
