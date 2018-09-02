# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class WeipuItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = Field()


class JournalDetail(Item):
    url = Field()


class ArticleItem(Item):
    url = Field()


class JournalArtical(Item):
    journal_cn = Field()
    journal_en = Field()
    issn = Field()
    cn = Field()
    isCore = Field()
    publisher = Field()
    identifier = Field()
    title_cn = Field()
    title_en = Field()
    title_url = Field()
    authors_cn = Field()
    authors_en = Field()
    abstract_cn = Field()
    abstract_en = Field()
    organizations = Field()
    keywords_cn = Field()
    keywords_en = Field()
    year = Field()
    volume = Field()
    issue = Field()
    page = Field()
    clcs = Field()
    md5 = Field()
