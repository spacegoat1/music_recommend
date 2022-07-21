import pandas as pd
import numpy as np
import ast
from mr.models import *
from django.db.models import F

def get_genre(x):
    try:
        return ast.literal_eval(x)[0]["genre_title"]
    except:
        return np.nan

tracks_raw = pd.read_csv("/home/yash/Desktop/Misc/music_recommend/raw_tracks.csv")
tracks_raw = tracks_raw[['track_id', 'track_title', 'album_title', 'artist_name', 'track_genres']]

# Assume that each track belongs to a single genre -> just taking the first genre listed
tracks_raw['genre_norm'] = tracks_raw['track_genres'].apply(lambda x: get_genre(x))

# dropping any records with missing data for convenience
tracks_raw = tracks_raw.dropna(how='any')

tracks_raw = tracks_raw[['track_id', 'track_title', 'album_title', 'artist_name', 'genre_norm']]

# Break data up to match models layout

# First populate artists, then albums, then genres, then tracks
artists = sorted(tracks_raw.artist_name.unique())
for artist in artists:
    Artist.objects.create(artist_name=artist)


# Populate albums
artists_data = pd.DataFrame.from_records(Artist.objects.all().values())
albums = tracks_raw[['artist_name', 'album_title']].sort_values('album_title').drop_duplicates('album_title', keep='first')
albums = albums.merge(artists_data, how='left')[['album_title', 'id']]

for i, r in albums.iterrows():
    Album.objects.create(album_title=r['album_title'], artist_id=r['id'])


# Populate genres
genres = sorted(tracks_raw.genre_norm.unique())
for genre in genres:
    Genre.objects.create(genre_name=genre)


# Populate tracks
albums_data = pd.DataFrame.from_records(Album.objects.annotate(album_id=F('id')).all().values("album_id", "album_title"))
genres_data = pd.DataFrame.from_records(Genre.objects.annotate(genre_id=F('id')).all().values("genre_id", "genre_name"))

tracks = tracks_raw[['track_id', 'track_title', 'album_title', 'genre_norm']]
tracks = tracks.merge(albums_data, how='left')
tracks = tracks.merge(genres_data, how='left', left_on='genre_norm', right_on='genre_name')

for i, r in tracks.iterrows():
    Track.objects.create(track_id=r['track_id'], 
                        track_title=r['track_title'],
                        album_id=r['album_id'],
                        genre_id=r['genre_id'])

