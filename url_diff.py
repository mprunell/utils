import sys
import getopt
import traceback
import urllib2
from urlparse import urljoin, urlparse, ParseResult
from BeautifulSoup import BeautifulSoup

def connect(conn, url):

    assert conn is not None, 'Input connection must be valid'
    assert url, 'Input old URL cannot be empty'

    response = None
    try:
        response = conn.open(url)
    except urllib2.HTTPError as e:
        error_msg = 'Error {} connecting to {}'.format(e.code, url)
        sys.stderr.write(repr(error_msg) + '\n')
    except urllib2.URLError as e:
        error_msg = 'Error {} connecting to {}'.format(e.reason, url)
        sys.stderr.write(repr(error_msg) + '\n')
    except:
        error_msg = 'Error connecting to {}'.format(url)
        sys.stderr.write(repr(error_msg) + '\n')

    return response

def crawl_page (conn, url, domain, visited_links=[]):

    assert conn is not None, 'Input connection must be valid'
    assert url, 'Input old URL cannot be empty'
    assert domain, 'Input old domain cannot be empty'
    assert isinstance(visited_links, list)

    visited_links.append(url)
    remaining_links = []
    title = ''
    meta_desc = ''
    response = connect(conn, url)
    if not response is None:
        body = response.read()
        try:        
            soup = BeautifulSoup(body)
        except:
            error_msg = 'Error parsing {}'.format(url)
            sys.stderr.write(error_msg + "\n")
            soup = None
        if not soup is None:
            if soup.html:
                if soup.html.head:
                    title = soup.html.head.title.string or ''
                else:
                    title =''
            else:
                title = ''
            meta_desc = soup.findAll(attrs={"name":"description"})
            if len (meta_desc) > 0:
                meta_desc = meta_desc[0]['content']
            else:
                meta_desc = ""
            if visited_links:
                anchors = soup.findAll("a")
                for anchor in anchors:
                    if anchor is None or not anchor.has_key('href'): continue
                    try:
                        href = anchor['href']
                        if domain in href or (not 'www' in href and not 'http' in href):
                            link = urljoin('http://' + domain, href).split ("#")[0].lower()
                            if not link in visited_links and link != '/' and not 'mailto' in link:
                                if not link in visited_links:
                                    if not '.pdf' in link.lower() \
                                        and not '.png' in link.lower() \
                                        and not '.jpg' in link.lower():
                                        remaining_links.append(link)
                    except:
                        print traceback.format_exc()
        
        print '{};{};{}'.format(url.encode('utf-8'), title.encode('utf-8').strip(' \n\t\r'), meta_desc.encode ('utf-8').strip(' \n\t\r'))

    assert visited_links, 'Output visited_links cannot be empty'

    return remaining_links, visited_links

def clean_scheme(url):

    assert url, 'Input URL cannot be empty'

    scheme = 'http://'
    sections = url.split(scheme)
    if len(sections) == 1:
        url = scheme + url

    assert url, 'Output URL cannot be empty'
    assert scheme in url, 'Output URL must have a scheme'

    return url

def replace_domain(source_url, new_domain):
    o = urlparse(source_url)

    return ParseResult(o.scheme, new_domain, o.path, o.params, o.query, o.fragment).geturl()
    
def find_differences(old_domain, new_domain, verbose=False):
    old_domain = unicode(old_domain)
    new_domain = unicode(new_domain)
    old_url = clean_scheme(old_domain)
    conn = urllib2.build_opener()
    visited_links = []
    remaining_links, visited_links = crawl_page(conn, old_url, old_domain, visited_links)
    new_url = replace_domain(old_url, new_domain)
    crawl_page(conn, new_url, new_domain)
    while True:
        if remaining_links:
            ln = remaining_links.pop()
            more_links, visited_links = crawl_page(conn, ln, old_domain, visited_links)
            new_ln = replace_domain(ln, new_domain)
            crawl_page(conn, new_ln, new_domain)
            remaining_links.extend(more_links)
        else:
            break
    
def main():
    
    old_domain = ''
    new_domain = ''
    version = '1.0'
    verbose = False
    help = False

    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'o:n:', ['old_domain=',
                                                                 'new_domain='
                                                                 'verbose',
                                                                 'help'
                                                                ])
    except getopt.GetoptError:
        sys.exit(2)

    option_not_found = False
    for opt, arg in options:
        if opt in ('-o', '--old'):
            old_domain = arg
        elif opt in ('-n', '--new'):
            new_domain = arg
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-h', '--help'):
            help = True
        else:
            option_not_found = True

    if not options or option_not_found or help:
        print 'Usage: {} -o <old_url> -n <new_url>'.format(sys.argv[0])
        if help:
            sys.exit(0)
        else:
            sys.exit(1)

    find_differences(old_domain, new_domain, verbose)
    
if __name__ == "__main__":
    main()

