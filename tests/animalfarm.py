import itertools
import threading
import time
from queue import SimpleQueue

from loguru import logger


class AnimalFarm:
    """Produce an animal every 'x' seconds."""

    name = "ANIMAL"
    animals = itertools.cycle(
        ["11111-CAT", "22222-DOG", "33333-HORSE", "44444-LION", "55555-ZEBRA"]
    )
    timers = itertools.cycle([3, 2, 1])

    def __init__(self, queue: SimpleQueue):
        """Produce an animal every 'x' seconds."""

        self.queue = queue
        self.debug = False
        self.timer = None
        self.next_timer(None)
        threading.Thread(target=self.work, name=self.name, daemon=True).start()

    def work(self) -> None:
        """Produce an animal every 'x' seconds."""

        for seq in itertools.count(start=1):
            time.sleep(self.timer)
            animal = next(self.animals)
            msg = f"{animal} after {self.timer} seconds."
            self.queue.put((self.name, seq, msg))

            if self.debug:
                msg = animal.rjust(30, "-")
                logger.error(msg)
                logger.warning(msg)
                logger.info(msg)
                logger.debug(msg)
                logger.trace(msg)

    def next_timer(self, key: int) -> None:
        """Change `timer`; signature per `register_fkey`."""

        self.timer = next(self.timers)
        if self.debug:
            logger.success(f"key={key} timer={self.timer}")

    def toggle_debug(self, key: int) -> None:
        """Change `debug`; signature per `register_fkey`."""

        self.debug = not self.debug
        if self.debug:
            logger.success(f"key={key} debug={self.debug}")
