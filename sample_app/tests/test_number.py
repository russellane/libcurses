from queue import SimpleQueue

from loguru import logger

from sample_app.feeds.number import NumberFeed
from sample_app.tests.testlib import slow


@slow
def test_feed():
    feed = NumberFeed(SimpleQueue())
    feed.next_timer(None)
    feed.next_timer(None)
    for _ in range(10):
        (msgtype, seq, msg) = feed.queue.get()
        logger.debug(f"msgtype {msgtype} seq {seq} line `{msg}`")
        if not seq:
            break
