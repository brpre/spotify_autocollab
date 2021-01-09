#!/usr/bin/env python
# coding: utf-8

# In[712]:


# get_ipython().system('pip install requests')


# In[713]:


import base64
import requests
import datetime
from urllib.parse import urlencode
import json


# In[714]:


client_id = '07c0678a19bd4663b42f1b8242d7154a'
client_secret = '03760c56d4074b14939929b018315280'


# In[715]:


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
        returns a base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
     
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization":f"Basic {client_creds_b64}"
        }
    
    def get_token_data(self):
        return {
            "grant_type":"client_credentials"
        }
    
    def perform_auth(self):
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


# In[716]:


spotify = SpotifyAPI(client_id, client_secret)
spotify.perform_auth()


# In[717]:


access_token = spotify.access_token


# In[718]:


# endpoint generator used to get list of playlist_id's for given user
def get_user_playlists_endpoint(user_id):
    # gets items list from paging obj, gets playlist_id's from each item
    # note: wrapped in a paging object 
    return f"https://api.spotify.com/v1/users/{user_id}/playlists?limit=50&fields=items(id)"

# endpoint generator used to get list of track objects for given playlist
def get_playlist_tracks_endpoint(playlist_id):
    # gets items list from paging obj
    return f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items"

# given csv string of track Spotify IDs
def get_tracks_endpoint(tracks_str):
    return f"https://api.spotify.com/v1/tracks?ids={tracks_str}"


# In[723]:


import collections

headers = {
    "Authorization": f"Bearer {access_token}"
}

# TODO main function that checks each username passed in argv for validity via user request
# responds if username is invalid, and makes a list of valid usernames, passes to find_overlap(list)

import sys

user_list = []

for i in range(1, len(sys.argv)):
    user_id = sys.argv[i]
    ureq = requests.get(f"https://api.spotify.com/v1/users/{user_id}", headers=headers)
    if ureq.status_code != 200:
        sys.exit(f"{user_id} is an invalid username. Please try again")
    else:
        user_list.append(user_id)


# takes list of users, returns array of track objects (in json probably)
# prints the tracks as a temporary result display because meh printing lists
def find_overlap(users):
    
    counter = collections.Counter()
    
    print("Auto-generating playlist for users: " + ", ".join(users))
    for user in users:
        # get json list of this user's playlists' playlist_id's
        # TODO CATCH EXCEPTION THAT BELOW LINE THROWS IF BAD USERNAME
        user_playlists_endpoint = get_user_playlists_endpoint(user)
        # get /users/{user_id}/playlists?limit=50&fields=items(id)"
        # and pass access token contained in header
        # request a json list of playlist_id's
        user_req_data = requests.get(user_playlists_endpoint, headers=headers)
        # call function that gets all songs user has in their playlists
        user_tracks = get_tracks(user_req_data)
        # print("Num tracks for user: " + str(len(user_tracks)))
        counter.update(user_tracks)

    overlap = { k: v for k, v in counter.items() if v >= len(users) }
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
        tracks_endpoint = get_tracks_endpoint(sublist_str)
        sublist_req = requests.get(tracks_endpoint, headers=headers)
        orjson = sublist_req.json().get('tracks')
        if orjson == None:
            break
            # TODO i need to handle the None case even if code works. make sure to
        for track in orjson:
            print(track.get('name'))
            overlapping_tracks.add(track.get('name'))
    
    return overlapping_tracks


# given user request, compiles a SET of tracks user has in public playlists        
def get_tracks(user_request_data):        
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
                playlist_tracks_endpoint = get_playlist_tracks_endpoint(playlist_id)
                # request a playlist object, metadata and json list of track_id's
                playlist_req_data = requests.get(playlist_tracks_endpoint, headers=headers)
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


# In[725]:


# WORKING CALLS 
# user_list = ["brenderman3", "briannannaj", "mattp0irier"]
# user_list = ["brenderman3", "ssumana11", "gigi.a"]
# user_list = ["mattp0irier", "brenderman3"]
# user_list = ["ssumana11", "soj6a61491y4so06b5krmkzw6"]
# user_list = ["nerds227", "gigi.a"]  

# user_list = ["mattp0irier", "brenderman3"]

# BROKEN CALLS






find_overlap(user_list)


# In[ ]:




