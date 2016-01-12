from urlparse import urlparse
import httplib

# this class will return the end url of a link shortener
# does not work with multi-level shortening (un-covered border case)
class link_lengthener():

    # initialize dictionary to optimize against re-querying
    def __init__(self):
        self.seen = {}

    # Parameters:
    # url: string of url to extend
    def extend(self, url):
        # url needs to start with http(s) for parser to work
        if "://" not in url:
            url = "http://" + url
        o = urlparse(url)
        path = '/' if o.path=='' else o.path
        # check to see if url has already been queried
        if (o.netloc + path) in self.seen:
            return self.seen[o.netloc + path]
        # else check to see if website has served many unshortened links
        elif (o.netloc in no_redirects) and no_redirects[o.netloc] == 3:
            url_dict = {}
            url_dict['response'] = "HTTP/1.1 200 OK
            url_dict['url'] = url
        # else query server and get response
        else:
            r = get_r(o.scheme, o.netloc, path)
            resp_str = ("HTTP/" + str(r.version)[0:1] + "."
                    + str(r.version)[1:2] +" "+ str(r.status) + " " + r.reason)
            # build dictionary
            url_dict = {}
            url_dict['response'] = resp_str
            # if the status code indicates a re-direct (3xx)
            if r.status / 100 == 3:
                url_dict['url'] = r.getheader('location')
            # if status code indicates OK (1xx or 2xx)
            elif r.status / 100 in (1,2):
                url_dict['url'] = o.scheme + "://" + o.netloc + path
                # keep track of servers that don't redirect
                if o.netloc in no_redirects:
                    no_redirects[o.netloc] += 1
                else:
                    no_redirects[o.netloc] = 1
            # if status code indicates req or server error (4xx or 5xx)
            # of if server returns invalid status code
            else:
                url_dict['url'] = ''

        # add info to seen and return
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
