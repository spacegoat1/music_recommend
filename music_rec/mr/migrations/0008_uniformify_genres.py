from django.db import migrations
import numpy as np


def forwards_func(apps, schema_editor):

    Track = apps.get_model("mr", "Track")
    Album = apps.get_model("mr", "Album")
    Artist = apps.get_model("mr", "Artist")
    Genre = apps.get_model("mr", "Genre")
    TrackWeight = apps.get_model("mr", "TrackWeight")

    # keep only the first 20 genres
    current_genres = np.array(Genre.objects.all().values_list('id', flat=True))
    num_genres_to_keep = 20
    genres_to_keep = current_genres[:num_genres_to_keep]
    genres_to_drop = current_genres[num_genres_to_keep:]

    # assign existing tracks to those genres at random
    current_tracks = list(Track.objects.all().values_list('id', flat=True))
    num_tracks_per_genre = int(np.floor(len(current_tracks) / num_genres_to_keep))
    
    for ix, g in enumerate(genres_to_keep):
        tracks_for_genre = current_tracks[num_tracks_per_genre*ix:num_tracks_per_genre*(ix+1)]
        genre_tracks = Track.objects.filter(id__in=tracks_for_genre)
        genre_tracks.update(genre_id=g)
        # genre_tracks.save()

    # assign the remaining tracks to a random genre
    remaining_tracks = current_tracks[num_tracks_per_genre*len(genres_to_keep):]
    genre_tracks = Track.objects.filter(id__in=remaining_tracks)
    genre_tracks.update(genre_id=genres_to_keep[0])

    # delete the remaining genres
    Genre.objects.filter(id__in=genres_to_drop).delete()

    # Resetting all track weights to start weight
    tracks = TrackWeight.objects.all()
    tracks.update(weight=10000.0)
    # tracks.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mr', '0007_listenhistory_user_trackweight_user'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
