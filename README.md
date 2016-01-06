# subreddit_mapper
Mapping the structure of subreddits via sidebar recommendations

### Requirements
config.json file with information filled out (template is provided). You can leave callback_uri as it is.
To get an ID and secret, go to [reddit's app page](https://www.reddit.com/prefs/apps/).

## Behavior

### Current behavior
v0.2\r\n
Writes information with related subreddits to output.csv and visits all subreddits found with depth-first-search. Does not handle link shortened reddit connections yet. If the program crashes, it will gracefully save all information to file so it can be started again later\r\n
v0.1\r\n
Prints information (no related subreddits) for all default subreddits

### Goal behavior
Create file of all subreddits found with list of all related subreddits. This will take a few days because of reddit API limitations.
