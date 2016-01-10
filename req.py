from urlparse import urlparse
import httplib

# this class will return the end url of a link shortener
# works with multi-level shortening
class link_lengthener():

    # to initialize, parse the given url into parts for later request
    # undefined behavior for url without server
    def __init__(self,url):
        # url needs to start with http(s) for parser to work
        if "://" not in url:
            url = "http://" + url
        o = urlparse(url)
        if o.scheme == 'https':
            self.use_secure = True
        elif o.scheme == 'http':
            self.use_secure = False
        else:
            raise NotHTTP("Link must be HTTP(S), not " + o.scheme)
        self.server = o.netloc
        if o.path == '':
            self.path = '/'
        else:
            self.path = o.path
        # init empty connection and response for later use
        self.connection = None
        self.response = None

    # private function to get response, actual querying is lazy
    def __get_response(self):
        if self.use_secure:
            self.connection = httplib.HTTPSConnection(self.server, 80)
        else:
            self.connection = httplib.HTTPConnection(self.server, 80)
        self.connection.request("HEAD", self.path)
        self.response = self.connection.getresponse()
        self.connection.close()

    # get the response message
    def get_response(self):
        if self.response is None:
            self.__get_response()
        resp_str = ("HTTP/" + str(self.response.version)[0:1] + "."
                + str(self.response.version)[1:2] + " "
                + str(self.response.status) + " " + self.response.reason)
        return resp_str

    # get the end url
    def get_url(self):
        if self.response is None:
            self.__get_response()
        return self.response.getheader('location')

    # get list of header elements
    def get_header(self):
        if self.response is None:
            self.__get_response()
        return self.response.msg.headers

# Exception to use in case of not HTTP link
class NotHTTP(Exception):
    pass
