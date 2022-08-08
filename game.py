import os
import json
import random
import datetime
import urllib
import spotipy
import deezer

from pydub import AudioSegment
from spotipy.oauth2 import SpotifyClientCredentials
from song import Song


PLAYLIST_ID = "5q8lwvarxPFAj1Hfj18h7q"
START_DATE = datetime.datetime(2022, 8, 7)
SEC_STEPS = [1, 2, 4, 7, 11, 16, 30]


class Game:
    def __init__(self) -> None:
        self.game_num = (datetime.datetime.today() - START_DATE).days + 1
        self.today_song = None

        tracks = self.get_all_tracks()
        self.all_songs = []
        for track in tracks:
            name = track["track"]["name"]
            if "-" in name:
                name = "-".join(name.split("-")[:-1]).strip()
            artist = track["track"]["artists"][0]["name"]
            id_ = track["track"]["id"]

            song = Song(name, artist, id_, None)
            self.all_songs.append(song)

        self.all_songs.sort(key=lambda song: song.artist)

    def get_all_tracks(self) -> list[dict]:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            os.environ["SPOTIFY_CLIENT_ID"],
            os.environ["SPOTIFY_CLIENT_SECRET"],
        ))

        results = sp.playlist_tracks(PLAYLIST_ID, fields="items,next")
        tracks = results["items"]
        while results["next"]:
            results = sp.next(results)
            tracks += results["items"]

        return tracks

    def get_used_song_ids(self) -> list[str]:
        if not os.path.exists("used-songs.csv"):
            return []

        with open("used-songs.csv", "r") as f:
            ids = f.read().split(",")

        return ids

    def save_song_as_used(self, song: Song) -> None:
        with open("used-songs.csv", "a+") as f:
            f.write(f"{song.id},")

    def get_unused_songs(self) -> list[Song]:
        used_ids = self.get_used_song_ids()
        songs = [song for song in self.all_songs if song.id not in used_ids]

        return songs

    def choose_new_song(self) -> Song:
        available_songs = self.get_unused_songs()
        song = random.choice(available_songs)

        return song

    def get_song_deezer_url(self, song: Song) -> str:
        client = deezer.Client()
        results = list(client.search(f"{song.name} {song.artist}"))

        return results[0].preview

    def save_song_snippets(self, song: Song) -> None:
        if not os.path.isdir("static/song-snippets"):
            os.mkdir("static/song-snippets")

        url = self.get_song_deezer_url(song)
        urllib.request.urlretrieve(url, "static/song-snippets/song.mp3")
        audio = AudioSegment.from_mp3("static/song-snippets/song.mp3")

        for i in SEC_STEPS[:-1]:
            snip = audio[:1000 * i]
            snip.export(f"static/song-snippets/snip-{i}.mp3", format="mp3")

    def get_today_song(self) -> Song:
        today = datetime.datetime.today().strftime("%Y%m%d")

        if not os.path.exists("song.json"):
            with open("song.json", "w+") as f:
                json.dump(Song("", "", "", "").__dict__, f, indent=4)

            with open("log.txt", "a+") as f:
                f.write(f"{datetime.datetime.now()}: created new song.json\n")

        with open("song.json", "r") as f:
            song = json.load(f)
        song = Song(*song.values())

        if song.date != today:
            while True:
                song = self.choose_new_song()
                try:
                    self.save_song_snippets(song)
                    break
                except urllib.error.URLError:
                    pass

            song.date = today
            with open("song.json", "w") as f:
                json.dump(song.__dict__, f, indent=4)

            self.save_song_as_used(song)

            with open("log.txt", "a+") as f:
                f.write(f"{datetime.datetime.now()}: got new song {str(song)}\n")

            return song
        return song

    def update(self) -> None:
        self.today_song = self.get_today_song()
