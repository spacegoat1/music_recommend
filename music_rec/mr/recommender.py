from mr.models import *
from collections import deque
import pandas as pd
import numpy as np
from django.contrib.auth.models import User
from numpy.random import choice
import pickle
from pathlib import Path
import os
from django.db.models import Sum


BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = os.path.join(os.path.join(BASE_DIR,'music_rec'),'tmp')

def load_recommender(user):
    file_name = str(TMP_DIR) + "/" + str(user.id) + ".pkl"
    with open(file_name, 'rb') as pickle_file:
        r = pickle.load(pickle_file)
    return r

# Calculation of parameters for models
RECOMMENDER_PARAMETERS = {
    'max_ratio': 10,
    'points_per_song_default': 1000,
    'deque_length': 5,
    'track_count': Track.objects.all().count(),
    'alpha_track': 0.1, # how much to update the track weight by, like a learning rate
    'alpha_album': 0.08, # how much to update the album weight by, like a learning rate
    'alpha_artist': 0.06, # how much to update the artist weight by, like a learning rate
    'alpha_genre': 0.04, # how much to update the genre weight by, like a learning rate
}

MIN_POSSIBLE_WEIGHT = \
    (2 * RECOMMENDER_PARAMETERS['track_count'] * RECOMMENDER_PARAMETERS["points_per_song_default"]) / \
        (1 + RECOMMENDER_PARAMETERS["max_ratio"])

MAX_POSSIBLE_WEIGHT = \
    (2 * RECOMMENDER_PARAMETERS['track_count'] * RECOMMENDER_PARAMETERS["points_per_song_default"]) / \
        (RECOMMENDER_PARAMETERS["max_ratio"] / (1 + RECOMMENDER_PARAMETERS["max_ratio"]))

ACTION_CONSEQUENCES = {
            'like': 'up',
            'dislike': 'down',
            'skip': 'down',
            'listened_through': 'up',
            'ignored': None,
        }


class Recommender:
    """
    A class for the recommendation system.
    In theory, it should accept the ListenHistory data as input and return a distribution over tracks as output. 
    This implementation will likely just do individual updates (accept track id, event and update the TrackWeight table)
    """

    def __init__(self, user, reset=False):
        # tracks = Track.objects.all()
        self.last_played = deque(RECOMMENDER_PARAMETERS["deque_length"]*[None], 
                                RECOMMENDER_PARAMETERS["deque_length"])
        self.track_count = RECOMMENDER_PARAMETERS['track_count']
        self.user = user if user else User.objects.get(id=1) # assuming a single user!
        # user = user if user else User.objects.get(id=1) # assuming a single user!

        # TO BE DONE:
        # If the total points != (self.track_count * points_per_song_default), 
        #   this means that new songs have been added to the library or deleted from the library.
        #   We need to adjust TrackWeight accordingly to account for this. 
        #   This could be as simple as merely adding the points_per_song_default for each new track.
        #   In case of track deletions, merely scale TrackWeight down till the sums add up to the total?

        if reset:
            # No historical weights implies that we have no evidence of user preferences -> assume flat prior
            weight = self.track_count
            TrackWeight.objects.filter(user=self.user).update(weight=weight)
        
        # Now set the current distribution over tracks
        self.current_distribution = TrackWeight.objects.filter(user=self.user).values_list("track", "weight")

    def get_new_weight(self, curr_total, num_tracks, alpha, direction):
        if direction == 'up':
            gap_above = (MAX_POSSIBLE_WEIGHT * num_tracks) - curr_total
            shift = gap_above * alpha
            new_total = curr_total + shift
            move_factor = new_total / curr_total
        else:
            gap_below = curr_total - (MIN_POSSIBLE_WEIGHT * num_tracks)
            shift = gap_below * alpha
            new_total = curr_total - shift
            move_factor = new_total / curr_total
        return move_factor, shift

    def sample(self):
        # Pick the next song to play depending on distribution, exclude the cache of recent songs
        curr_track_weights = \
            np.array(TrackWeight.objects.filter(user=self.user).exclude(track_id__in=self.last_played)\
                .values_list("track_id", "weight").order_by("track_id")).T
        chosen_track = int(choice(curr_track_weights[0,:], 
                            1, 
                            p=curr_track_weights[1,:]/np.sum(curr_track_weights[1,:]))[0])
        self.last_played.append(chosen_track)
        return chosen_track

    def update_weights(self, track_id, action):
        # Update the weights for a user given a track and action
        # action can be one of ["like", "dislike", "skip", "listened_through", "ignored"]

        up_or_down = ACTION_CONSEQUENCES[action]
        if up_or_down is None:
            # No action to be taken (because the user ignored the track)
            return None

        # When an action is taken, the following weights need to be updated:
        # 1. track
        # 2. album
        # 3. artist
        # 4. genre
        # track_id = 100
        track = Track.objects.get(id=track_id)
        track_weight = TrackWeight.objects.filter(track=track)
        album_weights = TrackWeight.objects.filter(track__album=track.album).difference(track_weight)
        artist_weights = TrackWeight.objects.filter(track__album__artist=track.album.artist)\
            .difference(album_weights).difference(track_weight)
        genre_weights = TrackWeight.objects.filter(track__genre=track.genre).difference(track_weight)
        
        track_shift_factor, track_shift = self.get_new_weight(curr_total=track_weight.aggregate(Sum('weight'))['weight__sum'], 
                                                num_tracks=1,
                                                alpha=RECOMMENDER_PARAMETERS['alpha_track'],
                                                direction=up_or_down)

        album_shift_factor, album_shift = self.get_new_weight(curr_total=album_weights.aggregate(Sum('weight'))['weight__sum'], 
                                                num_tracks=album_weights.count(),
                                                alpha=RECOMMENDER_PARAMETERS['alpha_album'],
                                                direction=up_or_down)

        artist_shift_factor, artist_shift = self.get_new_weight(curr_total=artist_weights.aggregate(Sum('weight'))['weight__sum'], 
                                                num_tracks=artist_weights.count(),
                                                alpha=RECOMMENDER_PARAMETERS['alpha_artist'],
                                                direction=up_or_down)

        genre_shift_factor, genre_shift = self.get_new_weight(curr_total=genre_weights.aggregate(Sum('weight'))['weight__sum'], 
                                                num_tracks=genre_weights.count(),
                                                alpha=RECOMMENDER_PARAMETERS['alpha_genre'],
                                                direction=up_or_down)

        # The weights of all other tracks need to be moved in the opposite direction
        total_shift = track_shift + album_shift + artist_shift + genre_shift
        remaining_tracks = TrackWeight.objects.all()\
                                    .difference(track_weight)\
                                    .difference(album_weights)\
                                    .difference(artist_weights)\
                                    .difference(genre_weights)
        remaining_tracks_total_weight = remaining_tracks.aggregate(Sum('weight'))['weight__sum']
        remaining_tracks_shift_factor = (remaining_tracks_total_weight - total_shift) / remaining_tracks_total_weight

        # Update all the weights in the DB
        track_weight.update(weight=F('weight') * track_shift_factor)
        album_weights.update(weight=F('weight') * album_shift_factor)
        artist_weights.update(weight=F('weight') * artist_shift_factor)
        genre_weights.update(weight=F('weight') * genre_shift_factor)
        remaining_tracks.update(weight=F('weight') * remaining_tracks_shift_factor)

        # We assume that there are no rounding errors since weights are floats, not ints
        return None

    def save(self):
        file_name = str(TMP_DIR) + "/" + str(self.user.id) + ".pkl"
        with open(file_name, "wb") as f:
            pickle.dump(self, f)

