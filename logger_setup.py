from __future__ import annotations
import logging


def setup_logging() -> logging.Logger:
    main_log = logging.getLogger("main")
    main_log.setLevel(logging.INFO)

    # File Handler
    file_handler = logging.FileHandler("main.log")
    file_handler.setLevel(logging.INFO)
    main_log.addHandler(file_handler)

    # Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    main_log.addHandler(stream_handler)

    if main_log.hasHandlers():
        return main_log

    return main_log
