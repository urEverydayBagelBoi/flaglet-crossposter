# Basic utilities
import datetime

# Read .env (tokens, etc.)
from py_dotenv import read_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
read_dotenv(dotenv_path)

# Config File
import configparser

def create_config():
    config = configparser.ConfigParser()
    config['Database'] = {
        'path': 'relative/or/explicit'
    }
    config['Discord'] = {
        'art_channel': 'channel_id',
        'approval_channel': 'channel_id',
    }
    with open('config.ini', 'w') as config_file:
        config.write(config_file)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_values = {
        'discord_art_channel': int(config.get('Discord', 'art_channel')),
        'discord_approval_channel': int(config.get('Discord', 'approval_channel')),
        'db_path': config.get('Database', 'path'),
    }
    return config_values

config_values = None
database = config_values['db_path']

# Logging
import logging
logging.basicConfig()
discord_log = logging.getLogger("DiscordLog")
discord_log.setLevel(logging.DEBUG)

# Discord Client
import interactions
from interactions import Intents as DiscordIntents
from interactions.models.discord.message import Message as DiscordMessage
# from interactions.api.events import Component

discord_client = interactions.Client(
    intents=DiscordIntents.DEFAULT | DiscordIntents.MESSAGE_CONTENT,
    asyncio_debug=True,
    logger=discord_log
)

# //// Data ////
import aiosqlite
# These are hardcoded here
crossposts_columns = {
    'source_platform': 'TEXT NOT NULL',
    'created': 'INTEGER NOT NULL', # stored as unix timestamp
    'status': 'TEXT NOT NULL DEFAULT pending',
    'approved': 'INTEGER', # stored as unix timestamp

    'art_message_id': 'INTEGER NOT NULL UNIQUE',
    'art_message_channel_id': 'INTEGER NOT NULL',
    'author_id': 'INTEGER NOT NULL',
    'queue_message_id': 'INTEGER',
    'queue_message_channel_id': 'INTEGER',

    'discord_crosspost_id': 'INTEGER',
    'stoat_crosspost_id': 'INTEGER',
}

async def create_tables():
    # // create tables if they don't exist
    crossposts_columns_string = ""
    for k, v in crossposts_columns.items():
        crossposts_columns_string += f'"{k}" {v},\n'

    async with aiosqlite.connect(database) as conn:
        await conn.execute(f'''
            CREATE TABLE IF NOT EXISTS "crossposts" (
                {crossposts_columns_string}
                PRIMARY KEY("id")
            );
        ''')
        await conn.commit()

async def verify_columns(table_name, columns):
    if not isinstance(columns, dict):
        raise ValueError('usrdb.verify_columns(): columns parameter must be a dictionary')

    async with aiosqlite.connect(database) as conn:
        async with await conn.execute(f'PRAGMA table_info({table_name})') as cursor:
            existing_columns = await cursor.fetchall()
        logging.info(f"    [existing_columns]: {existing_columns}")
        existing_column_names = ['id'] + [column[1] for column in existing_columns]
        logging.info(f"Verifying table [{table_name}]")
        await conn.execute('BEGIN;')
        try:
            for column_name, column_definition in columns.items():
                if column_name not in existing_column_names:
                    await conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition};')
                    logging.info(f"Added column '{column_name}' to {table_name}")
                else:
                    logging.info(f"Column '{column_name}' already exists in {table_name}")
            await conn.commit()
        except aiosqlite.Error as e:
            await conn.rollback()
            logging.error(f"[USRDB 'verify_columns' ERROR]: {e}")


# Artpost class
class crosspost:
    def __init__(self, conn: aiosqlite.Connection, art_message: DiscordMessage | None, queue_message: DiscordMessage | None):
        if art_message is None and queue_message is None:
            raise ValueError("Neither art_message object nor queue_message object were provided!!")
        if art_message is not None and queue_message is not None:
            raise ValueError("art_message *and* queue_message were provided. Please only provide one.")

        if art_message:
            # TODO
            # Try to reconstruct from existing data in db
            # using art_message to index.abs
            # If it doesn't exist, set exists = False and return.
            # This variable will be caught later to create it.
        
        if queue_message:
            # TODO
            # Do the same thing as with art_message
            # but use queue_message to query instead

        if not exists:
            self.created = datetime.datetime.now()
            self.art_message = art_message

            # if type(art_message) == DiscordMessage:
            if isinstance(art_message, DiscordMessage):
                self.author = art_message.author
                self.platform = "discord"
                # TODO: Send a queue message and set queue_message to that message object

            self.status = "pending"
        
    def _store(self):
        # Store self in db.
        # TODO
        pass


# //// Discord Code ////
@interactions.listen()
async def on_ready():
    discord_log.info(f"Discord client ready. Logged in as {discord_client.user.global_name} - Owned by {discord_client.owner}")

@interactions.listen()
async def on_message_create(event):
    # discord_log.debug(f"Discord message received: {event.message.content}")
    content = event.message.content
    if not event.message.author.id == discord_client.user.id and ("!art " in content or content.endswith("!art")):
        attachment_urls = " ".join([attachment.url for attachment in event.message.attachments])
        msg = f"Original Message: {event.message.jump_url}\nAuthor: {event.message.author.mention}\n\n> {content}\n\n-# {attachment_urls}"
        discord_log.debug(f"Discord art channel from config: {config_values['discord_art_channel']}")
    
        _ = await discord_client.fetch_channel(config_values['discord_art_channel'])
        await _.send(msg)


if __name__ == "__main__":
    if not os.path.exists('config.ini'):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
    else:
        config_values = read_config()
        database = config_values['db_path']
        print(config_values)
        discord_client.start(token=(os.getenv('DISCORD_TOKEN')))