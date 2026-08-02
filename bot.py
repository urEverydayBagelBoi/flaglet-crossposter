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
        "crosspost_message": "{user} posted some art!",
        "debug": False,
    }
    config["discord"] = {
        "crosspost_channel": "channel_id_here",
    }
    with open("config.ini", "w") as config_file:
        config.write(config_file)


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    # config_values = {"discord_crosspost_channel": (config.get("Discord", "crosspost_channel"))}
    # return config_values
    if config["general"]["debug"] is True:
        main_file_handler.setLevel(logging.DEBUG)
        main_stream_handler.setLevel(logging.DEBUG)
    return config


# config_values = None
config = None

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

    async def on_ready(self):
        main_log.info(
            f"Discord client ready. Logged in as {self.user.name} - Owned by {self.application.owner}"
        )
        self.crosspost_prefix = config['general']['prefix']

    async def on_message(self, message):
        main_log.debug(f"Discord message received: {message.content}")
        content = message.content
        if not message.author.id == self.user.id and (
            self.crosspost_prefix + " " in content
            or content.endswith(self.crosspost_prefix)
        ):
            main_log.debug(f"{DiscordClient.crosspost_prefix} messsage detected")

            # Notes:
            # I'm considering implementing bot-/server-side AI data poisoning for all art (images and text mainly)
            # before reuploading that back to Discord or in crossposts to other platforms.
            # That's why I'm universally downloading images instead of just passing attachment URLs.
            # For now at least.

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

            main_log.debug(
                f"Discord crosspost channel from config: {config['discord']['crosspost_channel']}"
            )
            _ = await self.fetch_channel(config["discord"]["crosspost_channel"])
            await _.send(msg)

    async def welcome_message(self):
        # TODO: implement
        # sent to every new member with a disclaimer on using crossposting downloading and saving the images for a future public gallery
        pass


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
