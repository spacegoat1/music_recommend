from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from mr.models import *
from mr.recommender import *


# Create your views here.

# create a function
def recommender_view(request):

    print("In recommender_view")
    songs = Track.objects.annotate().all()[:20]
    context ={
        "data":"Gfg is the best",
        "list":songs
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)


# create a function
def trial(request):

    print("In trial")
    songs = Track.objects.annotate().all()[:20]
    context ={
        "data":"Gfg is the best",
        "list":songs
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)




def index(request):
    songs = Track.objects.annotate().all()[:20]
    users = User.objects.annotate().all()
    current_track_id = 420
    print("In INDEX", current_track_id)
    context = {
        "data": "Gfg is the best",
        "list": songs,
        "users": users,
        "current_track_id": current_track_id,
    }
    # return response with template and context
    # print(request)
    # print(request.GET)
    # print(request.POST)
    # print(type(request))
    # post = request.POST.copy()
    # print(type(request['session']))
    # post['field'] = 'test persistent variable'
    # request.POST = post
    
    user = User.objects.first()
    user_recommender = Recommender(user)
    print(vars(user_recommender))
    sampled_song = user_recommender.sample()
    print("sampled_song", sampled_song)
    print(vars(user_recommender))
    user_recommender.save()
    return render(request, "recommender_template.html", context)

def like(request):
    songs = Track.objects.annotate().all()[:20]
    users = User.objects.annotate().all()
    user = User.objects.first()
    user_recommender = load_recommender(user)
    track_id = 400
    user_recommender.update_weights(track_id, "like")
    context = {
        "data": "Gfg is not the best",
        "list": songs,
        "users": users,
        "current_track_id": 100,
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)

def dislike(request):
    songs = Track.objects.annotate().all()[:20]
    users = User.objects.annotate().all()
    context = {
        "data": "Gfg is not the best",
        "list": songs,
        "users": users,
        "current_track_id": 200,
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)

def skip(request):
    songs = Track.objects.annotate().all()[:20]
    users = User.objects.annotate().all()
    context = {
        "data": "Gfg is not the best",
        "list": songs,
        "users": users,
        "current_track_id": 300,
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)

def listen_through(request):
    songs = Track.objects.annotate().all()[:20]
    users = User.objects.annotate().all()
    context = {
        "data": "Gfg is not the best",
        "list": songs,
        "users": users,
        "current_track_id": 300,
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)

def ignore(request):
    songs = Track.objects.annotate().all()[:20]
    users = User.objects.annotate().all()
    context = {
        "data": "Gfg is not the best",
        "list": songs,
        "users": users,
        "current_track_id": 300,
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)

def detail(request, user_id):
    # Load most recent listen history for user
    # Return some basic analytics of what they have listened to (favorite songs, favorite album, genre, artist)
    user = get_object_or_404(User, pk=user_id)
    return render(request, 'user_template.html', {'user': user})

