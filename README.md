# Streamrip discord bot

## Function

-   `/download <url>` command to download the media (Qobuz tracks and Deezer standard and dynamic URLs are supported)

## Installation

-   Install [Streamrip](https://github.com/nathom/streamrip/) and make sure you can use the scripting function
-   Install [`discord.py`](https://discordpy.readthedocs.io/en/stable/) and [`dotenv`](https://pypi.org/project/python-dotenv/) python packages
-   Fill your info in the `.env` file
-   Run `main.py`

#### The projset also contains a `load_to_db.py` script, that searches and loads already present tracks to the streamrip database

If you want to use the `load_to_db.py` script, you also need to install the [`mutagen`](https://pypi.org/project/mutagen/) package

## Media and Service support

#### Deezer standard (https://www.deezer.com/us/track/568120982) and dynamic (https://deezer.page.link/qDcA9CTCiWkC5XhN6) URLs are supported

-   [x] Qobuz
    -   [x] Tracks
    -   [ ] Albums
    -   [ ] Playlists
    -   [ ] Discographies
    -   [ ] Labels
-   [ ] Tidal
-   [x] Deezer
    -   [x] Tracks
    -   [ ] Albums
    -   [ ] Playlists
    -   [ ] Discographies
    -   [ ] Labels
-   [ ] SoundCloud
