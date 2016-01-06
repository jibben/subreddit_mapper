class subreddit:
    # Attributes:
        # name: string of subreddit name    'AskReddit'
        # subs: int of num subs             10089909
        # nsfw: bool of over18              False
        # type: string of self only         'self'
        # related: list of other subs   [sdk,dfamkj,sdfhj]
    __slots__ = ['name','subs','nsfw','type','related']

    def __init__(self, name, subs = 0,
                 nsfw = False, type = "any", related = []):
        self.name = name
        self.subs = subs
        self.nsfw = nsfw
        self.type = type
        self.related = related

    # encode the subreddit object into a csv string:
    # name,subs,nsfw,type,related0,related1,...
    def encode(self):
        csv_str = self.name
        csv_str += ',' + str(self.subs)
        csv_str += ',' + str(self.nsfw)
        csv_str += ',' + self.type
        for sub in self.related:
           csv_str += ',' + sub
        return csv_str

    # decode from a csv string as encoded above
    def decode(self, csv_str):
        info = csv_str.split(',')
        self.name = info[0]
        self.subs = int(info[1])
        self.nsfw = (info[2] == 'True')
        self.type = info[3]
        if len(csv_str) > 4:
            self.related = info[4:]

    # add related subreddit(s) to the list
    def add_related(self,subs):
        for sub in subs:
            self.related.append(sub)
