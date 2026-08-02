# // Environment Variables //
from py_dotenv import read_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
read_dotenv(dotenv_path)

# // Files & Paths //
from thumbnail import generate_thumbnail
crosspost_path = {
    "image": "./media/image/",
    "video": "./media/video/",
    "audio": "./media/audio/",
    "text": "./media/text/",
    "video": "./media/3d/",
    "other": "./media/other/",
}
make_paths = ['./media/', './media/temp/']
make_paths += crosspost_paths.values()
for path in make_paths:
    os.makedirs(path, exist_ok=True)


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

            # Notes:
            # I'm considering implementing bot-/server-side AI training protection and data poisoning for all art (images and text mainly)
            # before reuploading that back to Discord or in crossposts to other platforms.
            # That's why I'm universally downloading images instead of just passing attachment URLs.

            # Collect media (might go with a different solution idk)
            # Note: This isn't a temporary cache. I'm intending to create a public viewable gallery on a future dedicated site (protected against scraping and glazed+nightshaded against AI training obviously)
            image_file_paths = []
            other_file_paths = []
            if attachments.len() == 1 and attachments[0].content_type.startswith("image"):
                single_image = attachments[0].url
            else:
                for attachment in message.attachments:
                    if attachment.content_type.startswith("image"):
                        path = crosspost_path["image"] + attachment.filename
                        image = True
                    elif attachment.content_type.startswith("video"):
                        path = crosspost_path["video"] + attachment.filename
                    elif attachment.content_type.startswith("audio"):
                        path = crosspost_path["audio"] + attachment.filename
                    elif attachment.content_type.startswith("text"):
                        path = crosspost_path["text"] + attachment.filename
                    elif attachment.content_type.startswith("model"):
                        path = crosspost_path["3d"] + attachment.filename
                    else:
                        path = crosspost_path["other"] + attachment.filename

                    if image:
                        image_file_paths += path
                    else:
                        other_file_paths += path

                    data = await attachment.read()
                    if data is not None:
                        with open(path, "wb") as file:
                            file.write(data)
                    else:
                        other_file_paths += './media/file-question-mark.png' # display this placeholder, icon from lucide.dev
            
            # TODO:
            # - Create a temporary directory in ./media/temp named after message.id for thumbnails
            # - Supported images just have to be downscaled first if they're too large, then copy to temp dir
            # - All other filetypes have to be turned into thumbnails with the thumbnail module, then copied to temp dir

            embed = discord.Embed(
                title=config["general"]["crosspost_message"],
                url=message.jump_url,
                timestamp=message.timestamp,
                color=discord.Color.blurple,
            )
            embed.add_field(value=content) # text
            if single_image:
                embed.set_image(url=single_image)

            MAIN_LOG.debug(
                f"Discord crosspost channel from config: {config['discord']['crosspost_channel']}"
            )

            await self.target_channel.send(msg)

    async def welcome_message(self):
        # TODO: implement
        # sent to every new member with a disclaimer on using crossposting downloading and saving the images for a future public gallery
        pass



if __name__ == "__main__":
    config, log = setup()

    if config is None:
        exit(1) # Note to self: setup may use create_config() and return nothing. This is totally valid

    discord_intents = discord.Intents.default()
    discord_intents.message_content = True
    discord_client = DiscordClient(intents=discord_intents)

    discord_client.run(
        token=os.getenv("DISCORD_TOKEN"), log_handler=DISCORD_LOG_HANDLER
    )
