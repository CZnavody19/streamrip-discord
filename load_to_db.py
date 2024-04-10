from os import walk
from os.path import join
from mutagen import File
from dotenv import load_dotenv
from asyncio import run
from os import getenv
from streamrip.client import QobuzClient
from streamrip.config import Config
from streamrip.db import Database, Downloads, Failed
from difflib import SequenceMatcher

load_dotenv()

rip_config = Config.defaults()
rip_config.session.downloads.folder = getenv("STREAMRIP_FOLDER")
rip_config.session.qobuz.use_auth_token = True
rip_config.session.qobuz.email_or_userid = getenv("QOBUZ_USER_ID")
rip_config.session.qobuz.password_or_token = getenv("QOBUZ_TOKEN")

rip_db = Database(downloads=Downloads(getenv("STREAMRIP_DB_DOWNLOADS")), failed=Failed(getenv("STREAMRIP_DB_FAILED")))

def get_all_songs(directory: str) -> list[File]:
    out = []
    for path, _, files in walk(directory):
        for file in files:
            out.append(File(join(path, file)))
    return out

def compare_tracks(local, qobuz):
    score = 0

    try:
        score += SequenceMatcher(None, local["title"][0], qobuz["title"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["composer"][0], qobuz["composer"]["name"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["albumartist"][0], qobuz["album"]["artist"]["name"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["date"][0], qobuz["release_date_original"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["copyright"][0], qobuz["copyright"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["isrc"][0], qobuz["isrc"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["genre"][0], qobuz["album"]["genre"]["name"]).ratio()
    except:
        pass
    try:
        score += SequenceMatcher(None, local["album"][0], qobuz["album"]["title"]).ratio()
    except:
        pass

    return score/8 #Divide by number of tests

async def main():
    rip_client = QobuzClient(rip_config)
    await rip_client.login()
    if not rip_client.logged_in:
        return print("Invalid login")
    
    for song in get_all_songs(getenv("STREAMRIP_FOLDER")):
        if song is not None:
            song_str = "{} {}".format(song["title"][0], song["artist"][0])
            print("Searching {}".format(song_str))
            search = await rip_client.search("track", song_str, limit=20)
            comparisons = {}
            for result in search[0]["tracks"]["items"]:
                comparisons[result["id"]] = compare_tracks(song, result)
            print("Got {} results: {}".format(len(comparisons), comparisons))
            most_likely_song = max(comparisons, key=comparisons.get)
            print("Adding {} to database".format(most_likely_song))
            if not rip_db.downloaded(most_likely_song):
                rip_db.set_downloaded(most_likely_song)
            print("Successfully added")
            print()

if __name__ == "__main__":
    run(main())