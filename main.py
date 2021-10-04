import requests
import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
from personal_info import user_id, spotify_token
class playlist:

    

    def __init__(self):
        self.yt_user = self.get_yt_user()
        self.song_info = {}

    def create_spotify_playlist(self):
        api_url = "https://api.spotify.com/v1/users/{}/playlists".format(user_id)
        data = {
        "name": "Youtube Likes",
        "description": "description",
        "public": True
        }
        headers = {"Content-Type":"application/json",
                "Authorization": "Bearer {}".format(spotify_token)}
        
        response = requests.post(api_url, data=json.dumps(data), headers=headers)
        print(response.status_code)
        response_json = response.json()
        
        # return playlist id
        return response_json["id"]

    def get_yt_user(self):
        
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "code_secret_client.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        yt_user = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)
        

        request = yt_user.videos().list(
            part="snippet,contentDetails",
            
            myRating="like"
            
        )
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
               item["id"])


            # use youtube_dl to collect the song name & artist name
            download = False 
            ydl_opts = {
                'outtmpl': '%(id)s%(ext)s',     
                'writesubtitles': True,
                'format': 'mp4',
                'writethumbnail': True
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                video = ydl.extract_info(youtube_url, download)

            song = video["track"]
            artist = video["artist"]
            

            if song is not None and artist is not None:
                # save all important info and skip any missing song and artist
                self.song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.get_song_uri(song, artist)

                }
                


    def get_song_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=1".format(
            song_name,
            artist
        )

        headers = {"Content-Type":"application/json",
                    "Authorization": "Bearer {}".format(spotify_token)}

        response = requests.get(query,  headers=headers)

        response_json = response.json()
        songs = response_json["tracks"]["items"]

                # only use the first song
        uri = songs["uri"]

        return uri

    def add_songs_to_spotify(self):
        self.get_yt_user()
        uris = [info["spotify_uri"]
                for song, info in self.song_info.items()]   

        playlist_id = self.create_spotify_playlist()
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        headers = {"Content-Type":"application/json",
                "Authorization": "Bearer {}".format(spotify_token)}
        data ={}

        #response = requests.get(query)
        response = requests.post(query, data=request_data, headers=headers)
        print(response.status_code)
        response_json = response.json()
        return response_json
        


if __name__ == "__main__":
    x = playlist()
    x.add_songs_to_spotify()