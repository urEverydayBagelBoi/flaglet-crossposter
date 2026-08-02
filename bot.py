# // Environment Variables //
from py_dotenv import read_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
read_dotenv(dotenv_path)

# // Seperate Modules //
from config_manager import create_config, read_config
from logger_setup import MAIN_LOG, DISCORD_LOG_HANDLER


def setup():
    if not os.path.exists("config.ini"):
        create_config()
        MAIN_LOG.info("Config file created. Please edit it before running bot.py again.")
        return None, MAIN_LOG


    def error(e):
        _ = "Failed to start bot due to error reading config."
        if e:
            _ += f"\nError: {e}"
        MAIN_LOG.error(_ + "\nExiting.")
        raise AssertionError()
    
    try:
        config = read_config()
    except Exception as e:
        error(e)
    if config is None:
        error("config was none after read attempt")

    try:
        is_debug = config.getboolean('general', 'debug')
    except (KeyError, ValueError):
            is_debug = False # just default to false if unable to read
    
    if is_debug:
        MAIN_LOG.setLevel(logging.DEBUG)

    return config, MAIN_LOG

# // Discord //
import discord

class DiscordClient(discord.Client):
    # Overridden later
    crosspost_prefix = None
    target_channel = None

    # Need a better solution for this
    # def __init__(self, prefix):
    #     super().__init__()
    #     self.crosspost_prefix = config['general']['prefix']

    async def on_ready(self):
        self.crosspost_prefix = config['general']['prefix']
        self.target_channel = await self.fetch_channel(config["discord"]["crosspost_channel"])
        MAIN_LOG.info(
            f"Discord client ready. Logged in as {self.user.name} - Owned by {self.application.owner}"
        )

    async def on_message(self, message):
        MAIN_LOG.debug(f"Discord message received: {message.content}")
        content = message.content
        prefix = self.crosspost_prefix

        if not message.author.id == self.user.id and (
            prefix + " " in content or content.endswith(prefix)
        ):
            MAIN_LOG.debug(f"Messsage with prefix {prefix} detected")
            attachment_urls = " ".join(
                [attachment.url for attachment in message.attachments]
            )
            msg = f"Original Message: {message.jump_url}\nAuthor: {message.author.mention}\n\n> {content}"
            if attachment_urls != "":
                msg += f"\n-# {attachment_urls}"

            MAIN_LOG.debug(
                f"Discord crosspost channel from config: {config['discord']['crosspost_channel']}"
            )

            await self.target_channel.send(msg)



if __name__ == "__main__":
    config, log = setup()

    if config is None:
        raise AssertionError("No config found at runtime.")

    discord_intents = discord.Intents.default()
    discord_intents.message_content = True
    discord_client = DiscordClient(intents=discord_intents)

    discord_client.run(
        token=os.getenv("DISCORD_TOKEN"), log_handler=DISCORD_LOG_HANDLER
    )
