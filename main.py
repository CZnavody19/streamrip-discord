from discord import app_commands, Intents, Client, Interaction
from dotenv import load_dotenv
from os import getenv
from re import compile
from streamrip.config import Config
from streamrip.client import Client, QobuzClient
from streamrip.db import Database, Downloads, Failed
from streamrip.media import Pending, PendingSingle, Media, Track

load_dotenv()

url_regex = compile(r"https?://(?:www|open|play|listen)?\.?(qobuz|tidal|deezer)\.com(?:(?:/(album|artist|track|playlist|video|label))|(?:\/[-\w]+?))+\/([-\w]+)")

media_message_template = "{} by {} [{}]"

rip_config = Config.defaults()
rip_config.session.downloads.folder = getenv("STREAMRIP_FOLDER")

rip_db = Database(downloads=Downloads(getenv("STREAMRIP_DB_DOWNLOADS")), failed=Failed(getenv("STREAMRIP_DB_FAILED")))

async def get_client(provider: str) -> Client:
    match provider:
        case "qobuz":
            rip_config.session.qobuz.use_auth_token = True
            rip_config.session.qobuz.email_or_userid = getenv("QOBUZ_USER_ID")
            rip_config.session.qobuz.password_or_token = getenv("QOBUZ_TOKEN")

            rip_client = QobuzClient(rip_config)
            await rip_client.login()
            if not rip_client.logged_in:
                raise ConnectionError

            return rip_client
        
        case _:
            raise NotImplementedError

def get_pending(type: str, id: str, client: Client, config: Config, database: Database) -> Pending:
    match type:
        case "track":
            return PendingSingle(id=id, client=client, config=config, db=database)

        case _:
            raise NotImplementedError

def get_media_message(media: Media) -> str:
    match media:
        case Track():
            return media_message_template.format(media.meta.title, media.meta.artist, "{}/{}".format(media.meta.info.sampling_rate, media.meta.info.bit_depth))

def setup_commands(tree):
    @app_commands.command(name="download", description="Download a song")
    @app_commands.describe(url='The url of the song')
    async def download(interaction: Interaction, url: str):
        await interaction.response.defer(ephemeral=True, thinking=True)

        regex = url_regex.match(url)
        if regex is None:
            return await interaction.followup.send("Invalid URL")
        
        provider, type, id = regex.groups()
        client = None
        try:
            client = await get_client(provider=provider)
        except ConnectionError:
            return await interaction.followup.send("Invalid credentials or network error")
        except NotImplementedError:
            return await interaction.followup.send("Service has not been implemented")
        
        pending = None
        try:
            pending = get_pending(type=type, id=id, client=client, config=rip_config, database=rip_db)
        except NotImplementedError:
            return await interaction.followup.send("Media type has not been implemented")
        
        media = await pending.resolve()
        if media is None:
            return await interaction.followup.send("Error resolving media (may be downloaded already)")

        await interaction.followup.send("Downloading {}".format(get_media_message(media=media)))

        await media.rip()

        await interaction.followup.send("Successfully downloaded {}".format(get_media_message(media=media)))

        client.session.connector.close()
        client.session.close()

    tree.add_command(download)

def main():
    intents = Intents.default()
    intents.message_content = True

    client = Client(intents=intents)
    tree = app_commands.CommandTree(client) 

    setup_commands(tree=tree)

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        await tree.sync()
        print(f'Commands successfully synced!')

    client.run(getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    main()