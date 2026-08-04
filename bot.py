# // Environment Variables //
from py_dotenv import read_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
read_dotenv(dotenv_path)


# // Setup... //
# - Logging
# - Config
def setup():
    # Import Config
    from config_manager import create_config, read_config

    # Logging
    from logging import FileHandler
    from logger_setup import setup_logging

    MAIN_LOG = setup_logging()
    DISCORD_LOG_HANDLER = FileHandler(
        filename="discord.log", mode="w"
    )

    # // Config //
    if not os.path.exists("config.ini"):
        create_config()
        print("Config file created. Please edit it before running bot.py again.")
        return None, MAIN_LOG, 


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

    
    return config, MAIN_LOG, DISCORD_LOG_HANDLER




# // Discord //
import discord

class DiscordClient(discord.Client):
    # Overridden later
    crosspost_prefix = None
    target_channel = None

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
            self.crosspost_prefix + " " in content
            or content.endswith(self.crosspost_prefix)
        ):
            MAIN_LOG.debug(f"{DiscordClient.crosspost_prefix} messsage detected")
            MAIN_LOG.debug(
                f"Discord crosspost channel from config: {config['discord']['crosspost_channel']}"
            )

            title = config["general"]["crosspost_message"].format(user=message.author.name)
            main_embed = discord.Embed(
                title=title,
                description=content,
                url=message.jump_url,
                timestamp=message.created_at,
            )
            user_url = f"https://discord.com/users/{message.author.id}"
            main_embed.set_author(name=message.author.name, icon_url=message.author.avatar.url, url=user_url)

            filtered_attachments = filter(lambda attachment: attachment.content_type.startswith("image"), message.attachments)
            filtered_attachments = list(filtered_attachments)
            MAIN_LOG.debug(f"main_embed: {main_embed}")
            MAIN_LOG.debug(f"user_url: {user_url}")
            MAIN_LOG.debug(f"filtered_attachments: {filtered_attachments}")

            # just use cdn media links instead of downloading and reuploading
            if filtered_attachments == []:
                MAIN_LOG.debug(f"No valid attachments in message.")
                await self.target_channel.send(embed=main_embed)
            elif len(filtered_attachments) > 1:
                MAIN_LOG.debug(f"Multiple valid attachments in message.")
                embeds = [main_embed,] + [discord.Embed(url=message.jump_url).set_image(url=attachment.url) for attachment in filtered_attachments[0:]]
                await self.target_channel.send(embeds=embeds)
            else:
                MAIN_LOG.debug(f"One valid attachment in message.")
                main_embed.set_image(url=filtered_attachments[0].url)
                await self.target_channel.send(embed=main_embed)
            

    async def welcome_message(self):
        # TODO: implement
        # sent to every new member with a disclaimer on using crossposting downloading and saving the images for a future public gallery
        pass



if __name__ == "__main__":
    config, MAIN_LOG, DISCORD_LOG_HANDLER = setup()
    if config is None:
        exit() # Note to self: setup() may use create_config() and return nothing for config. This is totally valid


    discord_intents = discord.Intents.default()
    discord_intents.message_content = True
    discord_client = DiscordClient(intents=discord_intents)

    discord_client.run(
        token=os.getenv("DISCORD_TOKEN"), log_handler=DISCORD_LOG_HANDLER
    )
