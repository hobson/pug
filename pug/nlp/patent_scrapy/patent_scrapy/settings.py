# Scrapy settings for patent_scrapy project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'patent_scrapy'

SPIDER_MODULES = ['patent_scrapy.spiders']
NEWSPIDER_MODULE = 'patent_scrapy.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'patent_scrapy (+http://www.yourdomain.com)'
