from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from mr.models import *
from mr.recommender import *
from .forms import TrackForm
from mr.async_queue import *
from django.db.models import Max, Sum

# Create your views here.

def track_action(request):
    form = TrackForm(request.POST)
    action = request.POST.get('btn')
    user = User.objects.first()
    user_recommender = load_recommender(user)
    track_id = user_recommender.last_played[-1]

    return_new_track = False
    disable_like_dislike = False
    update_weights = True

    if action is None:
        # This is initial page load -> just sample a track, no weight updates needed
        return_new_track = True
    elif action == 'like':
        disable_like_dislike = True
    elif action == 'dislike':
        disable_like_dislike = True
    elif action == 'skip':
        return_new_track = True
    elif action == 'listen_through':
        return_new_track = True
    elif action == 'ignore':
        return_new_track = True

    if action in ["like", "dislike", "listen_through", "skip"]:
        track_lh = ListenHistory.objects.filter(user=user).order_by('-listen_time').first()
        if action == "like":
            track_lh.liked = True
        if action == "dislike":
            track_lh.disliked = True
        if action == "listen_through":
            track_lh.completed = True
            if track_lh.liked or track_lh.disliked:
                update_weights = False
        if action == "skip":
            track_lh.skipped = True
            if track_lh.liked or track_lh.disliked:
                update_weights = False
        track_lh.save()

    if return_new_track:
        sampled_track = Track.objects.get(pk=user_recommender.sample())
        # Add new track to listen history
        ListenHistory.objects.create(user=user, track=sampled_track)
    else:
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
    if action is not None and update_weights:
        async_processes(user_recommender, action, track_id)

    return render(request, 'track.html', {'form': form, 'track': track_details})


def analytics(request):
    # Load most recent listen history for user
    # Return some basic analytics of what they have listened to (favorite songs, favorite album, genre, artist)
    # No of tracks listened to, # of tracks liked, disliked, skipped

    # Note: These is just a tiny sample of the analytics that can be done based on listenhistory and current weights
    # These queries have not been optimized

    print("In detail")
    user = get_object_or_404(User, pk=1)
    ulh = ListenHistory.objects.filter(user=user)

    analytics = {
        'count': ulh.count(),
        'likes': ulh.filter(liked=True).count(),
        'dislikes': ulh.filter(disliked=True).count(),
        'skipped': ulh.count() - ulh.filter(completed=True).count(),
    }

    user_weights = TrackWeight.objects.filter(user=user)

    highest_wt = user_weights.aggregate(wt=Max('weight'))['wt']
    fav_track = user_weights.filter(weight=highest_wt)[0].track

    fav_album = user_weights.values('track__album').annotate(total_wt=Sum('weight')).order_by('-total_wt')[0]
    fav_artist = user_weights.values('track__album__artist').annotate(total_wt=Sum('weight')).order_by('-total_wt')[0]
    fav_genre = user_weights.values('track__genre', 'track__genre__genre_name').annotate(total_wt=Sum('weight')).order_by('-total_wt')[0]

    fav_track = {
        'track_title': fav_track.track_title,
        'track_album': fav_track.album.album_title,
        'track_artist': fav_track.album.artist.artist_name,
        'track_genre': fav_track.genre.genre_name,
    }

    o = Album.objects.get(id=fav_album['track__album'])
    fav_album = {
        'album': o.album_title,
        'album_artist': o.artist.artist_name,
    }

    o = Artist.objects.get(id=fav_artist['track__album__artist'])
    fav_artist = {
        'artist': o.artist_name,
    }

    o = Genre.objects.get(id=fav_genre['track__genre'])
    fav_genre = {
        'genre': o.genre_name,
    }

    favorites = {
        'track': fav_track,
        'album': fav_album,
        'artist': fav_artist,
        'genre': fav_genre,
    }

    return render(request, 'user_template.html', {'user': user, 
                                                'analytics': analytics,
                                                'favorites': favorites})


def genre_chart(request):
    
    labels = []
    data = []

    user = get_object_or_404(User, pk=1)
    genre_weights = TrackWeight.objects.filter(user=user).values('track__genre', 'track__genre__genre_name')\
                                .annotate(total_wt=Sum('weight')).order_by('track__genre__genre_name')
    for entry in genre_weights:
        labels.append(entry['track__genre__genre_name'])
        data.append(entry['total_wt'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

def artist_chart(request):
    
    labels = []
    data = []

    user = get_object_or_404(User, pk=1)
    artist_weights = TrackWeight.objects.filter(user=user).values('track__album__artist', 'track__album__artist__artist_name')\
                                .annotate(total_wt=Sum('weight')).order_by('track__album__artist__artist_name')
    for entry in artist_weights:
        labels.append(entry['track__album__artist__artist_name'])
        data.append(entry['total_wt'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })