import logging

from interactions import Client, Intents, listen
from interactions.api.events import Component

from py_dotenv import read_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
read_dotenv(dotenv_path)


logging.basicConfig()
flaglet_log = logging.getLogger("FlagletLogger")
flaglet_log.setLevel(logging.DEBUG)

client = Client(
    intents=Intents.DEFAULT | Intents.MESSAGE_CONTENT,
    asyncio_debug=True,
    logger=flaglet_log
)

@listen()
async def on_ready():
    flaglet_log.info(f"Ready. Logged in as {client}\nOwned by {client.owner}")

@listen()
async def on_message_create(event):
    # flaglet_log.debug(f"Message received: {event.message.content}")
    content = event.message.content
    if not event.message.author.id == client.user.id and ("#art " in content or content.endswith("#art")):
        attachment_urls = " ".join([attachment.url for attachment in event.message.attachments])
        msg = f"Original Message: {event.message.jump_url}\nAuthor: {event.message.author.mention}\n\n> {content}\n\n-# {attachment_urls}"

        _ = await client.fetch_channel(1462914139935477814)
        await _.send(msg)

client.start(token=(os.getenv('DISCORD_TOKEN')))
