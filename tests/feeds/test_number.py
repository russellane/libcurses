import sys
from queue import SimpleQueue

from loguru import logger

from tests.feeds.number import NumberFeed

try:
    logger.remove(0)
except ValueError:
    ...
logger.add(sys.stderr, format="{level} {function} {line} {message}", level="TRACE")


def test_feed():
    queue = SimpleQueue()
    feed = NumberFeed(queue)
    feed.next_timer(None)
    feed.next_timer(None)
    for _ in range(10):
        (msgtype, seq, msg) = feed.queue.get()
        logger.debug(f"msgtype {msgtype} seq {seq} line `{msg}`")
        if not seq:
            break
