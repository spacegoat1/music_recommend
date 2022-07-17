"""music_rec URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
# importing views from views..py
# from mr.views import recommender_view, trial
from mr import views


# from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # ex: /polls/
    # path('', views.index, name='index'),
    # ex: /polls/5/
    # path('<int:user_id>/', views.detail, name='detail'),
    # ex: /polls/5/results/
    # path('<int:user_id>/results/', views.results, name='results'),
    # ex: /polls/5/vote/
    # path('<int:track_id>/like/', views.like, name='like'),
    # path('<int:track_id>/dislike/', views.dislike, name='dislike'),
    # path('<int:track_id>/skip/', views.skip, name='skip'),
    path('', views.track_action, name='track-action'),
]
