import logging
import os

import colorama


class HighlightFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.levelno >= logging.ERROR:
            color = colorama.Fore.RED
        elif record.levelno >= logging.WARNING:
            color = colorama.Fore.YELLOW
        elif record.levelno >= logging.INFO:
            color = colorama.Fore.BLUE
        else:
            color = colorama.Fore.BLACK

        return "".join([color, super().format(record), colorama.Style.RESET_ALL])


def setup(name: str) -> None:
    # Ability to setup custom log levels for libs
    root_logger = logging.getLogger()

    logging.getLogger("asyncio").setLevel(logging.ERROR)

    # Collect the log level from environment
    level = getattr(logging, os.environ.get("LOG_LEVEL", "info").upper(), logging.INFO)
    root_logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(
        HighlightFormatter(f"{name} %(asctime)s [%(levelname)s] %(message)s")
    )

    root_logger.addHandler(handler)
