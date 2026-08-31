from __future__ import annotations
from configparser import ConfigParser

# from logging import Handler, Logger
import logging
import discord
from py_dotenv import read_dotenv
import os


# // Logging //
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


# // Environment Variables //
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
read_dotenv(dotenv_path)


def setup() -> tuple[ConfigParser | None, Logger, Handler]:
    """Sets up logging and config
    Returns:
        config
        MAIN_LOG
        DISCORD_LOG_HANDLER
    """
    from config_manager import create_config, read_config
    from logging import FileHandler
    from logger_setup import setup_logging

    # // Logging //
    MAIN_LOG = setup_logging()
    DISCORD_LOG_HANDLER = FileHandler(filename="discord.log", mode="w")

    # // Config //
    if not os.path.exists("config.ini"):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
        return None, MAIN_LOG, DISCORD_LOG_HANDLER

    def error(e):
        _ = "Failed to start bot due to error reading config."
        if e:
            _ += f"\nError: {e}"
        MAIN_LOG.error(_ + "\nExiting.")
        raise AssertionError()

    try:
        config = read_config()
        if config is None:
            error("config was none after read attempt")
        return (config, MAIN_LOG, DISCORD_LOG_HANDLER)
    except Exception as e:
        error(e)


# // Discord //
class DiscordClient(discord.Client):
    crosspost_prefix: str
    target_channel: discord.TextChannel

    async def on_ready(self):
        # prefix
        if config is None:
            raise AssertionError("no config variable found when on_ready was called")
        if config["general"]["prefix"] is None:
            raise AssertionError(
                "No prefix value found when indexing config['general']['prefix']"
            )
        self.crosspost_prefix = config["general"]["prefix"]

        # crosspost feed channel
        crosspost_channel = await self.fetch_channel(
            int(config["discord"]["crosspost_channel"])
        )
        if isinstance(crosspost_channel, discord.TextChannel):
            self.target_channel = crosspost_channel
        else:
            _ = f"channel {crosspost_channel} is NOT a text channel."
            MAIN_LOG.error(_)
            raise AssertionError(_)

        MAIN_LOG.info(
            f"Discord client ready. Logged in as {self.user.name} - Owned by {self.application.owner}"
        )

    async def on_message(self, message):
        MAIN_LOG.debug(f"Discord message received: {message.content}")
        content = message.content
        prefix = self.crosspost_prefix

        if not message.author.id == self.user.id and (
            self.crosspost_prefix + " " in content
            or content.endswith(self.crosspost_prefix)
        ):
            MAIN_LOG.debug(f"{self.crosspost_prefix} messsage detected")
            MAIN_LOG.debug(
                f"Discord crosspost channel from config: {config['discord']['crosspost_channel']}"
            )

            # // Embed //
            title = config["general"]["crosspost_message"].format(
                user=message.author.name
            )
            main_embed = discord.Embed(
                title=title,
                description=content,
                url=message.jump_url,
                timestamp=message.created_at,
            )
            user_url = f"https://discord.com/users/{message.author.id}"
            main_embed.set_author(
                name=message.author.name,
                icon_url=message.author.avatar.url,
                url=user_url,
            )
            MAIN_LOG.debug(f"user_url: {user_url}")
            MAIN_LOG.debug(f"main_embed: {main_embed}")

            # // Attachments //
            image_attachments = []
            # non_image_attachments = []
            for attachment in message.attachments:
                if attachment.content_type.startswith("image"):
                    # image_attachments += attachment
                    image_attachments.append(attachment)
                # else:
                #     non_image_attachments.append(attachment)
            urls = [attachment.url for attachment in image_attachments]
            # Note: image_attachments and non_image_attachments will be used later

            # // Send //
            if urls == []:
                MAIN_LOG.debug(f"No valid attachments in message.")
                await self.target_channel.send(embed=main_embed)
            elif len(urls) > 1:
                MAIN_LOG.debug(f"Multiple valid attachments in message.")
                if len(message.attachments) > 4:
                    extra = str(len(message.attachments) - 4)
                    footer = f"+{extra} other attachments"
                    main_embed.set_footer(text=footer)
                embeds = [
                    main_embed,
                ] + [
                    discord.Embed(url=message.jump_url).set_image(url=url)
                    for url in urls[0:]
                ]
                await self.target_channel.send(embeds=embeds)
            else:
                MAIN_LOG.debug(f"One valid attachment in message.")
                main_embed.set_image(url=urls[0])
                await self.target_channel.send(embed=main_embed)

    async def welcome_message(self):
        # TODO: implement
        pass


# NOTE: Is this necessary now? (since I renamed the main file from bot.py to __main__.py
if __name__ == "__main__":
    config, MAIN_LOG, DISCORD_LOG_HANDLER = setup()
    if config is None:
        exit()  # Note to self: setup() may use create_config() and return nothing for config. This is totally valid

    discord_intents = discord.Intents.default()
    discord_intents.message_content = True
    discord_client = DiscordClient(intents=discord_intents)

    discord_client.run(
        token=os.getenv("DISCORD_TOKEN"), log_handler=DISCORD_LOG_HANDLER
    )
