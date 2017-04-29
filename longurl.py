import httplib
import urlparse
import sys
import fileinput
import requests
import json
from bs4 import BeautifulSoup

# perform a lookup of the site against Bluecoat and return the current category
# note: Bluecoat will rate-limit you if there are lots of requests.
class SiteReview(object):
    def __init__(self):
        self.baseurl = "http://sitereview.bluecoat.com/rest/categorization"
        self.useragent = {"User-Agent": "Mozilla/5.0"}

    def sitereview(self, url):
        payload = {"url": url}
        
        try:
            self.req = requests.post(self.baseurl,headers=self.useragent,data=payload)
        except requests.ConnectionError:
            sys.exit("[-] ConnectionError: A connection error occurred")

        return json.loads(self.req.content)

# unshorten routine taken from here
# http://stackoverflow.com/questions/7153096/how-can-i-un-shorten-a-url-using-python/7153185#7153185
def unshorten_url(url):
    parsed = urlparse.urlparse(url)
    if parsed.scheme == 'https':
        h = httplib.HTTPSConnection(parsed.netloc)
    else:
        h = httplib.HTTPConnection(parsed.netloc)
    resource = parsed.path
    if parsed.query != "": 
        resource += "?" + parsed.query
    h.request('HEAD', resource )
    response = h.getresponse()
    if response.status/100 == 3 and response.getheader('Location'):
        return unshorten_url(response.getheader('Location')) # changed to process chains of short urls
    else:
        return url 

# iterate the input file, strip lines, follow the redirects and lookup in Bluecoat.
# tries to handle errors gracefully :)
def main(argv):
    inputfile = ''
    # ensure correct usage
    if len(sys.argv) < 2:
        print "Usage : " + sys.argv[0] + " <inputfile>"
        sys.exit(1)
    else:
        inputfile = sys.argv[1]

    # iterate each line in the input file
    for line in fileinput.input([inputfile]):
        line = line.rstrip('\n')
        # use try, except pass to skip over any errors
        try:
            url = unshorten_url(line)
            s = SiteReview()
            response = s.sitereview(url)
            # print response
            cat = BeautifulSoup(response["categorization"], "lxml").get_text()
            print line, "-->", url, "["+cat+"]"
        except:
            print "Skipping over " + line
            pass

if __name__ == "__main__":
    main(sys.argv[1:])