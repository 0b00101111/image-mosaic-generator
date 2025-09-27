# =============================================================================
#              1_download_covers.py - Album Cover Downloader
# =============================================================================
# This script connects to the Spotify API, finds albums for a list of artists,
# and downloads their cover art to be used as source images for our mosaic.
#
# IMPORTANT SECURITY NOTE:
# This script reads your Spotify credentials from environment variables to
# keep them secure and out of your code.
# =============================================================================

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import os

# --- 1. CONFIGURATION ---
OUTPUT_DIR = "raw_album_covers"
TARGET_COVERS = 5000 # The script will stop after reaching this number

# Massively expanded list for maximum diversity
ARTIST_NAMES = [
    # Classic Rock & Folk
    "The Beatles", "Led Zeppelin", "Pink Floyd", "Queen", "The Rolling Stones",
    "David Bowie", "Jimi Hendrix", "Bob Dylan", "Joni Mitchell", "Fleetwood Mac",
    "The Doors", "Creedence Clearwater Revival", "Eagles", "Neil Young", "The Who",

    # Pop & Modern
    "Taylor Swift", "Michael Jackson", "Madonna", "Prince", "Beyoncé", "Lady Gaga",
    "Rihanna", "Adele", "Bruno Mars", "Katy Perry", "Harry Styles", "Dua Lipa",

    # Hip-Hop / R&B
    "Kendrick Lamar", "Kanye West", "Frank Ocean", "Aretha Franklin", "Marvin Gaye",
    "Stevie Wonder", "A Tribe Called Quest", "OutKast", "Drake", "Jay-Z", "Dr. Dre",

    # Electronic & Dance
    "Daft Punk", "Kraftwerk", "Aphex Twin", "Massive Attack", "The Chemical Brothers",
    "LCD Soundsystem", "deadmau5", "Skrillex", "Boards of Canada", "Gorillaz",

    # Alternative & Indie
    "Radiohead", "Nirvana", "Björk", "Arcade Fire", "The Smiths", "Pixies",
    "Arctic Monkeys", "Vampire Weekend", "Tame Impala", "Florence + The Machine",

    # Jazz, Soul, Blues & Country
    "Miles Davis", "John Coltrane", "Nina Simone", "James Brown", "Etta James",
    "B.B. King", "Johnny Cash", "Dolly Parton", "Willie Nelson",

    # Metal & Punk
    "Metallica", "Black Sabbath", "Iron Maiden", "The Clash", "Ramones", "Sex Pistols",

    # And many more...
    "Elton John", "Billy Joel", "U2", "Red Hot Chili Peppers", "Green Day", "Foo Fighters",
    "Coldplay", "Muse", "The Killers", "Lana Del Rey", "Lorde", "Billie Eilish"
]

# --- 2. SETUP & EXECUTION ---
# Load credentials securely from environment variables
CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    print("FATAL ERROR: Spotify credentials not found in environment variables.")
    print("Please set 'SPOTIPY_CLIENT_ID' and 'SPOTIPY_CLIENT_SECRET' and try again.")
else:
    print(f"Starting large-scale album cover fetch. Target: {TARGET_COVERS} covers.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    downloaded_album_ids = set()

    for artist_name in ARTIST_NAMES:
        if len(downloaded_album_ids) >= TARGET_COVERS:
            print("\nTarget number of covers reached.")
            break

        print(f"\nSearching for artist: {artist_name}")
        try:
            results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            if not results['artists']['items']:
                print(f"  Could not find artist: {artist_name}. Skipping.")
                continue

            artist_id = results['artists']['items'][0]['id']
            offset = 0
            while offset < 100:
                albums = sp.artist_albums(artist_id, album_type='album,single', limit=50, offset=offset)
                if not albums['items']: break

                for album in albums['items']:
                    if len(downloaded_album_ids) >= TARGET_COVERS: break
                    album_id = album['id']
                    if album_id in downloaded_album_ids: continue
                    album_name = album['name']
                    if album['images']:
                        image_url = album['images'][0]['url']
                        try:
                            response = requests.get(image_url)
                            response.raise_for_status()
                            safe_filename = "".join([c for c in album_name if c.isalnum() or c in (' ', '-')]).rstrip()
                            output_path = os.path.join(OUTPUT_DIR, f"{safe_filename}.jpg")
                            with open(output_path, 'wb') as f:
                                f.write(response.content)

                            downloaded_album_ids.add(album_id)
                            print(f"\r  Downloaded: {len(downloaded_album_ids)}/{TARGET_COVERS} ({album_name})", end="")

                        except requests.exceptions.RequestException:
                            pass
                offset += 50
        except Exception as e:
            print(f"An error occurred for artist {artist_name}: {e}")

    print(f"\n\nDownload complete. Found {len(downloaded_album_ids)} unique album covers in '{OUTPUT_DIR}'.")
