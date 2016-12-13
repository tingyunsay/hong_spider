# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field

class CollectorSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    lost_mid = Field()
    lost_url = Field()
    lost_from = Field()
    lost_id = Field()
    lost_title = Field()
    lost_describe = Field()
    lost_person = Field()
    lost_time = Field()
    lost_location = Field()
