# music_recommend
Project to create DB of songs and make recommendations

Data taken from: https://github.com/mdeff/fma (fma_metadata.zip file -> raw_tracks.csv)

Check for frontend:
https://www.pluralsight.com/guides/introduction-to-django-templates
https://mkdev.me/posts/fundamentals-of-front-end-django

Questions:
1. Should history be saved? Seems like it should. Create a watch history table
2. How will the suggestions be actioned? i.e. if sampling from distribution, how is the distribution represented in DB?
3. How to prevent the same songs being played repeatedly? Use a fixed length queue? Or just use watch history itself?
4. Create a Recommender class -> it can have methods like reset, sample, update, etc.
5. What does it mean to "Currently play a song?" What happens when the song 'ends'? It should trigger an update request, mark the song as liked, update the distribution and sample a new song, which then becomes "currently playing"
6. What does it mean when a user "skips to next song"? It should trigger an update request, mark the song as disliked, update the distribution and sample a new song, which then becomes "currently playing"
7. The "reset" can just instantiate a new recommender object without history
8. Use deque with fixed length 5 to ensure that the last 5 songs don't get played again. How will this state persist between requests?

NEED SOME WAY TO INTERPRET THE PROFILE CREATED:
 -> TOP GENRES HISTORICALLY, TOP ARTISTS ETC. 
 -> LEAST LIKED...
 -> CHANGES OVER TIME

Django bootstrap v5

Use Django user model to link listen history for user

How to get the recommender variable to persist between request? -> Use Sessions -> NO -> Use pickle file

Will have to host on GCP

To login user: https://python.plainenglish.io/inbuild-user-authentication-with-django-38b5983a7543

To do:
1. Login user
2. Handle overlaps (same track belongs to track, album, artist, genre) - done
3. Make updates decay depending on no. of tracks listened to
4. SET TYPE DEFINTIONS FOR EACH FUNCTION, eg. track: Track
5. Add documentation for code


## ASSUMPTIONS:
1. The library of songs does not change in the midst of a user-session
2. If the library changes between sessions, how can we adjust for it? Songs that don't have weights should just get uniform weights whereas those for which we do have information should get scaled up/down
3. Each track belongs to exactly one album, each album belongs to exactly one artist, and each track belongs to exactly one genre. This is a limiting assumption, but useful for a quick implementation. 


## EXPLANATIONS:
1. The broad idea of the recommender is that before we have any information, each track is equally likely to be played. (Note: This assumption can be improved, so that each artist is equally likely or each genre is equally likely, etc. since the no. of tracks per artist is not the same, neither is the no. of tracks per genre etc. However, for simplicity, I am assuming that all tracks are equally likely. )<br>
The probability of a track being played is represented by a 'probability mass' given by a number of 'points' in the TrackWeight model. Therefore, the probability of a track i being played next is given by weight_i/sum_j(weight_j). <br>
The recommender object simulates the probability of each song being equally likely when a user first starts listening by assigning the same no. of points to each track. If we have existing information about a user, i.e. a set of track weights that is not uniform, that is loaded from disk when the user logs in. <br>
When a user listens to a track, we get feedback, which is assumed to be one of the following 5 possibilities: like, dislike, listen through till end, skip to next song, ignore. <br>
For simplicity, I assume that liking a track and listening to it through till the end are equivalent. Similarly, disliking and skipping are equivalent. "Ignoring" is meant to simulate a situation where the track is playing, but the user is not actually listening to it - this is a case where we actually get no feedback. <br>
If a user likes a track, we increase the weights for the track, for the album, for the artist, and for the genre. Note that an implicit hierarchical assumption is made here: a song is most strongly associated with itself, and with the album, artist, and the genre in descending order. Therefore, we must increase the track weight by some amount, then for the album by some lower value, and so on. If a user dislikes a track, the equivalent holds, except we reduce the weights. <br>
Then, when the next track is meant to be played, we sample from the distribution of weights over tracks, taking care not to play a track from the last x tracks. 
2. In terms of how much to scale weights, some important considerations are that we never want the weight of any given track to go to zero, since that track will never be played then. As a simplifying assumption, we can say that: 
> the highest weighted track (which we think the user likes the most) should never be more than X times more likely to be played than the lowest rated track. 

What this translates to is that the maximum possible values of (max(track_weight) / min(track_weight)) should never exceed X. We define this X to be a hyperparameter called max_ratio. We assume that this variable never changes across users, across sessions for simplicity. <br>
Some quick algebra allows us to derive upper and lower limits for track weights based on this assumption. These are calculated upon the recommender initialization and maintained in the min_possible_weight and max_possible_weight variables for the recommender. <br>
Additionally, (max_possible_weight - min_possible_weight) gives a range that the weights can be adjusted in. Now, if a song starts with the default no. of points, and is liked, we can adjust its track weight upward by some factor:
> lambda_track * ((max_possible_weight - track_current_weight) / (max_possible_weight - min_possible_weight))

Similarly, we can adjust the weight for each track of the album upward by (assuming there are m tracks in the album):
> lambda_album * ((max_possible_weight\*m - sum(current_weights_of_album_tracks)) / (max_possible_weight\*m - min_possible_weight*m))

and so on for artist and genre. <br>
When adjusting weights, we must be careful to maintain the same aggregate no of points across all tracks in the DB, so the weights of all tracks that do not fall into {track, album, artist, genre} must be reduced proportionally by the no of points that are added to this set. 
3. A deque is maintained of the last 5 songs to avoid playing any of those. The number 5 is a hyperparameter which can be tuned. 
4. # NEED TO BE CAREFUL -> LIKING A SONG IS NOT EQUIVALENT TO MOVING TO THE NEXT TRACK