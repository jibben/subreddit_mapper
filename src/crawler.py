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

## class ##
class crawler():
    # Attributes:
        # r: PRAW object to query reddit
        # l: link_lengthener to find endpoints of shortened URLs
        # count: int of number of subreddits visited
        # to_visit: list (used as stack) of subreddits to visit
        # seen: set of subreddits seen
        # out_file: csv file to write subreddit information to
        # reg: dictionary of regexes, used for scraping sidebar
        # exit: boolean of whether ctrl-c has been pressed
        # start_time: float of start time in seconds since epoch

    # Inputs:
        # user_agent: string descriptor to authenticate with Reddit
        # shorteners: list of strings of known link shorteners
            # this can be pulled from longurl.org API

    def __init__(self, user_agent, shorteners):
        # catch ctrl-c and exit gracefully
        signal.signal(signal.SIGINT, self.signal_handler)

        self.r = build_praw(user_agent)
        self.l = link_lengthener(shorteners)

        self.count = 0

        # load in old run if exists, otherwise start from scratch
        # if user deletes some files but not others, just ignore old files
        try:
            with open('./data/.to_visit.json') as f_visit:
                self.to_visit = json.load(f_visit)
            with open('./data/.seen.json') as f_seen:
                self.seen = set(json.load(f_seen))
            self.out_file = open('./data/output.csv', 'a')
        except:
            self.to_visit = get_defaults()
            self.seen = set(self.to_visit)
            if os.path.isfile('./data/output.csv'):
                os.rename('./data/output.csv',
                        './data/output_' + str(int(time.time())) + '.csv')
            self.out_file = open('./data/output.csv', 'w')
            self.out_file.write('name,access,num_subs,nsfw,type,related1,related2,...\n')

        # regexes
        self.reg = {}
        self.reg['sub'] = re.compile('\/r\/(\w{2,21})')
        self.reg['sub_link'] = re.compile('(?!www.)(\w{3,21})\.reddit\.com')
        self.reg['multi'] = re.compile('user\/([0-9a-zA-Z_-]{1,21})\/m\/([0-9a-zA-Z_-]{1,21})')
        self.reg['wiki'] = re.compile('\/r\/(\w{1,21})\/wiki\/(\S?)($|\)|\#)')
        self.reg['url'] = re.compile('(\[\S+?\]\()(\S+?\.\S+?)(\)\|?)')
        self.reg['rel'] = re.compile('(#.*?[[fF]riends|[sS]ubreddits|[rR]elated]*.*?\n)((.|\n)*?)(#|\Z)')

        # var to handle exit
        self.exit = False

        # var to time process
        self.start_time = None

    ## functions ##

    # exit gracefully upon ctrl-c press
    # press twice to force quit
    def signal_handler(self, signal, frame):
        if self.exit:
            sys.exit(1)
        else:
            self.exit = True
            print "\nExiting..."

    def crawl(self):
        self.start_time = time.time()
        print "Start time: " + time.ctime(self.start_time)[4:19]
        while self.to_visit and not self.exit:
            sub_name = self.to_visit.pop()
            try:
                current_sub = self.visit_sub(sub_name)

                # update set of seen and stack
                for sub in current_sub.related:
                    if sub not in self.seen:
                        self.to_visit.append(sub)
                        self.seen.add(sub)
            except praw.errors.InvalidSubreddit: #if sub is invalid, continue
                pass
            except SystemExit:
                raise
            except Exception as e: #other error, such as response failure
                self.to_visit.append(sub_name)
                #exit gracefully
                self.exit_write(sub_name,e,traceback.format_exc())
            self.count += 1
        if exit:
            self.exit_write(sub_name,"Ctrl-C Pressed")
        else:
            self.exit_write(sub_name,"Completed successfully")

    # 1) write exit information to exit.log
    # 2) if there are still subs to visit,
    # write to_visit.json and seen.json to file
    # 3) exit
    # sometimes socket will raise an error code not wrapped in an Exception
    # This will happen upon ctrl-c sometimes, so handle manually
    def exit_write(self, cur_sub, e, traceback = ""):
        end_time = time.time()
        print "End time: " + time.ctime(end_time)[4:19]
        with open('./data/exit.log', 'a') as f:
            f.write("End time: ")
            f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)) + "\n")
            f.write("Start time: ")
            f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)) + "\n")
            f.write("Time elapsed: " + str(round(end_time - self.start_time, 1)) + " seconds\n")
            f.write("Exited on sub: " + cur_sub + "\n")
            f.write("Number of subs scraped: " + str(self.count) + "\n")

            if "Interupted system call" in str(e):
                f.write("Ctrl-C Pressed\n")
            else:
                f.write(str(e) + "\n")
                if traceback:
                    f.write(traceback + "\n")
                f.write("\n")

        if self.to_visit:
            with open('./data/.seen.json', 'w') as f:
                f.write(json.dumps(list(self.seen)))

            with open('./data/.to_visit.json', 'w') as f:
                f.write(json.dumps(self.to_visit))

        self.out_file.close()
        sys.exit(2)

    # visit the subreddit, get information, and write to file
    # if the sub is banned/private/restricted, handle correctly
    # raises praw.errors.InvalidSubreddit error in case of invalid name
    def visit_sub(self, sub_name):
        try: # valid, public subreddit
            p_sub = self.r.get_subreddit(sub_name)

            related = self.parse_sidebar(sub_name,p_sub.description if p_sub.description!=None else "")

            sub = subreddit(sub_name, 'public', p_sub.subscribers, p_sub.over18,
                p_sub.submission_type if p_sub.submission_type!=None else "none",
                related)
        except praw.errors.Forbidden: #private, quarantined, or restricted
            sub = subreddit(sub_name, 'private')
        except praw.errors.NotFound: #banned
            sub = subreddit(sub_name, 'banned')
        except:
            raise

        self.write_sub(sub)
        return sub

    # function to find related subreddits from sidebar, returns list of names
    # checks checks for subs/multis, then wikis, then links
    def parse_sidebar(self, sub_name, sidebar):
        related = set()

        related |= self.get_subs(sidebar)

        for w in self.reg['wiki'].findall(sidebar):
            if re.search('[sS]ubs|[sS]ubreddits|[rR]elated|[fF]riends?', w[1]):
               related |= self.get_subs(r.get_wiki_page(match[0], w[1]).content_md)

        related |= self.parse_links(sidebar)

        # don't want self-pointers
        if sub_name in related:
            related.remove(sub_name)

        return list(related)

    # function to get set of subreddits from text, w/ multireddit parsing
    def get_subs(self, text):
        subs = set()

        # look for '/r/subname'
        for sub in self.reg['sub'].findall(text):
            subs.add(sub.lower().encode('ascii','ignore'))
        # look for 'subname.reddit.com'
        for sub in self.reg['sub_link'].findall(text):
            subs.add(sub.lower().encode('ascii','ignore'))
        # look for multireddits, parse them
        for match in self.reg['multi'].findall(text):
            subs |= self.parse_multi(match[0:2])

        return subs

    # function to get list of subreddits from multireddit
    def parse_multi(self, multi):
        subs = set()

        m = self.r.get_multireddit(multi[0], multi[1])

        for sub in m.subreddits:
            subs.add(sub.display_name.lower().encode('ascii','ignore'))

        return subs

    # function to find reddit links hidden through non-reddit link shortener
    def parse_links(self, text):
        subs = set()
        for link in self.reg['url'].findall(text):
            if 'reddit.com' not in link[1]:
                long_url = self.l.extend(link[1])

                if 'reddit.com' in long_url:

                    # check if multireddit
                    if '/m/' in long_url:
                        m = self.reg['multi'].match(long_url)
                        subs |= self.parse_multi([multi.group(1), multi.group(2)])

                    # then check if wiki
                    elif '/wiki/' in long_url:
                        w = self.reg['wiki'].match(long_url)
                        subs |= self.get_subs(self.r.get_wiki_page(w.group(0), w.group(1)).content_md)

                    # lastly check if simple subreddit
                    elif '/r/' in long_url:
                        sub = self.reg['sub'].match(long_url).group(0)
                        subs.add(sub.lower().encode('ascii','ignore'))

        return subs

    # function to write visited subreddit to output file
    def write_sub(self, sub):
        self.out_file.write(sub.encode())
        self.out_file.write('\n')

## functions out of class ##

def build_praw(user_agent):
    r = praw.Reddit(user_agent=user_agent, api_request_delay=1.0)

    # read in info from config file
    with open('./config.json', 'rb') as f_config:
        config = json.load(f_config)

    # set up authorization
    r.set_oauth_app_info(client_id=config["client_id"],
                         client_secret=["client_secret"],
                         redirect_uri=["redirect_uri"])
    # return full praw object
    return r

# check for local list of defaults and load, otherwise download and load
def get_defaults():
    # if no file, download and write it
    if not os.path.isfile('./data/.defaults.json'):
        default_url = urllib2.urlopen("https://www.reddit.com/subreddits/default.json")
        with open('./data/.defaults.json', 'w') as f_defaults:
            f_defaults.write(default_url.read())

        time.sleep(1)   #we have to sleep to respect API rules

    # now can load defaults from file
    with open('./data/.defaults.json', 'rb') as f_defaults:
        default_dict = json.load(f_defaults)

    default_list = []
    for sub in default_dict["data"]["children"]:
        default_list.append(sub["data"]["display_name"].lower())

    return default_list
