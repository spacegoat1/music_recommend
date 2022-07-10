from django.shortcuts import render
from django.http import HttpResponse
from mr.models import *

# Create your views here.



# create a function
def recommender_view(request):

    songs = Track.objects.annotate().all()[:20]
    context ={
        "data":"Gfg is the best",
        "list":songs
    }
    # return response with template and context
    return render(request, "recommender_template.html", context)
