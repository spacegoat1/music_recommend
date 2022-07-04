from django.db import models
from django.db.models import CASCADE, SET_NULL

# Create your models here.

"""
Simplifying assumptions:
1. Each album is recorded by a unique artist
2. Each track belongs to a unique album
3. Each track belongs to a unique genre
"""

class Artist(models.Model):
    """
    Artist model
    """
    id = models.AutoField(primary_key=True)
    artist_name = models.CharField(max_length=200, unique=True)


class Album(models.Model):
    """
    Album model
    """
    id = models.AutoField(primary_key=True)
    album_title = models.CharField(max_length=400, unique=True)
    artist = models.ForeignKey(to=Artist, on_delete=CASCADE)


class Genre(models.Model):
    """
    Genre model
    """
    id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=400, unique=True)


class Track(models.Model):
    """
    Model representing tracks
    """
    id = models.AutoField(primary_key=True)
    track_id = models.IntegerField() # From raw data
    track_title = models.CharField(max_length=500) # not unique!
    album = models.ForeignKey(to=Album, on_delete=CASCADE)
    genre = models.ForeignKey(to=Genre, on_delete=CASCADE)
