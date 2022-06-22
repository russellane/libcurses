import time
from pathlib import Path
from queue import SimpleQueue
from threading import Thread

from loguru import logger


class FileFeed:

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    msgtype = "FILE"
    lineno: int = 0
    is_eof: bool = False

    def __init__(
        self,
        ctrlq: SimpleQueue,
        path: Path | str,
        *,
        rewind: bool = True,
        follow: bool = False,
    ):

        self.ctrlq = ctrlq
        self.path = Path(path)
        self.rewind = rewind
        self.follow = follow
        self.queue = SimpleQueue()
        self.msgtype = str(path)

        Thread(target=self.run, name=self.__class__.msgtype, daemon=True).start()

    def run(self) -> None:

        logger.debug(f"open({str(self.path)!r})")

        with open(self.path, encoding="utf-8", errors="replace") as file:

            if not self.rewind:
                for _ in file:
                    self.lineno += 1

            while True:
                # logger.debug(f"reading {str(self.path)!r}")
                for line in file:
                    self.lineno += 1
                    self.queue.put((self.msgtype, self.lineno, line))
                    self.ctrlq.put((self.msgtype, 0, None))

                self.is_eof = True
                if not self.follow:
                    self.queue.put((self.msgtype, -self.lineno, ""))
                    self.ctrlq.put((self.msgtype, 0, None))
                    break
                time.sleep(1)
