from urlparse import urlparse
import httplib

# this class will return the end url of a link shortener
# works with multi-level shortening
class short_request():

    __slots__ = ['use_secure','server','path','connection','response']
    # to initialize, parse the given url into parts for later request
    # undefined behavior for url without server
    def __init__(self,url):
        o = urlparse(url)
        if o.scheme == 'https':
            self.use_secure = True
        else:
            self.use_secure = False
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

    def get_response(self):
        if self.response is None:
            self.__get_response()
        resp_str = ("HTTP/" + str(self.response.version)[0:1] + "."
                + str(self.response.version)[1:2] + " "
                + str(self.response.status) + " " + self.response.reason)
        return resp_str

    def get_url(self):
        if self.response is None:
            self.__get_response()
        return self.response.getheader('location')

    def get_header(self):
        if self.response is None:
            self.__get_response()
        return self.response.msg.headers

def main():
    req = short_request("http://goo.gl/N67DsV")
    print req.get_response()
    print req.get_url()

if __name__ == "__main__":
    main()
