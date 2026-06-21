# Basic utilities
import datetime
import asyncio
from asyncinit import asyncinit

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
        'discord_art_channel': config.get('Discord', 'art_channel'),
        'discord_approval_channel': config.get('Discord', 'approval_channel'),
        'db_path': config.get('Database', 'path'),
    }
    # Sanity Checks
    # for k, v in config_values.items():
    #     if 'discord' in k:
    #         if 'channel' in k:
    #             #if type(v) is not interactions.models.discord.Snowflake_Type:
    #             if not isinstance(v, int):
    #                 raise ValueError(f"read_config(): Invalid config option: {k}={v}")

    return config_values

config_values = None
database = None

# Logging
import logging
logging.basicConfig()
discord_log = logging.getLogger("DiscordLog")
discord_log.setLevel(logging.INFO)
main_log = logging.getLogger("MainLog")
main_log.setLevel(logging.DEBUG)

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
    'id': 'INTEGER NOT NULL UNIQUE',
    'source_platform': 'TEXT NOT NULL',
    'created': 'INTEGER NOT NULL', # stored as unix timestamp
    'status': 'TEXT NOT NULL DEFAULT pending',
    'resolved': 'INTEGER', # stored as unix timestamp

    'art_message_id': 'INTEGER NOT NULL UNIQUE',
    'art_message_channel_id': 'INTEGER NOT NULL',
    'author_id': 'INTEGER NOT NULL',
    'queue_message_id': 'INTEGER',
    'queue_message_channel_id': 'INTEGER',

    'discord_original_post_id': 'INTEGER',
}

async def create_tables(conn):
    '''Create tables if they don't exist.'''
    crossposts_columns_string = ""
    for k, v in crossposts_columns.items():
        crossposts_columns_string += f'"{k}" {v},\n'

    try:
        await conn.execute(f'''
            CREATE TABLE IF NOT EXISTS "crossposts" (
                {crossposts_columns_string}
                PRIMARY KEY("id")
            );
        ''')
        await conn.commit()
    except aiosqlite.Error as e:
        await conn.rollback()
        main_log.error(f"[verify_columns() ERROR]: {e}")

async def verify_columns(conn, table_name, columns: dict):
    """Verify that passed table contains columns passed in columns dictionary.
    
    Implicitly uses the local 'database' variable as the target database.
    Assumes that the passed table exists.
    """

    async with await conn.execute(f'PRAGMA table_info({table_name})') as cursor:
        existing_columns = await cursor.fetchall()
    main_log.info(f"    [existing_columns]: {existing_columns}")
    existing_column_names = ['id'] + [column[1] for column in existing_columns]
    main_log.info(f"Verifying table [{table_name}]")
    await conn.execute('BEGIN;')
    try:
        for column_name, column_definition in columns.items():
            if column_name not in existing_column_names:
                await conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition};')
                main_log.info(f"Added column '{column_name}' to {table_name}")
            else:
                main_log.info(f"Column '{column_name}' already exists in {table_name}")
        await conn.commit()
    except aiosqlite.Error as e:
        await conn.rollback()
        main_log.error(f"[verify_columns() ERROR]: {e}")

async def setup_database(db_path):
    main_log.info(f'Setting up database with path: {db_path}')
    async with aiosqlite.connect(db_path) as conn:
        await create_tables(conn)
        await verify_columns(conn, 'crossposts', crossposts_columns)

