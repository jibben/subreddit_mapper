#! /usr/bin/env python

import praw     # wrapper for python API
import json     # to handle json from initial default fetch
import urllib2  # to handle initial default fetch
import re       # to get subreddit matches from sidebar
import pprint   # for debuggging
import os       # for checking for files / moving files
import time     # to sleep after manual json request
import traceback# to put full traceback into log file
import sys      # to exit program
import signal   # to catch ^C 
from subreddit import subreddit

# global variable to handle exit

exit = False
# exit gracefully upon ctrl-c press
def signal_handler(signal, frame):
    global exit
    exit = True
    print "\nExiting..."

# function to find related subreddits from sidebar, returns list of names
def parse_sidebar(r,sub_name,sidebar):
    related = set()
    # subreddits are of the form '/r/namehere'
    re_sub = re.compile('\/r\/([0-9a-zA-Z_]{1,21})')
    re_multi = re.compile('user\/([0-9a-zA-Z_-]{1,21})\/m\/([0-9a-zA-Z_-]{1,21})')
    # fist simply parse any mentions directly in sidebar
    for match in re_sub.findall(sidebar):
        related.add(match.lower().encode('ascii','ignore'))

    # then fine any mentioned multireddits and parse them
    for match in re_multi.findall(sidebar):
        multi = r.get_multireddit(match[0], match[1], fetch=True)
        for sub in multi.subreddits:
            related.add(sub.display_name.lower().encode('ascii','ignore'))

    #TODO: handle link shorteners

    # don't want self-pointers
    try:
        related.remove(sub_name)
    except KeyError:
        pass #no self-pointer in related

    return list(related)

# function to write visited subreddit to output file
def write_sub(sub, f_output):
    f_output.write(sub.encode())
    f_output.write('\n')

def build_praw(user_agent):
    rd = praw.Reddit(user_agent=user_agent, api_request_delay=1.0)

    # read in info from config file
    with open('config.json', 'rb') as f_config:
        config = json.load(f_config)

    # set up authorization
    rd.set_oauth_app_info(client_id=config["client_id"],
                         client_secret=["client_secret"],
                         redirect_uri=["redirect_uri"])
    # return full praw object
    return rd

# check for local list of defaults and load, otherwise download and load
def get_defaults():
    # if no file, download and write it
    if not os.path.isfile('default.json'):
        default_url = urllib2.urlopen("https://www.reddit.com/subreddits/default.json")
        with open('default.json', 'w') as f_defaults:
            f_defaults.write(default_url.read())

        time.sleep(1)   #we have to sleep to respect API rules

    # now can load defaults from file
    with open('default.json', 'rb') as f_defaults:
        default_dict = json.load(f_defaults)

    default_list = []
    for sub in default_dict["data"]["children"]:
        default_list.append(sub["data"]["display_name"].lower())

    return default_list

# visit the subreddit with praw, get information, and write to file
def visit_sub(r, sub_name, f_output):
    p_sub = r.get_subreddit(sub_name, fetch=True)
    related = parse_sidebar(r,sub_name,p_sub.description if p_sub.description!=None else "")
    # create the subreddit info
    sub = subreddit(sub_name, p_sub.subscribers, p_sub.over18,
            p_sub.submission_type if p_sub.submission_type!=None else "none",
            related)

    write_sub(sub, f_output)

    return sub

# write error information to errors.log
# write to_visit.json and seen.json
# exit
def exit_write(cur_sub, to_visit, seen, f, e, traceback = ""):
    # write error info
    with open('out.log', 'a') as f:
        f.write("Time: ")
        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        f.write("\nExited on sub: " + cur_sub)
        f.write("\n" + str(e))
        if traceback:
            f.write("\n" + traceback)
        f.write("\n\n")

    # write seen to seen.json
    with open('seen.json', 'w') as f:
        f.write(json.dumps(list(seen)))

    # write to_visit to to_visit.json
    with open('to_visit.json', 'w') as f:
        f.write(json.dumps(to_visit))

    f.close () # close output file
    sys.exit(2)

# returns list: [to_visit, seen, f_output]
# if to_visit and seen both already exist, load in and start from where we were
# if ^ but output.csv doesn't exist, raise message and qui
# else start from scratch
# if starting from scratch and old output.csv, move to output_epoch.csv
def init_vars():
    has_visit = os.path.isfile('to_visit.json')
    has_seen = os.path.isfile('seen.json')

    if(has_visit and has_seen):
        with open('to_visit.json') as f_visit:
            to_visit = json.load(f_visit)

        with open('seen.json', 'rb') as f_seen:
            seen = set(json.load(f_seen))
        try:
            output = open('output.csv', 'a')
        except:
            print "no subreddits.csv. delete to_visit and seen to start over"
            exit(1)
    else:
        if(has_visit or has_seen):
            print "missing to_visit.json or seen.json: starting over"

        to_visit = get_defaults()
        seen = set(to_visit)

        if os.path.isfile('output.csv'):
            new_name = "output_"
            new_name += str(int(time.time()))
            new_name += ".csv"
            os.rename("output.csv", new_name)

        output = open('output.csv', 'w')

    return [to_visit, seen, output]

def main():
    # initialize praw object and holding structures
    r = build_praw('subreddit_mapper v0.3 github.com/jibbenHillen')

    # initialize to_visit and seen
    to_visit,seen,out_file = init_vars()

    # while there is a subreddit in the stack, visit it
    while to_visit and not exit:
        sub_name = to_visit.pop()
        try:
            current_sub = visit_sub(r, sub_name, out_file)

            # update set of seen and stack
            for sub in current_sub.related:
                if sub not in seen:
                    to_visit.append(sub)
                    seen.add(sub)

        except (praw.errors.Forbidden, praw.errors.NotFound,
                praw.errors.InvalidSubreddit): #error with the sub, continue
            pass
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e: #other error, such as response failure
            to_visit.append(sub_name)
            #exit gracefully
            exit_write(sub_name,to_visit,seen,out_file,e,traceback.format_exc())
    if exit:
        exit_write(sub_name,to_visit,seen,out_file,"Ctrl-C Pressed")
    else:
        exit_write(sub_name,to_visit,seen,out_file,"Completed successfully")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
