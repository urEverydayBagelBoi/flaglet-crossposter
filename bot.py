# // Environment Variables //
from py_dotenv import read_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
read_dotenv(dotenv_path)

# // Config File //
import configparser


def create_config():
    config = configparser.ConfigParser()
    config["general"] = {
        "prefix": "!art",
        "debug": False,
    }
    config["discord"] = {
        "crosspost_channel": "channel_id",
    }
    with open("config.ini", "w") as config_file:
        config.write(config_file)


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    # config_values = {"discord_crosspost_channel": (config.get("Discord", "crosspost_channel"))}
    # return config_values
    if config['general']['debug'] is True:
        main_file_handler.setLevel(logging.DEBUG)
        main_stream_handler.setLevel(logging.DEBUG)
    return config


# config_values = None
config = None

# // Logging //
import logging

main_log = logging.getLogger("main")
main_log.setLevel(logging.DEBUG)

main_file_handler = logging.FileHandler("main.log")
main_file_handler.setLevel(logging.INFO)
main_log.addHandler(main_file_handler)

main_stream_handler = logging.StreamHandler()
main_stream_handler.setLevel(logging.INFO)
main_log.addHandler(main_stream_handler)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
main_file_handler.setFormatter(formatter)
main_stream_handler.setFormatter(formatter)

discord_log_handler = logging.FileHandler(
    filename="discord.log", encoding="utf-8", mode="w"
)


# // Discord //
import discord


class DiscordClient(discord.Client):
    crosspost_prefix = None

    # Need a better solution for this
    # def __init__(self, prefix):
    #     super().__init__()
    #     self.crosspost_prefix = config['general']['prefix']

    async def on_ready(self):
        main_log.info(
            f"Discord client ready. Logged in as {self.user.name} - Owned by {self.application.owner}"
        )
        self.crosspost_prefix = config['general']['prefix']

    async def on_message(self, message):
        main_log.debug(f"Discord message received: {message.content}")
        content = message.content
        if not message.author.id == self.user.id and (
            self.crosspost_prefix + " " in content or content.endswith(self.crosspost_prefix)
        ):
            main_log.debug(f"{DiscordClient.crosspost_prefix} messsage detected")
            attachment_urls = " ".join(
                [attachment.url for attachment in message.attachments]
            )
            msg = f"Original Message: {message.jump_url}\nAuthor: {message.author.mention}\n\n> {content}"
            if attachment_urls != "":
                msg += f"-# {attachment_urls}"

            main_log.debug(
                f"Discord crosspost channel from config: {config['discord']['crosspost_channel']}"
            )

            _ = await self.fetch_channel(config["discord"]["crosspost_channel"])
            await _.send(msg)


discord_intents = discord.Intents.default()
discord_intents.message_content = True
discord_client = DiscordClient(intents=discord_intents)

if __name__ == "__main__":
    if not os.path.exists("config.ini"):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
    else:
        config = read_config()
        if config is None:
            raise AssertionError("config was none after reading")
        main_log.debug(config)
        discord_client.run(
            token=os.getenv("DISCORD_TOKEN"), log_handler=discord_log_handler
        )
