#! /usr/bin/env python

import os       # to get shorteners from longurl API
import urllib2  # ^^
import json     # ^^

from src.crawler import crawler

# function to handle fetching list of shorteners from longurl API
# hopefully they never disable this API...

# if already have file, read and return it
# otherwise download, write, and return it
def get_shorteners():
    if os.path.isfile('./data/.shorteners.json'):
        with open('./data/.shorteners.json', 'rb') as f_shorteners:
            shorteners = json.load(f_shorteners)

    else:
        shorteners_url = urllib2.urlopen("http://api.longurl.org/v2/services?format=json")

        shorteners = list(json.load(shorteners_url).keys())

        with open('./data/.shorteners.json', 'w') as f_shorteners:
            f_shorteners.write(json.dumps(shorteners))

    return shorteners

def main():
    subreddit_crawler = crawler('subreddit_mapper v1.0 github.com/jibbenHillen', get_shorteners())
    subreddit_crawler.crawl()

if __name__ == "__main__":
    main()
