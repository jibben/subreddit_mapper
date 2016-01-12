#! /usr/bin/env python

### external packages ###

import praw     # wrapper for python API
import json     # to handle json from initial default fetch
import urllib2  # to handle initial default fetch
import re       # to get subreddit matches from sidebar
import os       # for checking for files / moving files
import time     # to sleep after manual json request
import traceback# to put full traceback into log file
import sys      # to exit program
import signal   # to catch ^C


### custom classes ###

from subreddit import subreddit # subreddit object
from req import link_lengthener # class to extend shortened links


### regexes ###

# match sub name
re_sub = re.compile('\/r\/(\w{2,21})')
# the only subs less than 3 characters are also special prefixes
# so we won't lose any references to subs!
re_sub_link = re.compile('(?!www.)(\w{3,21})\.reddit\.com')
# match multireddits
re_multi = re.compile('user\/([0-9a-zA-Z_-]{1,21})\/m\/([0-9a-zA-Z_-]{1,21})')
# match wikis
re_wiki = re.compile('\/r\/(\w{1,21})\/wiki\/(\S?)($|\)|\#)')
# get all ('related','friends', 'subreddits') sections
# re_rel = re.compile('(#.*?[[fF]riends|[sS]ubreddits|[rR]elated]*.*?\n)((.|\n)*?)(#|\Z)')
# match all general links
re_url = re.compile('(\[\S+?\]\()(\S+\.\S+?)(\))')
# global variable to handle exit
exit = False


## functions ##

# exit gracefully upon ctrl-c press
# press twice to force quit
def signal_handler(signal, frame):
    global exit
    if exit:
        sys.exit(5)
    else:
        exit = True
        print "\nExiting..."

# function to find related subreddits from sidebar, returns list of names
def parse_sidebar(r,l,sub_name,sidebar):
    related = set()

    #get direct mentions of subs by name and multireddit
    related |= get_subs(r, sidebar)

    #find wiki matches in the sidebar, search those for multis/subreddits
    for w in re_wiki.findall(sidebar):
        if re.search('[sS]ubs|[sS]ubreddits|[rR]elated|[fF]riends?', w[1]):
           related |= get_subs(r, r.get_wiki_page(match[0], w[1]).content_md)

    # find links, follow through to end point, then look there for subs
    related |= parse_links(r, l, sidebar)

    # TODO: only in related section?
    #for match in re_rel.findall(sidebar):
    #    related |= parse_links(r, match[1])

    # don't want self-pointers
    try:
        related.remove(sub_name)
    except KeyError:
        pass #no self-pointer in related

    return list(related)

# function to get set of subreddits from text, w/ multireddit parsing
def get_subs(r, text):
    subs = set()
    # subreddits are of the form '/r/namehere'
    # fist simply parse any mentions directly in sidebar
    for sub in re_sub.findall(text):
        subs.add(sub.lower().encode('ascii','ignore'))
    # then parse for subs of the form 'namehere.reddit.com'
    for sub in re_sub_link.findall(text):
        subs.add(sub.lower().encode('ascii','ignore'))
    # then find any mentioned multireddits and parse them
    for match in re_multi.findall(text):
        subs |= parse_multi(r, match[0:2])

    return subs

# function to get list of subreddits from multireddit
def parse_multi(r, multi):
    subs = set()

    m = r.get_multireddit(multi[0], multi[1], fetch=True)

    for sub in m.subreddits:
        subs.add(sub.display_name.lower().encode('ascii','ignore'))

    return subs

# function to parse links and find end-subs from text
def parse_links(r, l, text):
    subs = set()
    for link in re_url.findall(text):
        # if a link is found that does not include reddit
        if 'reddit.com' not in link[1]:

            # AND the link when lengthened does include reddit
            long_url = l.extend(link[1])
            if 'reddit.com' in long_url:
                # try to parse end-result

                # check if multireddit
                if '/m/' in long_url:
                    m = re_multi.match(long_url)
                    subs |= parse_multi(r, [multi.group(1), multi.group(2)])

                # then check if wiki
                elif '/wiki/' in long_url:
                    w = re_wiki.match(long_url)
                    subs |= get_subs(r,
                            r.get_wiki_page(w.group(0), w.group(1)).content_md)

                # lastly check if simple subreddit
                elif '/r/' in long_url:
                    sub = re_sub.match(long_url).group(0)
                    subs.add(sub.lower().encode('ascii','ignore'))

    return subs

# function to write visited subreddit to output file
def write_sub(sub, f_output):
    f_output.write(sub.encode())
    f_output.write('\n')

