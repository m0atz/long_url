import httplib
import urlparse
import sys
import fileinput
import requests
import json
import getopt
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

# # 
# main:
# parse args and ensure usage.
# unshorten the URL using the 'request' library and follow redirects.
# if -b is selected them perform a bluecoat lookup on the final URL in the hop and display.
# else, just print the final result.
# #
def main(argv):
    inputfile = ''
    bluecoat  = False
    
    # parse args and ensure correct usage
    try:
      opts, args = getopt.getopt(argv,"hi:b",["ifile=","bluecoat"])
    except getopt.GetoptError:
        print "Usage : " + sys.argv[0] + " -i inputfile [--bluecoat]"
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print "Usage : " + sys.argv[0] + " -i inputfile [--bluecoat]"
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-b", "--bluecoat"):
            bluecoat = True

    # iterate each line in the input file
    for line in fileinput.input([inputfile]):
        line = line.rstrip('\n')
        try:
            # unshorten the url
            url = unshorten_url(line)
            # determine whether to display bluecoat cat or not
            if (not bluecoat):
                print line, "-->", url
            elif (bluecoat):
                s = SiteReview()
                response = s.sitereview(url)
                cat = BeautifulSoup(response["categorization"], "lxml").get_text()
                print line, "-->", url, "["+cat+"]"
        # handle errors, semi-gracefully :)
        except:
            print "Skipping over " + line
            pass

if __name__ == "__main__":
    main(sys.argv[1:])