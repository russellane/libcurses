import os
import threading
import time
from pathlib import Path
from queue import SimpleQueue


class FileFeed:

    # pylint: disable=too-few-public-methods

    msgtype = "FILE"
    lineno: int = 0
    is_eof: bool = False

    def __init__(
        self,
        queue: SimpleQueue,
        path: os.PathLike,
        rewind: bool = True,
        follow: bool = False,
    ):

        self.queue = queue
        self.path = Path(path)
        self.rewind = rewind
        self.follow = follow

        threading.Thread(target=self.run, name=self.msgtype, daemon=False).start()

    def run(self) -> None:

        with open(self.path, encoding="utf-8", errors="replace") as file:

            if not self.rewind:
                for _ in file:
                    self.lineno += 1

            while True:
                time.sleep(1)
                for line in file:
                    self.lineno += 1
                    self.queue.put((self.msgtype, self.lineno, line))
                    time.sleep(0.001)  # need context switch

                self.is_eof = True
                if not self.follow:
                    self.queue.put((self.msgtype, -self.lineno, ""))
                    break
