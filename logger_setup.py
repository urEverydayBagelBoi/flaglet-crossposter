import logging

def setup_logging():
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


# These are imported from bot.py
MAIN_LOG = setup_logging()
DISCORD_LOG_HANDLER = logging.FileHandler(
    filename="discord.log", mode="w"
)