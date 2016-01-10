from urlparse import urlparse
import httplib

# this class will return the end url of a link shortener
# works with multi-level shortening
    class link_lengthener():

    # initialize dictionary to optimize against re-querying
    def __init__(self):
        seen = {}

    def extend(self, url):
        # url needs to start with http(s) for parser to work
        if "://" not in url:
            url = "http://" + url
        o = urlparse(url)
        path = '/' if o.path=='' else o.path
        # check to see if url has already been queried
        try:
            return seen[o.netloc + path]
        # query server and get response
        except:
            r = __get_r(o.scheme, o.netloc, '/' if o.path=='' else o.path)
            resp_str = ("HTTP/" + str(r.version)[0:1] + "."
                    + str(r.version)[1:2] +" "+ str(r.status) + " " + r.reason)
            # build dictionary
            url_dict = {}
            url_dict['response'] = resp_str
            url_dict['url'] = r.getheader('location')
            url_dict['header'] = r.msg.headers
            seen[url] = url_dict
            return url_dict


    # private function to get response
    def __get_r(scheme, server, path):
        if scheme.upper() == 'HTTPS':
            self.connection = httplib.HTTPSConnection(self.server, 80)
        elif scheme.upper() == 'HTTP':
            self.connection = httplib.HTTPConnection(self.server, 80)
        else:
            raise NotHTTP("Link must be HTTP(S), not " + o.scheme)
        self.connection.request("HEAD", self.path)
        self.response = self.connection.getresponse()
        self.connection.close()

# Exception to use in case of not HTTP link
class NotHTTP(Exception):
    pass
