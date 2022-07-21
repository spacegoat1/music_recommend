# music_recommend
Project to create DB of music tracks and play future tracks based on user's behavior. 

Data taken from: https://github.com/mdeff/fma (fma_metadata.zip file -> raw_tracks.csv)

## ASSUMPTIONS:
1. The library of songs does not change in the midst of a user-session
2. Each track belongs to exactly one album, each album belongs to exactly one artist, and each track belongs to exactly one genre. This is a limiting assumption, but useful for a quick implementation. 

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

What this translates to is that the maximum possible values of (max(track_weight) / min(track_weight)) should never exceed X. We define this X to be a hyperparameter called max_ratio (currently set to 50). We assume that this variable never changes across users, across sessions for simplicity. <br>
Some quick algebra allows us to derive upper and lower limits for track weights based on this assumption. These are calculated upon the recommender initialization and maintained in the min_possible_weight and max_possible_weight variables for the recommender. <br>
Additionally, (max_possible_weight - min_possible_weight) gives a range that the weights can be adjusted in. Now, if a song starts with the default no. of points, and is liked, we can adjust its track weight upward by some factor:
> lambda_track * ((max_possible_weight - track_current_weight) / (max_possible_weight - min_possible_weight))

Similarly, we can adjust the weight for each track of the album upward by (assuming there are m tracks in the album):
> lambda_album * ((max_possible_weight\*m - sum(current_weights_of_album_tracks)) / (max_possible_weight\*m - min_possible_weight*m))

and so on for artist and genre. <br>
When adjusting weights, we must be careful to maintain the same aggregate no of points across all tracks in the DB, so the weights of all tracks that do not fall into {track, album, artist, genre} must be reduced proportionally by the no of points that are added to this set. 

3. A deque is maintained of the last 5 songs to avoid playing any of those. The number 5 is a hyperparameter which can be tuned. 

4. Note that 'liking' a track and 'listening through' the track are treated equivalently. Similarly, 'disliking' and 'skipping' a track are also treated equivalently. Liking or disliking a track once disables liking/disliking it again in the same listen, but the track can be liked/disliked the next time it is listened to. 

5. Note that the number of songs is not uniformly distributed across genres (distribution of song counts has been shared by email), and since we start with the assumption that each song is equally likely, this translates to the most frequent genre being overplayed in the beginning. 

6. Weights are updated asynchronously. The code for async updates in DB was taken off StackOverflow: https://stackoverflow.com/questions/6614194/how-to-have-django-give-a-http-response-before-continuing-on-to-complete-a-task and called in async_queue.py

7. I included a simple bar chart using this guide: https://www.section.io/engineering-education/integrating-chart-js-in-django/ Ideally, I would have liked to show a probability distribution across all tracks, but there are too many to show meaningfully, so I left it at probability by genre. Note that the 'alpha_genre' parameter is higher than the artist and album ones only because I am showing the distribution of masses over genres on the frontend - so that likes/dislikes by the user shows us as an effect on genre. 

8. I wanted to check that the recommender was actually doing what was expected, so I wrote a small test function in test_recommender.py, and it appears to be function well. 

9. While in theory we can have multiple users since a user model has already been implemented, for the current demo, only a single user is assumed. 