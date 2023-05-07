from twisted.internet import reactor

from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
import sys

sys.path.append('C:\\Users\\Админ\\Desktop\\parsing\\parsing-scraping')
from project_parser_hh.spiders.hh_ru import HhRuSpider


if __name__ == '__main__':
    configure_logging()
    settings = get_project_settings()

    process = CrawlerProcess(settings)
    process.crawl(HhRuSpider)

    process.start()