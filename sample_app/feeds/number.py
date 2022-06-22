import itertools
import time
from queue import SimpleQueue
from threading import Thread

from loguru import logger


class NumberFeed:

    msgtype = "NUMBER"
    numbers = itertools.cycle([x * 10 for x in "123"])
    timers = itertools.cycle([3, 2, 1])
    timer = None
    debug = False

    def __init__(
        self,
        ctrlq: SimpleQueue,
    ):

        self.ctrlq = ctrlq
        self.queue = SimpleQueue()
        self.next_timer(None)
        Thread(target=self.run, name=self.msgtype, daemon=True).start()

    def run(self) -> None:

        for seq in itertools.count(start=1):
            time.sleep(self.timer)
            number = next(self.numbers)
            msg = f"{number} after {self.timer} seconds."
            self.queue.put((self.msgtype, seq, msg))
            self.ctrlq.put((self.msgtype, 0, None))

            if self.debug:
                msg = number.center(30, "-")
                logger.critical(msg)
                logger.error(msg)
                logger.warning(msg)
                logger.info(msg)
                logger.debug(msg)
                logger.trace(msg)

    def next_timer(self, key: int) -> None:

        self.timer = next(self.timers)
        logger.debug(f"key {key} timer {self.timer}")

    def toggle_debug(self, key: int) -> None:

        self.debug = not self.debug
        logger.debug(f"key {key} debug {self.debug}")
