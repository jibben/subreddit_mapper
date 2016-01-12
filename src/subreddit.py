class subreddit:
    # Attributes:
        # name: string of subreddit name    'AskReddit'
        # access: string of public-status   'public'
        # subs: int of num subs             10089909
        # nsfw: bool of over18              False
        # type: string of self/link/all     'self'
        # related: list of other subs       [sdk,dfamkj,sdfhj]
    __slots__ = ['name','access','subs','nsfw','type','related']

    def __init__(self, name, access, subs = 0, nsfw = False,
            type = "any", related = []):
        self.name = name
        self.access = access
        self.subs = subs
        self.nsfw = nsfw
        self.type = type
        self.related = related

    # encode the subreddit object into a csv string:
    # name,subs,nsfw,type,related0,related1,...
    def encode(self):
        csv_str = (self.name + ',' + self.access + ',' + str(self.subs)
                + ',' + str(self.nsfw) + ',' + self.type)
        for sub in self.related:
           csv_str += ',' + sub
        return csv_str

    # decode from a csv string as encoded above
    def decode(self, csv_str):
        info = csv_str.split(',')
        self.name = info[0]
        self.access = info[1]
        self.subs = int(info[2])
        self.nsfw = (info[3] == 'True')
        self.type = info[4]
        if len(csv_str) > 4:
            self.related = info[5:]

    # add related subreddit(s) to the list
    def add_related(self,subs):
        for sub in subs:
            self.related.append(sub)
