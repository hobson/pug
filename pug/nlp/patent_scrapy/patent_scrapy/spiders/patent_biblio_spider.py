from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from wikiscrapy.items import WikiItem
from datetime import datetime
from collections import Counter

from pug.nlp.strutil import get_words, clean_wiki_datetime
from pug.nlp.util import listify
from pug.nlp import regex_patterns as RE

URL_TRADEMARK_INFO_PREFIX = r'https://tsdrapi.uspto.gov/ts/cd/casestatus/sn'
URL_RE_TRADEMARK_INFO_PREFIX = r'https\:\/\/tsdrapi\.uspto\.gov\/ts\/cd\/casestatus\/sn'
URL_RE_TRADEMARK_INFO_SUFFIX = r'[0-9]{8}\/info\.xml'
URL_RE_TRADEMARK_INFO = URL_RE_TRADEMARK_INFO_PREFIX + URL_RE_TRADEMARK_INFO_SUFFIX
URL_RE_GOOGLE_PATENT_BIBLIO_ZIP = r'https?\:\/\/storage\.googleapis\.com\/patents\/appl_bib\/2014\/ipab20[0-2][0-9][01][0-9][0123][0-9]_wk[0-5][0-9]\.zip'

#from time import sleep

class PatentBiblioSpider(CrawlSpider):
    """Crawls google's "bulk download" patent api to retreive and unzip bibliography files. 

    Rate limited by obeying robots.txt (see settings.py), autothrottle

    $ cd nlp/wikiscrapy
    $ scrapy crawl wiki -o wikipedia_erdos.json -t json

    >>> import subprocess
    >>> subprocess.check_output('scrapy', 'crawl', 'wiki', stderr=subprocess.STDOUT)

    """

    verbosity = 1
    name = 'wiki'
    download_delay = 1.1
    allowed_domains = ['en.wikipedia.org', 'en.wiktionary.org']  # , 'en.m.wikipedia.org']
    #start_urls = [r'http://www.google.com/googlebooks/uspto-patents-applications-biblio.html']
    rules = [
        Rule(SgmlLinkExtractor(allow=[URL_RE_GOOGLE_PATENT_BIBLIO_ZIP]), follow=True, process_links='filter_links', callback='parse_response'),
        #Rule(SgmlLinkExtractor(allow=['/wiki/.*']), 'parse_response')]
        ]

    def __init__(self, start_urls=None, *args, **kwargs):
        self.start_urls = [r'http://www.google.com/googlebooks/uspto-patents-applications-biblio.html']
        if start_urls:
            self.start_urls = listify(start_urls)
        super(PatentBiblioSpider, self).__init__(*args, **kwargs)


    def clean_list(self, l):
        ans = ['']
        for item in l:
            # TODO: regex to see if it's a number of the form 1.2.3 before creating a new line item
            # and use the section number as a key or value in a dictionary
            stripped = item.strip()
            if stripped:
                ans[-1] += stripped + ' '
            if item.endswith('\n'):
                ans[-1] = ans[-1].strip()
                ans += ['']
        return ans


    def filter_links(self, links):
        filtered_list = []
        for link in links:
            if not RE.wikipedia_special.match(link.url):
                filtered_list += [link]
        if self.verbosity > 1:
            print '-'*20 + ' LINKS ' + '-'*20
            print '\n'.join(link.url for link in filtered_list)
        # sleep(1.1)
        if self.verbosity > 1:
            print '-'*20 + '-------' + '-'*20
        return filtered_list

    def parse_response(self, response):
        # TODO: 
        #   1. check for error pages and slowdown or halt crawling
        #   2. throttle based on robots.txt
        #   3. save to database (so that json doesn't have to be loaded manually)
        #   4. use django Models rather than scrapy.Item model
        #   5. incorporate into a django app (or make it a django app configurable through a web interface)
        #   6. incrementally build occurrence matrix rather than saving raw data to django/postgres db
        if self.verbosity > 1:
            print '='*20 + ' PARSE ' + '='*20
        sel = Selector(response)
        a = WikiItem()
        a['url'] = response.url
        a['title'] = ' '.join(sel.xpath("//h1[@id='firstHeading']//text()").extract())
        a['toc'] = ' '.join(self.clean_list(sel.xpath("//div[@id='toc']//ul//text()").extract()))
        a['text'] = ' '.join(sel.xpath('//div[@id="mw-content-text"]//text()').extract())
        a['modified'] = clean_wiki_datetime(sel.xpath('//li[@id="footer-info-lastmod"]/text()').re(r'([0-9]+\s*\w*)'))
        a['crawled'] = datetime.now()
        a['count'] = dict(Counter(get_words(a['text'])))
        if self.verbosity > 1:
            print '='*20 + '=======' + '='*20
        yield a
