from __future__ import print_function
import urllib, json
from urlparse import urljoin

from scrapy.utils.jsonrpc import jsonrpc_client_call  #, JsonRpcError



class CrawlerRPC(object):

    def __init__(self, spider_name=None, host='localhost', port=6080):
        self.host = host
        self.port = port
        self.spider_name = spider_name

    def stop(self, spider_name=None):
        """Stop the named running spider, or the first spider found, if spider_name is None"""
        if spider_name is None:
            spider_name = self.spider_name
        else:
            self.spider_name = spider_name
        if self.spider_name is None:
            self.spider_name = self.list_running()[0].split(':')[-1]
        self.jsonrpc_call('crawler/engine', 'close_spider', self.spider_name)

    def list_running(self):
        """List of running spiders"""
        return self.json_get('crawler/engine/open_spiders')

    def list_available(self):
        """List names of available spiders"""
        return self.jsonrpc_call('crawler/spiders', 'list')

    def list_resources(self):
        """list-resources - list available web service resources"""
        return self.json_get('')['resources']

    def get_spider_stats(self, spider_name):
        """get-spider-stats <spider> - get stats of a running spider"""
        if spider_name is None:
            spider_name = self.spider_name
        else:
            self.spider_name = spider_name
        if self.spider_name is None:
            self.spider_name = self.list_running()[0].split(':')[-1]
        return(self.jsonrpc_call('stats', 'get_stats', self.spider_name))

    def get_global_stats(self):
        """get-global-stats - get global stats"""
        return self.jsonrpc_call('stats', 'get_stats')

    def get_wsurl(self, path='', host=None, port=None):
        if host is None:
            host = self.host
        else:
            self.host = host
        if port is None:
            port = self.port
        else:
            self.port = port
        return urljoin("http://%s:%s/"% (host, port), path)

    def jsonrpc_call(self, path='', method='', spider_name=None, host=None, port=None):
        url = self.get_wsurl(path=path, host=host, port=port)
        print(repr((url, method, spider_name)))
        if spider_name is None:
            return jsonrpc_client_call(url, method)
        else:
            return jsonrpc_client_call(url, method, spider_name)

    def json_get(self, path, host=None, port=None):
        url = self.get_wsurl(path=path, host=host, port=port)
        return json.loads(urllib.urlopen(url).read())

