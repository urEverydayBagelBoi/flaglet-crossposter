# Read .env (tokens, etc.)
from py_dotenv import read_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
read_dotenv(dotenv_path)

# Config File
import configparser

def create_config():
    config = configparser.ConfigParser()
    config['Discord'] = {
        'art_channel': 'channel_id',
    }
    with open('config.ini', 'w') as config_file:
        config.write(config_file)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_values = {
        'discord_art_channel': (config.get('Discord', 'art_channel'))
    }
    return config_values

config_values = None

# Logging
import logging
logging.basicConfig()
discord_log = logging.getLogger("FlagletLogger")
discord_log.setLevel(logging.DEBUG)

# Discord Client
import interactions
from interactions import Intents as DiscordIntents
# from interactions.api.events import Component

discord_client = interactions.Client(
    intents=DiscordIntents.DEFAULT | DiscordIntents.MESSAGE_CONTENT,
    asyncio_debug=True,
    logger=discord_log
)

@interactions.listen()
async def on_ready():
    discord_log.info(f"Discord client ready. Logged in as {discord_client} - Owned by {discord_client.owner}")

@interactions.listen()
async def on_message_create(event):
    # discord_log.debug(f"Discord message received: {event.message.content}")
    content = event.message.content
    if not event.message.author.id == discord_client.user.id and ("#art " in content or content.endswith("#art")):
        attachment_urls = " ".join([attachment.url for attachment in event.message.attachments])
        msg = f"Original Message: {event.message.jump_url}\nAuthor: {event.message.author.mention}\n\n> {content}\n\n-# {attachment_urls}"
        # discord_log.debug(f"Discord art channel from config: {config_values['discord_art_channel']}")
    
        _ = await discord_client.fetch_channel(config_values['discord_art_channel'])
        await _.send(msg)

if __name__ == "__main__":
    if not os.path.exists('config.ini'):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
    else:
        config_values = read_config()
        print(config_values)
        discord_client.start(token=(os.getenv('DISCORD_TOKEN')))