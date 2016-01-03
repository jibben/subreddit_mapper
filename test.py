import praw
import json

# initialize praw object
r = praw.Reddit(user_agent='subreddit_mapper see https://github.com/jibbenHillen/subreddit_mapper')
# read in info from config file
with open('config.json', 'rb') as config_file:
    config = json.load(config_file)
# set up authorization
r.set_oauth_app_info(client_id=config["client_id"],
                     client_secret=["client_secret"],
                     redirect_uri=["redirect_uri"])
submissions = r.get_subreddit('opensource').get_hot(limit=10)
for thing in submissions:
    print thing