# /// Artpost class ///
@asyncinit
class crosspost:
    '''Represents a crosspost from any specific platform.

    Keeps track of:
    - Resolve status
    - Datetime of creation and resolve
    - Origin Platform
    - Locally related messages (queue messages and the art post they refer to)
    - Crossposted messages (if any)
    
    Functions:
    - Completely purge a crosspost all at once from all platforms (emergencies)
    - Approve or deny a crosspost
    - Abstract interfacing with items stored in SQL

    Attributes:
        Universal:
            - id                int
            - source_platform   "discord", will be expanded with "stoat", etc.
            - created           datetime.datetime
            - status            "approved", "denied", "purged", "pending"
            - resolved          datetime.datetime | None
            - new               bool (whether recovered from db or newly registered)

        Varying form per source platform:
            - art_message           message object
            - author                user object
            - queue_message         message object

        May be None if source = destination:
            - discord_crosspost     message object
            Soon(tm):
            - stoat_crosspost       message object
    '''
    async def __init__(self, conn: aiosqlite.Connection, art_message: DiscordMessage=None, queue_message: DiscordMessage=None):
        if art_message:
            ref_message = art_message
            # TODO
            # Try to reconstruct from existing data in db
            # using art_message to index.abs
            # If it doesn't exist, set exists = False and return.
            # This variable will be caught later to create it.
            exists = False
        elif queue_message:
            ref_message = queue_message
            # TODO
            # Do the same thing as with art_message
            # but use queue_message to query instead
            # if there's a queue message, a crosspost should be registered. Otherwise there's a db error.
            exists = False
        # Invalid cases
        elif queue_message and art_message:
            raise ValueError("art_message *and* queue_message were provided. Please only provide one.")
        else:
            raise ValueError("Neither art_message object nor queue_message object were provided!!")
        if not exists:
            self.created = datetime.datetime.now()
            self.art_message = art_message
            if isinstance(art_message, DiscordMessage):
                self.source_platform = "discord"
                self.author = art_message.author
                # TODO: Send a queue message to Discord and immediately set queue_message to that message object
                # If it can't send this message, __init__ should fail.
                # *and* it should reply to an art message that it failed.
                queue_channel = await discord_client.fetch_channel(config_values['discord_approval_channel'])
                image_attachments = []
                # fields = []
                for attachment in art_message.attachments:
                    embed_attachment = interactions.EmbedAttachment(url=attachment.url, proxy_url=attachment.proxy_url)
                    main_log.debug(f'Attachment sent of content type: {attachment.content_type}')
                    if attachment.content_type == 'image':
                        image_attachments.append(embed_attachment)
                    # else:
                    #     fields += interactions.EmbedField(
                    #         name=f'{attachment.filename} - {attachment.content_type}',
                    #         value=attachment.url,
                    #     )
                # if fields == []:
                #     fields = None
                author = interactions.EmbedAuthor(
                    name=art_message.author.username,
                    url=f'https://discordapp.com/users/{art_message.author.id}',
                    icon_url=art_message.author.avatar_url,
                )
                # embed = interactions.Embed(
                #     author=author,
                #     description=art_message.content,
                #     timestamp=art_message.created_at,
                #     url=art_message.jump_url,
                #     footer=f"Original Message: {art_message.jump_url}",
                #     provider=interactions.EmbedProvider(name="Flaglet Bridge"),
                #     images=image_attachments,
                #     fields=fields
                # ),
                args = {
                    'title': f'{self.art_message.author.display_name} posted some art! (click to jump)',
                    'url': self.art_message.jump_url,
                    'author': author,
                    'description': str(self.art_message.content),
                    'timestamp': self.art_message.created_at,
                    'images': image_attachments,
                }
                if image_attachments != []:
                    args['images'] = image_attachments

                embed = interactions.Embed(**args)
                self.queue_message = await queue_channel.send(embed=embed)
            self.status = "pending"
        self.new = not exists

        
    def _store(self):
        '''
        sqlite db stores:
            Universal:
                - crosspost_id      = int - local identifier, totally seperate from platforms
                - source_platform   = string - "discord", can be "stoat" or other in the future
                - created           = UNIX timestamp (int)
                - status            = string - "approved", "denied", "purged" or "pending"
                - resolved          = UNIX timestamp (int) *or* None
            Varying in form per source platform:
                - art_message_id
                - art_message_channel_id
                - author_id
                - queue_message_id
                - queue_message_channel_id
        Returns:
        int: id in db
        '''
       # Store self in db.
        # See __init__ docstring for db formatting details
        # TODO
        pass
    
    def __repr__(self):
        # TODO:
        # this errors because some might be none
        # put 'None' as a string wherever the actual value is None
        return f'''
        //// Crosspost ////
        ID:                     {self.id}
        source_platform:        {self.source_platform}
        created:                {self.created}
        status:                 {self.status}
        resolved:               {self.resolved}
        new?:                   {self.new}
        art_message:            {self.art_message}
        art_message channel:    {self.art_message.channel}
        author:                 {self.author}
        queue_message:          {self.queue_message}
        queue_message channel:  {self.queue_message.channel}
        discord_crosspost:      {self.discord_crosspost}
        '''



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
        msg = f"Original Message: {event.message.jump_url}\nAuthor: {event.message.author.mention}\n\n> {content}"
        if not (attachment_urls is None or attachment_urls != ""):
            msg += "\n\n-# {attachment_urls}"
        discord_log.debug(f"Discord art channel from config: {config_values['discord_art_channel']}")
        _ = await discord_client.fetch_channel(config_values['discord_art_channel'])
        await _.send(msg)
    # TODO: Temp
    if not event.message.author.id == discord_client.user.id:
        main_log.debug(await crosspost(await aiosqlite.connect(database), event.message))

if __name__ == "__main__":
    init = True
    if not os.path.exists('config.ini'):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
        init = False
    elif config_values is None:
        try:
            config_values = read_config()
        except:
            raise AssertionError("Failed to read config. Did you use the right syntax?")
            init = False
    if config_values is not None and not os.path.exists(config_values['db_path']):
        database = config_values['db_path']
        main_log.debug(f'db_path: {database}')
        try:
            asyncio.run(setup_database(database))
        except aiosqlite.Error as e:
            main_log.error(f"Error while attempting to create database. aiosqlite error: {e}")
    if not os.path.exists(config_values['db_path']):
        raise AssertionError("Database did not exist after creation attempt. Did you specify the path correctly in the config?")

    if init:
        # print(config_values)
        discord_client.start(token=(os.getenv('DISCORD_TOKEN')))