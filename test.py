#! /usr/bin/env python

import praw     # wrapper for python API
import json     # to handle json from initial default fetch
import urllib2  # to handle initial default fetch
import re       # to get subreddit matches from sidebar
import pprint   # for debuggging
import os.path  # for writing to file
from subreddit import subreddit
# function to find related subreddits from sidebar, returns list of names
def parse_sidebar(sidebar):
    related = []
    #TODO: implement
    return related

# function to write visited subreddit to output file
def write_sub(sub):
    #TODO: implement
    print sub.encode()

def main():
    # initialize praw object and holding structures
    r = praw.Reddit(user_agent='subreddit_mapper see https://github.com/jibbenHillen/subreddit_mapper',
                api_request_delay = 1.0)
    seen = set()
    to_visit = []

    # read in info from config file
    with open('config.json', 'rb') as config_file:
        config = json.load(config_file)
    # set up authorization
    r.set_oauth_app_info(client_id=config["client_id"],
                         client_secret=["client_secret"],
                         redirect_uri=["redirect_uri"])

    # get list of default subreddits and start from there
    default_url = urllib2.urlopen("https://www.reddit.com/subreddits/default.json")
    default_dict = json.loads(default_url.read())
    # for each default sub, add to stack to check
    for sub in default_dict["data"]["children"]:
        to_visit.append(sub["data"]["display_name"])
        seen.add(sub["data"]["display_name"])
    # while there is a subreddit in the stack, visit it
    while to_visit:
        sub_name = to_visit.pop()
        sub_info = r.get_subreddit(sub_name)
        current_sub = subreddit(sub_name,
                        sub_info.subscribers,
                        sub_info.over18,
                        sub_info.submission_type)
        current_sub.add_related(parse_sidebar(sub_info.description))

        write_sub(current_sub)

        # update set of seen and stack
        for sub in current_sub.related:
            if sub not in seen:
                to_visit.append(sub)
                seen.add(rel_sub)

if __name__ == "__main__":
    main()
