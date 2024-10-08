from discord import Client as DiscordClient
from discord import app_commands, Intents, Interaction
from dotenv import load_dotenv
from requests import get
from os import getenv
from re import compile
from streamrip.client import Client as StreamRipClient
from streamrip.config import Config
from streamrip.client import QobuzClient, DeezerClient
from streamrip.db import Database, Downloads, Failed
from streamrip.media import Pending, PendingSingle, Media, Track, PendingAlbum, Album

load_dotenv()

url_regex = compile(r"https?://(?:www|open|play|listen)?\.?(qobuz|tidal|deezer)\.com(?:(?:/(album|artist|track|playlist|video|label))|(?:\/[-\w]+?))+\/([-\w]+)")
deezer_dynamic_url_regex = compile(r"https://deezer\.page\.link/\w+")

media_message_template = "{} by {} [{}]"

plex_url_template = "{}://{}:{}/library/sections/{}/refresh"

rip_config = Config.defaults()
rip_config.session.downloads.folder = getenv("STREAMRIP_FOLDER")
rip_config.session.filepaths.add_singles_to_folder = True

rip_db = Database(downloads=Downloads(getenv("STREAMRIP_DB_DOWNLOADS")), failed=Failed(getenv("STREAMRIP_DB_FAILED")))

async def get_client(provider: str) -> StreamRipClient:
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
        
        case "deezer":
            rip_config.session.deezer.arl = getenv("DEEZER_ARL")

            rip_client = DeezerClient(rip_config)
            await rip_client.login()
            if not rip_client.logged_in:
                raise ConnectionError
            
            return rip_client
        
        case _:
            raise NotImplementedError

def get_pending(type: str, id: str, client: StreamRipClient, config: Config, database: Database) -> Pending:
    match type:
        case "track":
            return PendingSingle(id=id, client=client, config=config, db=database)
    
        case "album":
            return PendingAlbum(id=id, client=client, config=config, db=database)

        case _:
            raise NotImplementedError

def get_media_message(media: Media) -> str:
    match media:
        case Track():
            return media_message_template.format(media.meta.title, media.meta.artist, "{}/{}".format(media.meta.info.sampling_rate, media.meta.info.bit_depth))
        
        case Album():
            return media_message_template.format(media.meta.album, media.meta.albumartist, "{}/{}".format(media.meta.info.sampling_rate, media.meta.info.bit_depth))
        
def get_deezer_url(url: str) -> str:
    return get(url).url

def setup_commands(tree):
    @app_commands.command(name="download", description="Download a song")
    @app_commands.describe(url='The url of the song')
    async def download(interaction: Interaction, url: str):
        await interaction.response.defer(ephemeral=True, thinking=True)

        deezer_regex = deezer_dynamic_url_regex.match(url)
        if deezer_regex is not None:
            url = get_deezer_url(url)

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

    @app_commands.command(name="scan", description="Rescan the Plex library")
    async def scan(interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        url = plex_url_template.format(getenv("PLEX_SERVER_PROTOCOL"), getenv("PLEX_SERVER_URL"), getenv("PLEX_SERVER_PORT"), getenv("PLEX_LIBRARY_ID"))
        params = {"X-Plex-Token": getenv("PLEX_TOKEN")}
        response = get(url=url, params=params)

        if response.status_code == 200:
            return await interaction.followup.send("Successfully rescaned the library")

        await interaction.followup.send("Failed to refresh the library with error code {}".format(response.status_code))

    tree.add_command(download)
    if getenv("ENABLE_PLEX_REFRESH").lower() == "true":
        tree.add_command(scan)

def main():
    intents = Intents.default()
    intents.message_content = True

    client = DiscordClient(intents=intents)
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