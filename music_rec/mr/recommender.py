from mr.models import *
from collections import deque
import pandas as pd
import numpy as np


class Recommender:
    """
    A class for the recommendation system.
    In theory, it should accept the ListenHistory data as input and return a distribution over tracks as output. 
    This implementation will likely just do individual updates (accept track id, event and update the TrackWeight table)
    """

    def __init__(self, reset=False):
        # tracks = Track.objects.all()
        self.last_5 = deque(5*[None], 5)
        self.track_count = Track.objects.all().count()

        if reset:
            # No historical weights implies that we have no evidence of user preferences -> assume flat prior
            weight = self.track_count
            TrackWeight.objects.all.update(weight=weight)
        
        # Now set the current distribution over tracks
        self.current_distribution = TrackWeight.objects.all().values_list("track", "weight")

    def sample(self):
        # Pick the next song to play depending on distribution
