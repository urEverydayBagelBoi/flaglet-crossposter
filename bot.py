debug_mode = False
# // Environment Variables //
from py_dotenv import read_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
read_dotenv(dotenv_path)

# // Config File //
import configparser


def create_config():
    config = configparser.ConfigParser()
    config["Discord"] = {
        "art_channel": "channel_id",
    }
    with open("config.ini", "w") as config_file:
        config.write(config_file)


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    config_values = {"discord_art_channel": (config.get("Discord", "art_channel"))}
    return config_values


config_values = None

# // Logging //
import logging

main_log = logging.getLogger('main')
main_log.setLevel(logging.DEBUG)

main_file_handler = logging.FileHandler('main.log')
main_file_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
main_log.addHandler(main_file_handler)

main_stream_handler = logging.StreamHandler()
main_stream_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
main_log.addHandler(main_stream_handler)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
main_file_handler.setFormatter(formatter)
main_stream_handler.setFormatter(formatter)

discord_log_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# // Discord //
import discord
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)


@discord_client.event
async def on_ready():
    main_log.info(
        f"Discord client ready. Logged in as {discord_client.user.name} - Owned by {discord_client.application.owner}"
    )


@discord_client.event
async def on_message(message):
    main_log.debug(f"Discord message received: {message.content}")
    content = message.content
    if not message.author.id == discord_client.user.id and (
        "!art " in content or content.endswith("!art")
    ):
        main_log.debug("!art messsage detected")
        attachment_urls = " ".join(
            [attachment.url for attachment in message.attachments]
        )
        msg = f"""Original Message: {message.jump_url}\nAuthor: {message.author.mention}\n\n> {content}\n\n-# {attachment_urls}"""
        main_log.debug(f"Discord art channel from config: {config_values['discord_art_channel']}")

        _ = await discord_client.fetch_channel(config_values["discord_art_channel"])
        await _.send(msg)


if __name__ == "__main__":
    if not os.path.exists("config.ini"):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
    else:
        config_values = read_config()
        if config_values is None:
            raise AssertionError("config_values was none after reading")
        main_log.debug(config_values)
        discord_client.run(token=os.getenv('DISCORD_TOKEN'), log_handler=discord_log_handler)