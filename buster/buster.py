"""Ghost Buster. Static site generator for Ghost.

Usage:
  buster.py generate [--domain=<local-address>] [--dir=<path>]
  buster.py (-h | --help)
  buster.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  --dir=<path>              Absolute path of directory to store static pages.
  --domain=<local-address>  Address of local ghost installation [default: localhost:2368].
"""
import os
import re
import fnmatch
from docopt import docopt
from pyquery import PyQuery

def main():
    arguments = docopt(__doc__, version='0.1.3')
    if arguments['--dir'] is not None:
        static_path = arguments['--dir']
    else:
        static_path = os.path.join(os.getcwd(), 'static')

    if arguments['generate']:
        command = ("wget "
                   "--recursive "             # follow links to download entire site
                   "--convert-links "         # make links relative
                   "--page-requisites "       # grab everything: css / inlined images
                   "--no-parent "             # don't go to parent level
                   "--directory-prefix {1} "  # download contents to static/ folder
                   "--no-host-directories "   # don't create domain named folder
                   "--restrict-file-name=unix "  # don't escape query string
                   "{0}").format(arguments['--domain'], static_path)
        os.system(command)

        # remove query string since Ghost 0.4
        file_regex = re.compile(r'.*?(\?.*)')
        for root, dirs, filenames in os.walk(static_path):
            for filename in filenames:
                if file_regex.match(filename):
                    newname = re.sub(r'\?.*', '', filename)
                    print "Rename", filename, "=>", newname
                    os.rename(os.path.join(root, filename), os.path.join(root, newname))

        # remove superfluous "index.html" from relative hyperlinks found in text
        abs_url_regex = re.compile(r'^(?:[a-z]+:)?//', flags=re.IGNORECASE)
        def fixLinks(text, parser):
            d = PyQuery(bytes(bytearray(text, encoding='utf-8')), parser=parser)
            for element in d('a'):
                e = PyQuery(element)
                href = e.attr('href')
                if not abs_url_regex.search(href):
                    new_href = re.sub(r'rss/index\.html$', 'rss/index.rss', href)
                    new_href = re.sub(r'/index\.html$', '/', new_href)
                    new_href = re.sub(r'index\.html$', '.', new_href)
                    e.attr('href', new_href)
                    print "\t", href, "=>", new_href
            for element in d('link'):
                e = PyQuery(element)
                href = e.attr('href')
                if href is not None and not abs_url_regex.search(href):
                    new_href = re.sub(r'rss/index\.html$', 'rss/index.rss', href)
                    new_href = re.sub(r'\?v=.*$', '', href)
                    e.attr('href', new_href)
                    print "\t", href, "removed v =>", new_href
            for element in d('script'):
                e = PyQuery(element)
                href = e.attr('src')
                if href is not None and not abs_url_regex.search(href):
                    new_href = re.sub(r'\?v=.*$', '', href)
                    e.attr('src', new_href)
                    print "\t", href, "removed v =>", new_href
            if parser == 'html':
                return "<!DOCTYPE html>" + d.html(method='html').encode('utf8')
            return d.__unicode__().encode('utf8')

        # fix links in all html files
        for root, dirs, filenames in os.walk(static_path):
            for filename in fnmatch.filter(filenames, "*.html"):
                filepath = os.path.join(root, filename)
                parser = 'html'
                if root.endswith("/rss"):  # rename rss index.html to index.rss
                    parser = 'xml'
                    newfilepath = os.path.join(root, os.path.splitext(filename)[0] + ".rss")
                    os.rename(filepath, newfilepath)
                    filepath = newfilepath
                with open(filepath) as f:
                    filetext = f.read().decode('utf8')
                print "fixing links in ", filepath
                newtext = fixLinks(filetext, parser)
                with open(filepath, 'w') as f:
                    f.write(newtext)
    else:
        print __doc__

if __name__ == '__main__':
    main()
