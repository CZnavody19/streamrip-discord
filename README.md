# Streamrip discord bot

## Function

-   `/download <url>` command to download the media (Qobuz tracks and Deezer standard and dynamic URLs are supported)
-   `/scan` command to rescan the plex library (only one server and library is supported)

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
    -   [x] Albums  (untested so far)
    -   [ ] Playlists
    -   [ ] Discographies
    -   [ ] Labels
-   [ ] Tidal
-   [x] Deezer
    -   [x] Tracks
    -   [x] Albums  (untested so far)
    -   [ ] Playlists
    -   [ ] Discographies
    -   [ ] Labels
-   [ ] SoundCloud

## Plex integration

You can optionaly set up an integration with Plex media server to refresh your music library with a command

### How to find your token:
-   In your web browser open your plex server web ui
-   Open devtools and go to network
-   Find a request with `X-Plex-Token` in the url and copy the token

### To get your library id go to the [plex API documentation page](https://plexapi.dev/api-reference/library/get-all-libraries) and run the request

##### The number you are looking for is under the "key" field