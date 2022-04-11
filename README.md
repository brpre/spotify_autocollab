# spotify_autocollab : a recommender system for Spotify

## see ac_detailed_summary.ipynb for more information on all of the below

TL;DR Two implementations:
1. Blends, but naive and before they were cool - pass spotify usernames and it will generate a list of songs that everyone enjoys (inefficient and old, from when I was teaching myself python)
  a. collects a set of songs each given user has in their public playlists via the Spotify API
  b. inefficiently gets set intersection of user sets, outputs list
  
2. a simple recommender system that uses a combination of collaborative filtering and content-based filtering - pass a target user and a list of their friends to get song recommendations for the target user
  a. get recommendation candidates - collects friend user's public playlists and their songs, aggregates them into a set. implicit collaborative filtering, using friends as candidate generators
  b. encode recommendation candidates - uses object embeddings in a vector space of song attributes / audio feature data
  c. understand user preference - get target user's playlists and songs, generate corresponding object embeddings, cluster and export cluster centroids
  d. content-based filtering in a space of collaboratively generated candidates - using target user centroid as query embeddings, get kNN from candidate dataset for each centroid

Contributors
- prestage.b@northeastern.edu
- massud.e@northeastern.edu

# What is autocollab for Spotify?

We built a Spotify song recommendation system by collecting public user data from Spotify's API for a target user and their friends. The recommender uses the audio features of songs provided by Spotify's API (ex. acousticness, tempo, danceability, etc) to recommend songs from the friends' playlists to the target user. The recommender [groups](#Clustering) the target user's songs and [finds similar songs](#Recommending) in the friends' songs. Our recommender system does a good job [if some assumptions hold](#Assumptions), but results may vary if the target user doesn't have preferences we can detect (i.e. a distinct group or groups), friend data is wildly different from the target user, or the amount of data given to the system is too small.

# Ethical Considerations

Because our tool recommends songs, it comes with the same bias-oriented ethical considerations that other recommender systems have. Our system pulls recommendation candidates from songs found in playlists saved by a manually specified list of users. Because the content of these playlists is not controlled, there may be strong bias towards certain artists, studios, or genres, putting artists and genres outside of the candidate pool at a disadvantage. Our system only allows users to discover new music that their friends have already discovered, so the recommendations could harm new artists, preventing them from being discovered. Our system risks popular artists getting more popular and undiscovered artists never getting discovered. **We suggest that any product derived from this work integrate randomly sampled songs from Spotify into its candidate pool to establish some equity across music producers and genres.** See [freshness, diversity, and fairness in recommendation systems](https://developers.google.com/machine-learning/recommendation/dnn/re-ranking)

# Introduction

Many people struggle to find new music that they enjoy, especially on a platform as massive as Spotify. The problem lies in "candidate generation", i.e. finding songs that are worth considering. Music listeners often turn to Spotify's auto-generated Daily Mix and Discover Weekly playlists, but many agree that the best music recommendations come from their friends. Getting music from friends manually is difficult, requiring listening to the songs to make decisions, and finding commonalities can take a long time. **The goal of this project is to automate the process of getting music recommendations from your friends. Rather than having a specific song, album, or artist explicitly recommended between friends, our project aims to recommend new songs to a user based on their preferences, using their friends' public playlists as the candidate pool.**

# Data Description

(Full details of songs data and some cool visualizations can be found in `pipeline_and_visualizations.ipynb`, a summary of the relevant details is given here).

Our data is collected from each user's public playlists via the Spotify API, and the audio features are produced by Spotify. The audio features are used for our embedding space in which songs and queries exist as vectors.

To collect our data, we requested public playlist data for the given user and specified friends from the [Spotify API](https://developer.spotify.com/documentation/web-api/reference/). We then aggregated this data and requested [audio feature data](https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-audio-features) for each track to use as our "[embedding](https://developers.google.com/machine-learning/glossary#embeddings)" in the embedding space, which will be used for recommendations.

# Method

To recommend songs to users, we used a two step process.

1. We used k-Means Clustering on the target user's songs to get an abstract representation of user preferences. We used the centroids as ['query embeddings'](https://developers.google.com/machine-learning/recommendation/dnn/retrieval) which we used to generate recommendations.

2. We applied k-Nearest Neighbors to find which of the friends' songs are closest to this user's centroids. For each centroid, the k-nearest songs were recommended.

In essence, we conceptualize user preference with clusters, and then recommend songs from the friends dataset based on their distance to the nearest centroid. Using friends data via a ['social graph'](https://developers.google.com/machine-learning/recommendation/dnn/scoring) is a common source for candidate generation in contemporary recommendation systems.
