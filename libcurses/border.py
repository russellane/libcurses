"""Arguments for window.border([ls[, rs[, ts[, bs[, tl[, tr[, bl[, br]]]]]]]])."""

from collections import namedtuple

__all__ = ["Border"]

Border = namedtuple(
    "Border",
    ["ls", "rs", "ts", "bs", "tl", "tr", "bl", "br"],
    defaults=[0, 0, 0, 0, 0, 0, 0, 0],
)
