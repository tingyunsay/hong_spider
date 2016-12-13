# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import codecs
import json

import MySQLdb.cursors
from scrapy.exceptions import DropItem
from scrapy import log

from twisted.enterprise import adbapi
import datetime
from scrapy import log
from scrapy.exceptions import DropItem
import redis
from pybloomfilter import BloomFilter
import time
import os
from scrapy import log
import logging
import re
import datetime
from scrapy.exceptions import CloseSpider

class FilterPipeline(object):
	def __init__(self):
		self.bloomname = "filter"
		self.f = open("./log.txt",'a')
		self.now = time.time()
		self.one_month_ago = datetime.datetime(time.localtime(self.now).tm_year,time.localtime(self.now).tm_mon-1,time.localtime(self.now).tm_mday)
		
	def open_spider(self,spider):
		self.bloomname = "filter"
		isexists = os.path.exists(self.bloomname+".bloom")
		if isexists == True:
			self.bf = BloomFilter.open(self.bloomname+".bloom")
		else:
			self.bf = BloomFilter(100000000,0.001,self.bloomname+".bloom")
	def process_item(self,item,spider):
		token = str(item['lost_url'])+"----"+str(item['lost_id'])+"----"+str(item['lost_describe'])
		time_temp = re.search(r'\d+-\d+-\d+',str(item['lost_time'])).group()
		time_stamp = datetime.datetime(int(re.search(r'\d+',time_temp).group()),int(re.search(r'(?<=-)\d+',time_temp).group()),int(re.search(r'\d+$',time_temp).group()))
		print time.localtime(self.now)	
		
		if time.mktime(time_stamp.timetuple()) < time.mktime(self.one_month_ago.timetuple()):
			#print >> self.f,"At Time %s , the item[%s] : the datetime is overtimed._____________"%(time.ctime(),token)
			raise DropItem("****************************The datetime is overtimed!!!!!")
		flag = self.bf.add(token)
		if flag == False:
			return item
		#这里表示：如果没有重复，item接着放到下面的pipeline类中处理
		else:
			#print >> self.f,"At Time %s , the item[%s] is overread url , Not Allowed._____________"%(time.ctime(),token)
			#raise CloseSpider('At time %s , Spider has been destroied_____________'%time.ctime())
			raise DropItem("****************************is the overread url!!!!!")
			#time.sleep(10)
		
class Collector_SpiderPipeline(object):
    def __init__(self):
	self.file = codecs.open('tempfile.json','wb',encoding="utf-8")
	
    def process_item(self, item, spider):
	line = json.dumps(dict(item),ensure_ascii=False)+"\n"
	self.file.write(line)
	return item

class SQLPipeline(object):
	def __init__(self):
		self.f = open("./log.txt",'a')
		self.dbpool=adbapi.ConnectionPool('MySQLdb',
			host='127.0.0.1',
			db='weibo_lost',
			user='root',
			passwd='liaohong',
			cursorclass=MySQLdb.cursors.DictCursor,
			charset='utf8',
			use_unicode=True)
    	def process_item(self,item,spider):
		query=self.dbpool.runInteraction(self.conditional_insert,item)
		query.addErrback(self.handle_error)
		return item
    	def conditional_insert(self,tx,item):
		#print >> self.f,"At Time %s , lost_location = %s._____________"%(time.ctime(),item['lost_location'])
		tx.execute(\
		"insert into lost(lost_mid,lost_url,lost_from,lost_id,lost_title,lost_describe,lost_person,lost_time,lost_location)\
		values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
		(item['lost_mid'],
		item['lost_url'],
		item['lost_from'],
		item['lost_id'],
		item['lost_title'],
		item['lost_describe'],
		item['lost_person'],
		item['lost_time'],
		item['lost_location']
		))
    	def handle_error(self,e,item):
		print >> self.f,"At Time %s , int url : %s ,there is a error : %s._____________"%(time.ctime(),item['lost_url'],e)
		self.f.close()
		log.err(e)



