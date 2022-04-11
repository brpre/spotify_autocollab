#!/usr/bin/env python

# get_ipython().system('pip install requests')

import base64
import requests
import datetime
from urllib.parse import urlencode
import json
import collections
import sys

# auth code borrowed with variations from github.com/codingforentrepreneurs/30-Days-of-Python Day 19
class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"

    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        
    def get_client_credentials(self):
        """
        gets the client credientials for authenticating with the Web API

        :return: json representing the authorization header client_creds_b64 (base64 encoded string)
                 client credientials in API's preferred form
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
     
    def get_token_headers(self):
        """
        creates and returns the json header of the creds that are sent to API

        :return: json representing the authorization header
        """
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization":f"Basic {client_creds_b64}"
        }
    
    def get_token_data(self):
        """
        produces token data in useful form

        :return:  json/dict/thing with grant type and credentials
        """
        return {
            "grant_type":"client_credentials"
        }
    
    def perform_auth(self):
        """
        performs a post request, updates access token and token expiration

        :return: True if auth was successful
        """
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in'] # in unit seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True    

    def get_access_token(self):
        """
        generates and returns the access token, calling auth function if existing access token is expired

        :return: the access token
        """
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token() 
        return token

    # above method replaces two below lines
    # spotify = SpotifyAPI(client_id, client_secret)
    # spotify.perform_auth()

    # To get something, you need its type (user, playlist, etc), its Spotify ID, and the correct string formatting

    def get_user_playlists_endpoint(self, user_id):
        """
        endpoint generator used to get list of playlist objects for given user. This function gets the URL,
        simplification to playlist_id's happens elsewhere

        :param user_id: base 62 identifier found at end of spotify URI, unique to each user
        :return: fstring url, used to get user's playlists
        """
        # suffix of URL: gets items list from paging obj, gets playlist_id's from each item
        # note: wrapped in a paging object i think
        return f"https://api.spotify.com/v1/users/{user_id}/playlists?limit=50&fields=items(id)"


    def get_playlist_tracks_endpoint(self, playlist_id):
        """
        endpoint generator used to get list of track objects for given playlist

        :param playlist_id: base 62 identifier found at end of spotify URI, unique to each playlist
        :return: fstring url used to get a list of track objects for given playlist
        """
        # gets items list from paging obj
        return f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items"

    def get_tracks_endpoint(self, tracks_str):
        """
        produces a url endpoint to retrieve a list of tracks, supplied as a comma separated list of Spotify IDs

        :param tracks_str: a comma separated list of Spotify IDs that point to tracks
        :return: fstring url used to get list of track objects
        """
        return f"https://api.spotify.com/v1/tracks?ids={tracks_str}"

    # TODO things were buggy until i added a global copy of headers. this isn't ideal, fix it
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    """
    access_token = spotify.access_token
    """

    def get_resource_header(self):
        """
        retrieves current access token, formats it in json dict pair thing

        :return: json header for authorized requests
        """
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers

    # headers = self.get_resource_header()

    # TODO main function that checks each username passed in argv for validity via user request
    # note: this can be done in find_overlap()

    """
    this part is if you want to run the code from command line, verifies the usernames supplied are valid
    TODO figure out how to do this same verification elsewhere
    
        user_list = []
    
        for i in range(1, len(sys.argv)):
            user_id = sys.argv[i]
            ureq = requests.get(f"https://api.spotify.com/v1/users/{user_id}", headers=headers)
            if ureq.status_code != 200:
                sys.exit(f"{user_id} is an invalid username. Please try again")
            else:
                user_list.append(user_id)
    """

    # takes list of users, returns array of track objects (in json probably)
    # prints the tracks as a temporary result display because meh printing lists
    def find_overlap(self, user_list):
        """
        Finds the "overlap" between users in user_list, current impl checks all public playlistd each user has saved,
        creates a set of tracks for each user (no repeats) adds all tracks from all user sets to a counting dict
        and returns list of songs that occur in all users' tracksets

        :param user_list: list of Spotify account usernames (should be valid usernames but we check below)
        :return: array of track objects representing the songs user_list users have in common, (json array probably)
        """

        counter = collections.Counter()

        print("Auto-generating playlist for users: " + ", ".join(user_list))

        for user in user_list:
            # get json list of this user's playlists' playlist_id's
            # TODO CATCH EXCEPTION THAT BELOW LINE THROWS IF BAD USERNAME, try catch?
            #   responds if username is invalid, and makes a list of valid usernames
            # gets an endpoint for json list of playlist objects corresponding to this user's playlists
            user_playlists_endpoint = self.get_user_playlists_endpoint(user)
            # get request using user_playlists_endpoint, gets json list of playlist objects (this user's playlists)
            # impl of below: gets /users/{user_id}/playlists?limit=50&fields=items(id)", passes access token in header
            user_req_data = requests.get(user_playlists_endpoint, headers=self.get_resource_header())
            # call function that gets all songs user has in their playlists
            user_tracks = self.get_tracks(user_req_data)
            # update the counting dict to include entries and counts for this user's trackset
            counter.update(user_tracks)

        overlap = { k: v for k, v in counter.items() if v >= len(user_list) }
        print("Overlap size: " + str(len(overlap)))
        print("Songs that users will enjoy: \n\n")
        # at this point overlap is a dict of SpotifyID:numInstances (always num users)
        overlap = list(overlap)

        if len(overlap) == 0:
            """ TODO SOMEHOW THIS LINE IS UNREACHABLE. RUN SUMANA X VARSHINI"""
            print("sir. no overlap here")

        # split overlap list into chunks small enough for spotify api to accept
        split_overlap = [overlap[i:i + 25] for i in range(0, len(overlap), 25)]  


        overlapping_tracks = set()

        for sublist in split_overlap:
            sublist_str = ','.join(sublist)
            tracks_endpoint = self.get_tracks_endpoint(sublist_str)
            sublist_req = requests.get(tracks_endpoint, headers=self.get_resource_header())
            orjson = sublist_req.json().get('tracks')
            if orjson == None:
                break
                # TODO i need to handle the None case even if code works. make sure to
            for track in orjson:
                print(track.get('name'))
                overlapping_tracks.add(track.get('name'))

        return overlapping_tracks


# TODO move this function to above find overlap. make sure everything still works when you do
    def get_tracks(self, user_request_data):
        """
        given user request, compiles a SET of tracks user has across all their public playlists

        :param user_request_data: json list of playlist objects (representing this user's public playlists)
        :return: a set of tracks representing a user's entire public library with no repeats
        """
        paging_obj_dict = user_request_data.json() # json array of dicts wrapped in a paging object
        playlist_dict = paging_obj_dict.get('items') # json array of dicts

        track_set = set()

        if playlist_dict == None:
            print("welp. you gooned something up. if playlist_dict == None ")
        else:
            for playlist_id_dict in playlist_dict:
                playlist_id = playlist_id_dict.get('id') # playlist Spotify ID string
                # pass playlist_id to endpoint generator, get all songs in playlist
                # TODO CATCH EXCEPTION THAT BELOW LINE THROWS IF BAD PLAYLIST ID
                playlist_tracks_endpoint = self.get_playlist_tracks_endpoint(playlist_id)
                # request a playlist object, metadata and json list of track_id's
                playlist_req_data = requests.get(playlist_tracks_endpoint, headers=self.get_resource_header())
                playlist_paging_obj_dict = playlist_req_data.json()
                track_dict = playlist_paging_obj_dict.get('items')

                # get all tracks from this playlist
                for track in track_dict:
                    track_id = track.get('track').get('id')
                    track_set.add(track_id)

               # was kinda using this for load progress but i'm tired of it
               # print(len(track_set))

        # print("Num tracks for user: " + str(len(track_set)))
        return track_set


# WORKING CALLS 
# user_list = ["brenderman3", "briannannaj", "mattp0irier"]
# user_list = ["brenderman3", "ssumana11", "gigi.a"]
# user_list = ["mattp0irier", "brenderman3"]
# user_list = ["ssumana11", "soj6a61491y4so06b5krmkzw6"]
# user_list = ["nerds227", "gigi.a"]  

# user_list = ["mattp0irier", "brenderman3"]

# BROKEN CALLS


# find_overlap(user_list)