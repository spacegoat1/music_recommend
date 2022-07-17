from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from mr.models import *
from mr.recommender import *
from .forms import TrackForm
from mr.async_queue import *

# Create your views here.

def track_action(request):
    print("In track_action")
    print(request.POST.get('btn'))
    form = TrackForm(request.POST)

    action = request.POST.get('btn')

    user = User.objects.first()
    user_recommender = load_recommender(user)

    return_new_song = False
    disable_like_dislike = False

    if action is None:
        # This is initial page load -> just sample a track, no weight updates needed
        return_new_song = True
    elif action == 'like':
        disable_like_dislike = True
    elif action == 'dislike':
        disable_like_dislike = True
    elif action == 'skip':
        return_new_song = True
    elif action == 'listen_through':
        return_new_song = True
    elif action == 'ignore':
        return_new_song = True

    if action in ["like", "dislike", "listen_through"]:
        track_lh = ListenHistory.objects.filter(user=user).order_by('-listen_time').first()
        if action == "like":
            track_lh.liked=True
        if action == "dislike":
            track_lh.disliked=True
        if action == "listen_through":
            track_lh.completed=True
        track_lh.save()

    if return_new_song:
        sampled_track = Track.objects.get(pk=user_recommender.sample())
        # Add new track to listen history
        ListenHistory.objects.create(user=user, track=sampled_track)
    else:
        track_id = user_recommender.last_played[-1]
        sampled_track = Track.objects.get(pk=track_id)

    track_details = {
        'track_id': sampled_track.id,
        'track_title': sampled_track.track_title,
        'track_album': sampled_track.album.album_title,
        'track_artist': sampled_track.album.artist.artist_name,
        'track_genre': sampled_track.genre.genre_name,
        'disable': disable_like_dislike,
    }

    user_recommender.save()
    if action is not None:
        async_processes(user_recommender, action)

    return render(request, 'track.html', {'form': form, 'track': track_details})


def detail(request, user_id):
    # Load most recent listen history for user
    # Return some basic analytics of what they have listened to (favorite songs, favorite album, genre, artist)
    print("In detail")
    user = get_object_or_404(User, pk=user_id)
    return render(request, 'user_template.html', {'user': user})

