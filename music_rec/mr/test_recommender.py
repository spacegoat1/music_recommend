# Execute test in Django shell
from mr.recommender import *
from mr.models import *
import random

# We want to test whether when a track is liked/listened through:
# 1. Does its weight increase?
# 2. Do the weights of tracks associated with its album increase?
# 3. Do the weights of tracks associated with its artist increase?
# 4. Do the weights of tracks associated with its genre increase?
# 5. Do the weights of tracks NOT associated with the track decrease? (They should, to satisfy #6)
# 6. Does the overall sum of all weights before and after stay the same?
# When a track is disliked/skipped, we expect the opposite

def test_weight_update():
    user = User.objects.first()
    user_recommender = load_recommender(user)

    random_track = Track.objects.get(id=random.choice(list(Track.objects.all().values_list('pk', flat=True))))
    album_tracks = Track.objects.filter(id__in=Track.objects.filter(album=random_track.album))\
        .exclude(id=random_track.id)\
        .values_list('id', flat=True)
    artist_tracks = Track.objects.filter(id__in=Track.objects.filter(album__artist=random_track.album.artist))\
        .exclude(id__in=album_tracks)\
        .exclude(id=random_track.id)\
        .values_list('id', flat=True)
    genre_tracks = Track.objects.filter(id__in=Track.objects.filter(genre=random_track.genre))\
        .exclude(id__in=album_tracks)\
        .exclude(id__in=artist_tracks)\
        .exclude(id=random_track.id)\
        .values_list('id', flat=True)
    other_tracks = Track.objects.exclude(id=random_track.id)\
                                .exclude(id__in=album_tracks)\
                                .exclude(id__in=artist_tracks)\
                                .exclude(id__in=genre_tracks)

    weights_before = {
        'track': TrackWeight.objects.filter(track_id__in=[random_track.id]).aggregate(Sum('weight'))['weight__sum'],
        'album': TrackWeight.objects.filter(track_id__in=album_tracks).aggregate(Sum('weight'))['weight__sum'],
        'artist': TrackWeight.objects.filter(track_id__in=artist_tracks).aggregate(Sum('weight'))['weight__sum'],
        'genre': TrackWeight.objects.filter(track_id__in=genre_tracks).aggregate(Sum('weight'))['weight__sum'],
        'other': TrackWeight.objects.filter(track_id__in=other_tracks).aggregate(Sum('weight'))['weight__sum'],
    }

    # Quick check to see whether the sets are being selected correction
    assert(len(album_tracks) + len(artist_tracks) + len(genre_tracks) + len(other_tracks) + 1 == Track.objects.all().count(),
            "Track counts not adding up!")

    # Perform like/listen_through
    action = random.choice(["like", "listen_through", "dislike", "skip"])
    # action = "dislike"
    user_recommender.update_weights(action, random_track.id)

    # Weights after update
    weights_after = {
        'track': TrackWeight.objects.filter(track_id__in=[random_track.id]).aggregate(Sum('weight'))['weight__sum'],
        'album': TrackWeight.objects.filter(track_id__in=album_tracks).aggregate(Sum('weight'))['weight__sum'],
        'artist': TrackWeight.objects.filter(track_id__in=artist_tracks).aggregate(Sum('weight'))['weight__sum'],
        'genre': TrackWeight.objects.filter(track_id__in=genre_tracks).aggregate(Sum('weight'))['weight__sum'],
        'other': TrackWeight.objects.filter(track_id__in=other_tracks).aggregate(Sum('weight'))['weight__sum'],
    }

    # Now check
    print("Action: ", action)
    for k in weights_after.keys():
        if weights_after[k] is not None:
            print(f"{k} -> {weights_after[k] / weights_before[k]}")

