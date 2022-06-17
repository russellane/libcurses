"""Logger sink to curses."""

from queue import SimpleQueue

from loguru import logger

from libcurses.console import ConsoleMessageType


class LoggerSink:
    """Logger sink to curses."""

    msgtype = ConsoleMessageType.LOGGER.value

    def __init__(self, queue: SimpleQueue):
        """Logger sink to curses.

        Forward logger messages through `queue` to main-thread;
        main-thread will `dispatch` to handler that writes to curses.
        """

        self.queue = queue
        self.location = "{name}.{function}:{line}"
        self.verbose = 0
        self._level_name = "INFO"
        self._id = None
        #
        self.configure()

    def configure(self) -> None:
        """Configure the logger."""

        if self._id is not None:
            # Loguru can't actually change the format of an active logger;
            # remove and recreate.
            logger.trace(f"remove logger {self._id}")
            logger.remove(self._id)

        self._id = logger.add(
            lambda msg: self.queue.put((self.msgtype, msg.record["level"].name, msg)),
            level=self._level_name,
            format="|".join(
                [
                    "{time:HH:mm:ss.SSS}",
                    self.location,
                    "{level}",
                    "{message}{exception}",
                ]
            ),
        )

        logger.trace(f"add logger {self._id} location {self.location!r}")

    def set_location(self, location) -> None:
        """Set the location format.

        Args:
            location:   `loguru` format string to format the location section of each
                        message. For example, "{thread.name}:{file}:{line}:{function}".
        """

        self.location = location if location is not None else ""
        self.configure()

        logger.trace(f"update location={self.location!r}")

    def set_verbose(self, verbose: int) -> None:
        """Set logging level based on `--verbose`."""

        self.verbose = verbose
        _ = ["INFO", "DEBUG", "TRACE"]
        self._level_name = _[min(verbose, len(_) - 1)]
        self.configure()

        logger.trace(f"update verbose={self._level_name!r}")
