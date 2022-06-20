from queue import SimpleQueue

import pytest
from loguru import logger

from tests.feeds.file import FileFeed
from tests.testlib import slow


@slow
@pytest.mark.parametrize(
    ("name", "nlines", "rewind", "follow"),
    [
        ("--rewind", 0, True, False),
        ("--rewind", 10, True, False),
        ("--rewind", 100, True, False),
        ("--rewind", 1000, True, False),
        #
        ("--no-rewind", 0, False, False),
        ("--no-rewind", 10, False, False),
        ("--no-rewind", 100, False, False),
        ("--no-rewind", 1000, False, False),
    ],
)
def test_queue_get(tmp_path, name, nlines, rewind, follow):

    _ = name  # unused
    path = tmp_path / f"file-with-{nlines}-lines.txt"
    path.write_text(
        "\n".join([f"This is line {x}" for x in range(1, nlines + 1)]),
        encoding="utf-8",
    )

    feed = FileFeed(SimpleQueue(), path, rewind=rewind, follow=follow)
    feed.debug = True
    last_lineno = None

    while True:
        (msgtype, lineno, line) = feed.queue.get()
        logger.debug(f"msgtype {msgtype} lineno {lineno} line `{line.strip()}`")
        if lineno <= 0:
            break
        last_lineno = lineno

    assert feed.lineno == nlines
    if last_lineno is not None:
        assert last_lineno == nlines

    logger.debug(f"NLINES: {nlines}")
