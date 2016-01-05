# subreddit_mapper
Mapping the structure of subreddits via sidebar recommendations

### Requirements
config.json file with information filled out (template is provided). You can leave callback_uri as it is.
To get an ID and secret, go to [reddit's app page](https://www.reddit.com/prefs/apps/).

## Behavior

### Current behavior
v0.1
Prints information (no related subreddits) for all default subreddits

### Goal behavior
Create file of all subreddits found with list of all related subreddits. This will take a few days because of reddit API limitations.
