from lxml import etree

import scrapy
from scrapy import Spider
import pymongo

from weipu.items import JournalDetail

detailHeader = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'www.cqvip.com',
    'Pragma': 'no-cache',
    'Referer': 'http://www.cqvip.com/main/search.aspx?tid=7',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/60.0.3112.90 Safari/537.36 '
}


class detail_spider(Spider):
    name = "journal_spider"
    client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
    db = client['weipu']

    def start_requests(self):
        next_url = self.db.list_urls.find_and_modify(query={'check': 0}, update=({'$set': {'check': 1}}))['url']
        yield scrapy.Request(url=next_url, headers=detailHeader, callback=self.detail_parse)

    def detail_parse(self, response):
        try:
            nodes = etree.HTML(response.text).xpath('//ol[@class="date"]/li/i')
            # print(response.text)
            for node in nodes:
                item = JournalDetail()
                if int(node.text) >= 2015:
                    parent = node.xpath("../a/@href")
                    for child in parent:
                        item['url'] = "http://www.cqvip.com" + child
                        # print(item['url'])
                        yield item
                else:
                    break
        except:
            pass
        next_url = self.db.list_urls.find_and_modify(query={'status': 0}, update=({'$set': {'status': 1}}))['url']
        if next_url is not None:
            yield scrapy.Request(url=next_url, headers=detailHeader, callback=self.detail_parse)
