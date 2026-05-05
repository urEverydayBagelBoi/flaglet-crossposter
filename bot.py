import logging

from interactions import Client, Intents, listen
from interactions.api.events import Component

# Read .env (tokens, etc.)
from py_dotenv import read_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
read_dotenv(dotenv_path)

logging.basicConfig()
discord_log = logging.getLogger("FlagletLogger")
discord_log.setLevel(logging.DEBUG)

discord_client = Client(
    intents=Intents.DEFAULT | Intents.MESSAGE_CONTENT,
    asyncio_debug=True,
    logger=discord_log
)

@listen()
async def on_ready():
    discord_log.info(f"Ready. Logged in as {discord_client}\nOwned by {discord_client.owner}")

@listen()
async def on_message_create(event):
    # discord_log.debug(f"Message received: {event.message.content}")
    content = event.message.content
    if not event.message.author.id == discord_client.user.id and ("#art " in content or content.endswith("#art")):
        attachment_urls = " ".join([attachment.url for attachment in event.message.attachments])
        msg = f"Original Message: {event.message.jump_url}\nAuthor: {event.message.author.mention}\n\n> {content}\n\n-# {attachment_urls}"

        _ = await discord_client.fetch_channel(1462914139935477814)
        await _.send(msg)

discord_client.start(token=(os.getenv('DISCORD_TOKEN')))