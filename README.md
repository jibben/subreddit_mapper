# subreddit_mapper
Mapping the structure of subreddits via sidebar recommendations

### Requirements
Run setup.py to create config.json
To get an ID and secret, go to [reddit's app page](https://www.reddit.com/prefs/apps/).

## Behavior

### Current behavior
v1.0

Everything appears to work corrrectly, tested with up to 2000 scraped subreddits. Run with main.py


v0.5

Now scrapes related subreddits from link-shorteners, wikis, and mulireddits

v0.3

Now gracefully handles incorrect subreddit names, forbidden subreddits, and banned subreddits. Will gracefully exit on ctrl-c. Saves all crashes and exits to out.log.

Created 'clean' script to clean up to start a new run - deletes output.csv, seen.json, to_visit.json, out.log


v0.2

Writes information with related subreddits to output.csv and visits all subreddits found with depth-first-search. Does not handle link shortened reddit connections yet. If the program crashes, it will gracefully save all information to file so it can be started again later

v0.1

Prints information (no related subreddits) for all default subreddits

### Goal behavior
Create file of all subreddits found with list of all related subreddits. This will take a few days because of reddit API limitations.
