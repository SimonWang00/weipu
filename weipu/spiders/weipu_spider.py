import scrapy
from scrapy import Spider
import json
from lxml import etree

from weipu.items import WeipuItem


class Weipu(Spider):
    name = "weipu_spider"

    listHeader = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': 'www.cqvip.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    currentNum = 1
    totalPageNum = 943

    list_url = "http://www.cqvip.com/data/main/search.aspx?action=so&tid=7&k=&w=&o=&mn=&issn=&cnno=&rid=0&c=&gch=&cnt=&perpage=0&ids="

    def start_requests(self):
        yield scrapy.Request(url=self.list_url, meta={}, headers=self.listHeader, callback=self.list_parse)

    def list_parse(self, response):
        text = json.loads(response.text)
        message = text['message']
        tree = etree.HTML(message)
        # print(totalPageNum)
        nodes = tree.xpath("//th[@rowspan]/a/@href")
        for node in nodes:
            item = WeipuItem()
            item['url'] = node
            yield item
        self.currentNum += 1
        if self.currentNum < self.totalPageNum:
            url = "http://www.cqvip.com/data/main/search.aspx?action=so&tid=7&k=&w=&o=&mn=&issn=&cnno=&rid=0&c=&gch=&cnt=&curpage=%d&perpage=0&ids=" % (
                self.currentNum)
            yield scrapy.Request(url=url, meta={}, headers=self.listHeader, callback=self.list_parse)
