import hashlib
import re

from lxml import etree

import pymongo
import scrapy
from weipu.items import JournalArtical
from scrapy import Spider


class image_spider(Spider):
    name = "image_spider"
    client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
    db = client['meta_journal']

    def start_requests(self):
        info = self.db.vip.find_and_modify(query={'check': 0}, update=({'$set': {'check': 1}}))
        item = JournalArtical()
        next_url = 'http://60.171.75.82:82/ZK/detail.aspx?id=' + info['identifier']
        article_url = info['article_url']
        journal_code = re.compile('http://www.cqvip.com/QK/([\\d\\w]+)').match(article_url).group(1)
        item['title_url'] = article_url
        item['journal_cn'] = info['journal_cn']
        item['journal_en'] = info['journal_en']
        item['issn'] = info['issn']
        item['cn'] = info['cn']
        item['publisher'] = info['publisher']
        item['isCore'] = info['isCore']

        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': '60.171.75.82:82',
            'Pragma': 'no-cache',
            'Referer': 'http://60.171.75.82:82/ZK/journal.aspx?q=/' + journal_code + '/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        yield scrapy.Request(url=next_url,dont_filter=True, headers=header, meta={'data': item, '_id': info['_id']},
                             callback=self.journal_parse)

    def journal_parse(self, response):
        try:
            if 200 == response.status:
                item = response.meta['data']
                title_cn = ''
                title_en = ''
                authors_cn = ''
                authors_en = ''
                organizations = ''
                keywords_cn = ''
                keywords_en = ''
                abstract_cn = ''
                abstract_en = ''
                year = ''
                issue = ''
                page = ''
                clcs = ''
                # print('root--->%s'%len(etree.HTML(response.text).xpath('//div[@class="article_detail"]')))
                root = etree.HTML(response.text).xpath('//div[@class="article_detail"]')[0]
                journal_cn_node = root.xpath('./h1/text()')
                if len(journal_cn_node) > 0: title_cn = journal_cn_node[0]
                journal_en_node = root.xpath('./em/text()')
                if len(journal_en_node) > 0: title_en = journal_en_node[0]

                detail_root = root.xpath('./span')
                for i in range(len(detail_root)):
                    span_node = detail_root[i]
                    class_node = span_node.xpath('./@class')
                    if len(class_node) > 0:
                        class_value = class_node[0]
                        if "author" == class_value:
                            authors_cn = re.sub('(作　　者：|\[\\d+\])', '', span_node.xpath('string(.)').replace(';', '；'))
                            continue
                        if "org" == class_value:
                            organizations = re.sub('(机构地区：|\[\\d+\])', '',
                                                   re.sub(',\S+\s+', '；', span_node.xpath('string(.)')))
                            continue
                        if "from" == class_value:
                            text = re.sub('(出　　处：《(\\S)+》\\s?)', '', span_node.xpath('string(.)'))
                            p = re.compile('(\\d+)年第(\\d+)期\\s([\\d-]+)')
                            m = p.match(text)
                            if m is not None:
                                year = m.group(1)
                                issue = m.group(2)
                                page = m.group(3)
                            continue
                        if "abstrack" == class_value:
                            abstract_cn = span_node.xpath('string(.)').replace('摘　　要：', '')
                            continue
                        if "keywords" == class_value:
                            keywords_cn = span_node.xpath('string(.)').replace('关键词：', '').replace('  ', '；')
                            continue
                        if "class" == class_value:
                            clcs = span_node.xpath('./a/b/text()')[0]
                            continue
                        if 'en' == class_value:
                            front_class = detail_root[i - 1].xpath('./@class')[0]
                            if 'author' == front_class:
                                authors_en = span_node.xpath('string(.)')
                            if 'abstrack' == front_class:
                                abstract_en = re.sub('\\s+', ' ', span_node.xpath('string(.)'))
                                continue
                            if 'keywords' == front_class:
                                keywords = re.split(' ;', span_node.xpath('string(.)'))
                                if len(keywords) > 0:
                                    for keyword in keywords:
                                        if len(item) > 0:
                                            keywords_en += (keyword.strip() + "；")
                                continue
                    else:
                        raise Exception()
                item['title_cn'] = title_cn
                item['title_en'] = title_en
                item['authors_cn'] = authors_cn
                item['authors_en'] = authors_en
                item['organizations'] = organizations
                item['keywords_cn'] = keywords_cn
                item['keywords_en'] = keywords_en
                item['abstract_cn'] = abstract_cn
                item['abstract_en'] = abstract_en
                item['year'] = year
                item['issue'] = issue
                item['page'] = page
                item['clcs'] = clcs
                item['abstract_en'] = abstract_en
                hash_code = hashlib.md5()
                hash_code.update(item['title_url'].encode('utf-8'))
                item['md5'] = hash_code.hexdigest()
                yield item
            else:
                print('<----网页错误:%s----->'%response.status)
                raise Exception()
        except Exception as e:
            print(e)
            
            print(response.meta['data']['title_url'])
            _id = response.meta['_id']
            self.db.vip.update({'_id': _id}, {'$set': {'check': 2}})
        info = self.db.vip.find_and_modify(query={'check': 0}, update=({'$set': {'check': 1}}))
        item2 = JournalArtical()
        next_url = 'http://60.171.75.82:82/ZK/detail.aspx?id=' + info['identifier']
        article_url = info['article_url']
        journal_code = re.compile('http://www.cqvip.com/QK/([\\d\\w]+)').match(article_url).group(1)
        item2['title_url'] = article_url
        item2['journal_cn'] = info['journal_cn']
        item2['journal_en'] = info['journal_en']
        item2['issn'] = info['issn']
        item2['cn'] = info['cn']
        item2['publisher'] = info['publisher']
        item2['isCore'] = info['isCore']

        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': '60.171.75.82:82',
            'Pragma': 'no-cache',
            'Referer': 'http://60.171.75.82:82/ZK/journal.aspx?q=/' + journal_code + '/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        yield scrapy.Request(url=next_url, dont_filter=True,headers=header, meta={'data': item2, '_id': info['_id']},
                             callback=self.journal_parse)