def build_praw(user_agent):
    rd = praw.Reddit(user_agent=user_agent, api_request_delay=1.0)

    # read in info from config file
    with open('../config.json', 'rb') as f_config:
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
    if not os.path.isfile('../data/default.json'):
        default_url = urllib2.urlopen("https://www.reddit.com/subreddits/default.json")
        with open('../data/default.json', 'w') as f_defaults:
            f_defaults.write(default_url.read())

        time.sleep(1)   #we have to sleep to respect API rules

    # now can load defaults from file
    with open('../data/default.json', 'rb') as f_defaults:
        default_dict = json.load(f_defaults)

    default_list = []
    for sub in default_dict["data"]["children"]:
        default_list.append(sub["data"]["display_name"].lower())

    return default_list

# function to handle fetching list of shorteners from longurl API
# hopefully they never disable this API...
def get_shorteners():
    # if file, read and return it
    if os.path.isfile('../data/shorteners.json'):
        with open('../data/shorteners.json', 'rb') as f_shorteners:
            shorteners = json.load(f_shorteners)
        return shorteners
    # if no file, download write and return it
    else:
        shorteners_url = urllib2.urlopen("http://api.longurl.org/v2/services?format=json")
        # just get list of keys
        shorteners = list(json.load(shorteners_url).keys())
        with open('../data/shorteners.json', 'w') as f_shorteners:
            f_shorteners.write(json.dumps(shorteners))

        return shorteners

# visit the subreddit with praw, get information, and write to file
def visit_sub(r, l, sub_name, f_output):
    # works for all valid public subs
    try:
        p_sub = r.get_subreddit(sub_name, fetch=True)
        related = parse_sidebar(r,l,sub_name,p_sub.description if p_sub.description!=None else "")
    # create the subreddit info
        sub = subreddit(sub_name, 'public', p_sub.subscribers, p_sub.over18,
            p_sub.submission_type if p_sub.submission_type!=None else "none",
            related)
        write_sub(sub, f_output)
    # handle private or banned subs too
    except praw.errors.Forbidden:
        sub = subreddit(sub_name, 'private')
        write_sub(sub, f_output)
    except praw.errors.NotFound:
        sub = subreddit(sub_name, 'banned')
        write_sub(sub, f_output)
    # if a sub does not exist, function will raise InvalidSubreddit error

    return sub

# write error information to errors.log
# write to_visit.json and seen.json
# exit
def exit_write(cur_sub, to_visit, seen, f, e, traceback = ""):
    # write error info
    with open('../data/out.log', 'a') as f:
        f.write("Time: ")
        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        f.write("\nExited on sub: " + cur_sub)
        f.write("\n" + str(e))
        if traceback:
            f.write("\n" + traceback)
        f.write("\n\n")

    # write seen to seen.json
    with open('../data/seen.json', 'w') as f:
        f.write(json.dumps(list(seen)))

    # write to_visit to to_visit.json
    with open('../data/to_visit.json', 'w') as f:
        f.write(json.dumps(to_visit))

    f.close () # close output file
    sys.exit(2)

# returns list: [to_visit, seen, f_output]
# if to_visit and seen both already exist, load in and start from where we were
# if ^ but output.csv doesn't exist, raise message and qui
# else start from scratch
# if starting from scratch and old output.csv, move to output_epoch.csv
def init_vars():
    has_visit = os.path.isfile('../data/to_visit.json')
    has_seen = os.path.isfile('../data/seen.json')

    if(has_visit and has_seen):
        with open('../data/to_visit.json') as f_visit:
            to_visit = json.load(f_visit)

        with open('../data/seen.json', 'rb') as f_seen:
            seen = set(json.load(f_seen))
        try:
            output = open('../data/output.csv', 'a')
        except:
            print "no subreddits.csv. delete to_visit and seen to start over"
            exit(1)
    else:
        if(has_visit or has_seen):
            print "missing to_visit.json or seen.json: starting over"

        to_visit = get_defaults()
        seen = set(to_visit)

        if os.path.isfile('../data/output.csv'):
            new_name = "../data/output_"
            new_name += str(int(time.time()))
            new_name += ".csv"
            os.rename("../data/output.csv", new_name)

        output = open('../data/output.csv', 'w')

    return [to_visit, seen, output]

def main():
    # initialize praw object and link_lengthener
    r = build_praw('subreddit_mapper v0.5 github.com/jibbenHillen')
    l = link_lengthener(get_shorteners())

    # initialize to_visit and seen
    to_visit,seen,out_file = init_vars()

    # while there is a subreddit in the stack, visit it
    while to_visit and not exit:
        sub_name = to_visit.pop()
        try:
            current_sub = visit_sub(r, l, sub_name, out_file)

            # update set of seen and stack
            for sub in current_sub.related:
                if sub not in seen:
                    to_visit.append(sub)
                    seen.add(sub)
        except praw.errors.InvalidSubreddit: #if sub is invalid, continue
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
