"""Logger sink to curses."""

from queue import SimpleQueue

from loguru import logger

import libcurses


class LoggerSink:
    """Logger sink to curses."""

    def __init__(self, queue: SimpleQueue):
        """Logger sink to curses.

        Forward logger messages through a `SimpleQueue` to a curses-worker.
        """

        self._queue = queue
        self._level_name = "INFO"
        self._delim = "|"
        self._location = "{file}:{line}:{function}"
        self._logger_id = None
        self._init_sink()

        # for use by the curses-worker only
        # self.win = None

    def _init_sink(self) -> None:

        if self._logger_id is not None:
            # Loguru can't actually change the format of an active logger;
            # remove and recreate.
            logger.trace(f"remove _logger_id {self._logger_id}")
            logger.remove(self._logger_id)

        self._logger_id = logger.add(
            lambda msg: self._queue.put(
                (libcurses.ConsoleMessageType.LOGGER.value, msg.record["level"].name, msg)
            ),
            level=self._level_name,
            format=self._delim.join(
                [
                    "{time:HH:mm:ss.SSS}",
                    self._location,
                    "{level}",
                    "{message}{exception}",
                ]
            ),
        )

        logger.trace(f"add _logger_id {self._logger_id} _location {self._location!r}")

    def set_location(self, location) -> None:
        """Set the location format.

        Args:
            location:   `loguru` format string to format the location section of each
                        message. For example, "{thread.name}:{file}:{line}:{function}".
        """

        self._location = location if location is not None else ""
        self._init_sink()

    def set_verbose(self, verbose: int) -> None:
        """Set logging level based on `--verbose`."""

        _ = ["INFO", "DEBUG", "TRACE"]
        self._level_name = _[min(verbose, len(_) - 1)]
        self._init_sink()
