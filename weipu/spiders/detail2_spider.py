import re
import hashlib

import pymongo
import scrapy
from lxml import etree
from scrapy import Spider

from weipu.items import JournalArtical

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'www.cqvip.com',
    'Pragma': 'no-cache',
    'Referer': 'www.cqvip.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    # 'User-Agent': 'User-Agent:Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0'
}

detail_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'www.cqvip.com',
    'Pragma': 'no-cache',
    'Referer': 'http://www.cqvip.com/QK/85504B/201707/',
    'Upgrade-Insecure-Requests': '1',
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    'User-Agent': 'User-Agent:Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0'
}
class detail2_spider(Spider):
    name = "detail2_spider"
    client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
    db = client['cqvip']
    p = re.compile("/QK/[\\d\\w]+/\\d+/(\\d+).html");

    def start_requests(self):
        print (self.db.journal_meta_url_20180301.find({'status': 0}).count())
        next_url = self.db.journal_meta_url_20180301.find_and_modify(query={'status': 0}, update=({'$set': {'status': 1}}))['url']
        print(next_url)
        yield scrapy.Request(url=next_url, meta={'url': next_url}, headers=headers,
                             callback=self.detail_parse)

    def detail_parse(self, response):
        print(response.status)
        try:
            print("111")
            if 200 != response.status:
                raise Exception("error url")
            item = response.meta['data']
            print(item)
            item['article_url'] = response.meta['article_url']
            title_cn = ''
            authors_cn = ''
            organizations = ''
            keywords_cn = ''
            abstract_cn = ''
            year = ''
            volume = ''
            issue = ''
            page = ''
            clcs = ''
            start_page = ''
            end_page = ''
            doc = etree.HTML(response.text)
            title_cn_nodes = doc.xpath('//meta[@name="citation_title"]')
            print ('爬取第一个数据成功！')
            if len(title_cn_nodes) > 0:
                title_cn = title_cn_nodes[0].xpath('@content')[0]
            authors_cn_nodes = doc.xpath('//meta[@name = "citation_author"]')
            if len(authors_cn_nodes) > 0:
                for author_node in authors_cn_nodes:
                    authors_cn += (author_node.xpath('@content')[0] + "；")
            organizations_nodes = doc.xpath('//strong/i/a[contains(@href,"aspx?o=")]')
            if len(organizations_nodes) > 0:
                for index in range(len(organizations_nodes)):
                    if 0 == (index % 2):
                        organizations += (organizations_nodes[index].text + "；")
            keywords_cn_nodes = doc.xpath('//form[@name="frmdata"]/input[@name = "keyword_c"]/@value')
            if len(keywords_cn_nodes) > 0:
                keywords_cn = keywords_cn_nodes[0]
            keywords_cn = re.sub(r'(\[(\d)+\]|\s+)', "", keywords_cn).replace(";", "；")
            abstract_cn_nodes = doc.xpath('//td[@class="sum"]')
            if len(abstract_cn_nodes) > 0:
                for abstract_cn_node in abstract_cn_nodes:
                    if "摘" in abstract_cn_node.xpath('./b/text()')[0]:
                        abstract_cn = abstract_cn_node.xpath('./text()')[1].strip()
                        break
            year_nodes = doc.xpath('//meta[@name="citation_date"]/@content')
            if len(year_nodes) > 0:
                year = year_nodes[0]
            issue_nodes = doc.xpath('//meta[@name="citation_issue"]/@content')
            if len(issue_nodes) > 0:
                issue = issue_nodes[0]
            volume_nodes = doc.xpath('//form[@name = "frmdata"]/input[@name = "volumn"]/@value')
            if len(volume_nodes) > 0:
                volume = volume_nodes[0]
            start_page_nodes = doc.xpath('//meta[@name = "citation_firstpage"]/@content')
            if len(start_page_nodes) > 0:
                start_page = start_page_nodes[0]
            end_page_nodes = doc.xpath('//meta[@name = "citation_lastpage"]/@content')
            if len(end_page_nodes) > 0:
                end_page = end_page_nodes[0]
            if (end_page is not None) and (start_page is not None):
                page = start_page + "-" + end_page
            clcs_nodes = doc.xpath('//form[@name = "frmdata"]/input[@name = "classtype"]/@value')
            if len(clcs_nodes) > 0:
                clcs = clcs_nodes[0].replace(" ", "；")
            item['title_cn'] = title_cn
            item['authors_cn'] = authors_cn
            item['organizations'] = organizations
            item['keywords_cn'] = keywords_cn
            item['abstract_cn'] = abstract_cn
            item['year'] = year
            item['issue'] = issue
            item['volume'] = volume
            item['page'] = page
            item['clcs'] = clcs
            hash = hashlib.md5()
            hash.update(item['article_url'].encode('utf-8'))
            item['md5'] = hash.hexdigest()
            yield item
        except:
            error_url = response.meta['url']
            print('error url ' + error_url)
            self.db.error_article_urls.insert({'error_url': error_url})

    def detail2_parse(self, response):
        try:
            if response.status != 200:
                raise Exception("error url" + response.meta['url'])
            journal_cn = ''
            journal_en = ''
            isCore = None
            issn = ''
            cn = ''
            publisher = ''
            doc = etree.HTML(response.text)
            journal_cn_nodes = doc.xpath('//h1[@class="f20 heiti normal black"]')
            if len(journal_cn_nodes) > 0:
                journal_cn = journal_cn_nodes[0].text
            journal_en_nodes = doc.xpath('//h1[@class="f10 tahoma normal gray"]')
            if len(journal_en_nodes) > 0:
                journal_en = journal_en_nodes[0].text
            isCore_nodes = doc.xpath('//li[@class = "f12"]/img[@class = "cores"]')
            if len(isCore_nodes) > 0:
                isCore = 1
            detail_nodes = doc.xpath('//ul[@class = "wow"]/li/b')
            item = None
            for node in detail_nodes:
                if node.text == "主办单位：":
                    publisher = node.xpath('../text()')[0].replace(' ', '；')
                if node.text == "国内统一刊号：":
                    cn = node.xpath('../text()')[0]
                if node.text == "国际标准刊号：":
                    issn = node.xpath('../text()')[0]
                item = JournalArtical()
                item['journal_cn'] = journal_cn
                item['journal_en'] = journal_en

                item['issn'] = issn
                item['cn'] = cn
                item['isCore'] = False if isCore is None else True
                item['publisher'] = publisher
            article_nodes = doc.xpath('//em/a/@href')
            for node in article_nodes:
                article_url = "http://www.cqvip.com" + node
                item['article_url'] = article_url
                m = self.p.match(node)
                try:
                    item['identifier'] = m.group(1)
                except:
                    pass
                print(item)
                #yield item
                # yield scrapy.Request(url=article_url, meta={'data': item, 'article_url': article_url},
                #                      headers=detail_headers,
                #                      callback=self.detail_parse)
        except Exception as e:
            error_url = response.meta['url']
            print("error url:" + error_url)
            self.db.journal_urls.update({'url': error_url}, {'check', 2})
        next_url = self.db.journal_urls.find_and_modify(query={'check': 0}, update=({'$set': {'check': 1}}))['url']
        yield scrapy.Request(url=next_url, headers=headers, callback=self.detail2_parse)
