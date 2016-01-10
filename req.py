from urlparse import urlparse
import httplib

# this class will return the end url of a link shortener
# does not work with multi-level shortening (un-covered border case)
class link_lengthener():

    # initialize dictionary to optimize against re-querying
    def __init__(self):
        self.seen = {}

    def extend(self, url):
        # url needs to start with http(s) for parser to work
        if "://" not in url:
            url = "http://" + url
        o = urlparse(url)
        path = '/' if o.path=='' else o.path
        # check to see if url has already been queried
        try:
            return self.seen[o.netloc + path]
        # query server and get response
        except:
            r = get_r(o.scheme, o.netloc, path)
            resp_str = ("HTTP/" + str(r.version)[0:1] + "."
                    + str(r.version)[1:2] +" "+ str(r.status) + " " + r.reason)
            # build dictionary
            url_dict = {}
            url_dict['response'] = resp_str
            # if the status code indicates a re-direct
            if r.status / 100 == 3:
                url_dict['url'] = r.getheader('location')
            elif r.status / 100 == 4:
                url_dict['url'] = ''
            else:
                url_dict['url'] = o.scheme + "://" + o.netloc + path
            url_dict['header'] = r.msg.headers
            self.seen[o.netloc + path] = url_dict
            return url_dict

# Exception to use in case of not HTTP link
class NotHTTP(Exception):
    pass

# function to get response
def get_r(scheme, server, path):
        if scheme.upper() == 'HTTPS':
            connection = httplib.HTTPSConnection(server)
        elif scheme.upper() == 'HTTP':
            connection = httplib.HTTPConnection(server)
        else:
            raise NotHTTP("Link must be HTTP(S), not " + o.scheme)
        connection.request("HEAD", path)
        response = connection.getresponse()
        connection.close()
        return response
