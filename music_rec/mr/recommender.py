from mr.models import *
from collections import deque
import pandas as pd
import numpy as np
from django.contrib.auth.models import User
from numpy.random import choice
import pickle
from pathlib import Path
import os
from django.db.models import Sum, F


BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = os.path.join(os.path.join(BASE_DIR,'music_rec'),'tmp')

def load_recommender(user):
    try:
        # Load recommender from history (saved to disk)
        file_name = str(TMP_DIR) + "/" + str(user.id) + ".pkl"
        with open(file_name, 'rb') as pickle_file:
            r = pickle.load(pickle_file)
        return r
    except:
        # The user does not have an existing recommender object
        return Recommender(user)

# Calculation of parameters for models
RECOMMENDER_PARAMETERS = {
    'max_ratio': 50,
    'points_per_song_default': 10000,
    'deque_length': 5,
    'track_count': Track.objects.all().count(),
    'alpha_track': 0.3, # how much to update the track weight by, like a learning rate
    'alpha_album': 0.2, # how much to update the album weight by, like a learning rate
    'alpha_artist': 0.15, # how much to update the artist weight by, like a learning rate
    'alpha_genre': 0.25 , # how much to update the genre weight by, like a learning rate
    'decay_factor': 0.99,
}

MIN_POSSIBLE_WEIGHT = \
    (2 * RECOMMENDER_PARAMETERS["points_per_song_default"]) / \
        (1 + RECOMMENDER_PARAMETERS["max_ratio"])

MAX_POSSIBLE_WEIGHT = \
    (2 * RECOMMENDER_PARAMETERS["points_per_song_default"]) * \
        (RECOMMENDER_PARAMETERS["max_ratio"] / (1 + RECOMMENDER_PARAMETERS["max_ratio"]))

ACTION_CONSEQUENCES = {
            'like': 'up',
            'dislike': 'down',
            'skip': 'down',
            'listen_through': 'up',
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
        self.track_count = RECOMMENDER_PARAMETERS['track_count'] # No of tracks in DB

        # discount controls how much the new evidence updates existing weights. 
        # The idea is, when we have little information, we should update the weights more
        # However, once we have already plenty of data, the evidence should update weights less
        # If we keep decaying the importance of new evidence, eventually weights will stop updating
        # Therefore, discount should be in the range (0.5, 1)
        self.discount = 1.0 

        self.user = user if user else User.objects.get(id=1) # assuming a single user!
        # user = user if user else User.objects.get(id=1) # assuming a single user!

        if reset:
            # No historical weights implies that we have no evidence of user preferences -> assume flat prior
            weight = self.track_count
            TrackWeight.objects.filter(user=self.user).update(weight=weight)
        
        # Now set the current distribution over tracks
        self.current_distribution = TrackWeight.objects.filter(user=self.user).values_list("track", "weight")

    def sample(self):
        # Pick the next song to play depending on distribution, exclude the cache of recent songs
        curr_track_weights = \
            np.array(TrackWeight.objects.filter(user=self.user).exclude(track_id__in=self.last_played)\
                .values_list("track_id", "weight").order_by("track_id")).T
        chosen_track = int(choice(curr_track_weights[0,:], 
                            1, 
                            p=curr_track_weights[1,:]/np.sum(curr_track_weights[1,:]))[0])
        self.last_played.append(chosen_track)
        self.discount = max(0.5, self.discount*RECOMMENDER_PARAMETERS['decay_factor'])

        return chosen_track

    def get_new_weight(self, curr_total, num_tracks, alpha, direction):
        if num_tracks == 0:
            return 1, 0
        if direction == 'up':
            gap_above = (MAX_POSSIBLE_WEIGHT * num_tracks) - curr_total
            shift = gap_above * alpha * self.discount
            new_total = curr_total + shift
            move_factor = new_total / curr_total
        else:
            gap_below = curr_total - (MIN_POSSIBLE_WEIGHT * num_tracks)
            shift = gap_below * alpha * self.discount
            new_total = curr_total - shift
            move_factor = new_total / curr_total
            shift *= -1 # multiplying by -1 to signify downward shift
        return move_factor, shift

    def update_weights(self, action, track_id):
        # Update the weights for a user given a track and action
        # action can be one of ["like", "dislike", "skip", "listen_through", "ignored"]

        up_or_down = ACTION_CONSEQUENCES[action]
        if up_or_down is None:
            # No action to be taken (because the user ignored the track)
            return None

        # When an action is taken, the following weights need to be updated:
        # 1. track 2. album 3. artist 4. genre
        if track_id is None:
            # This should never happen
            return None
        track = Track.objects.get(id=track_id)
        track_weight = TrackWeight.objects.filter(track=track)
        track_weight_ids = track_weight.values_list("id")
        album_weights = TrackWeight.objects.filter(track__album=track.album).exclude(id__in=track_weight_ids)
        album_weights_ids = album_weights.values_list("id")
        artist_weights = TrackWeight.objects.filter(track__album__artist=track.album.artist)\
            .exclude(id__in=album_weights_ids).exclude(id__in=track_weight_ids)
        artist_weights_ids = artist_weights.values_list("id")
        genre_weights = TrackWeight.objects.filter(track__genre=track.genre)\
            .exclude(id__in=track_weight_ids)\
            .exclude(id__in=album_weights_ids)\
            .exclude(id__in=artist_weights_ids)
        
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
        remaining_tracks = TrackWeight.objects.exclude(id__in=track_weight_ids)\
                                            .exclude(id__in=album_weights_ids)\
                                            .exclude(id__in=artist_weights_ids)\
                                            .exclude(id__in=genre_weights.values_list("id"))
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

