"""Loguru/curses colormap.

This module provides the `get_colormap` function.
"""

import curses
import re

from loguru import logger

__all__ = ["get_colormap"]

_COLORMAP: dict[str, int] = {}  # key=loguru-level-name, value=curses-color/attr


def get_colormap() -> dict[str, int]:
    """Return map of `loguru-level-name` to `curses-color/attr`.

    Call after creating all custom levels with `logger.level()`.
    Map is build once and cached; repeated calls return same map.
    """

    global _COLORMAP  # noqa
    if not _COLORMAP:
        _COLORMAP = {}

        colors = {
            "black": curses.COLOR_BLACK,
            "blue": curses.COLOR_BLUE,
            "cyan": curses.COLOR_CYAN,
            "green": curses.COLOR_GREEN,
            "magenta": curses.COLOR_MAGENTA,
            "red": curses.COLOR_RED,
            "white": curses.COLOR_WHITE,
            "yellow": curses.COLOR_YELLOW,
        }

        attrs = {
            "bold": curses.A_BOLD,
            "dim": curses.A_DIM,
            "normal": curses.A_NORMAL,
            "hide": curses.A_INVIS,
            "italic": curses.A_ITALIC,
            "blink": curses.A_BLINK,
            "strike": curses.A_HORIZONTAL,
            "underline": curses.A_UNDERLINE,
            "reverse": curses.A_REVERSE,
        }

        # Parse strings like:
        #   "red bold"
        #   "green, reverse"
        #   "<blue><italic><WHITE>"
        # Apply lowercase colors to fg, and uppercase to bg.

        re_words = re.compile(r"[\w]+")

        for idx, lvl in enumerate(logger._core.levels.values()):  # type: ignore # noqa protected-access
            fg = curses.COLOR_WHITE
            bg = curses.COLOR_BLACK
            attr = 0
            for word in re_words.findall(lvl.color):
                if word.islower() and (_ := colors.get(word)):
                    fg = _
                elif word.isupper() and (_ := colors.get(word.lower())):
                    bg = _
                elif _ := attrs.get(word):
                    attr |= _

            curses.init_pair(idx + 1, fg, bg)
            _COLORMAP[lvl.name] = curses.color_pair(idx + 1) | attr
            logger.trace(
                f"name={lvl.name} color={lvl.color} idx={idx+1} fg={fg} bg={bg} "
                f"color={_COLORMAP[lvl.name]} attr={attr:o}"
            )

    return _COLORMAP
