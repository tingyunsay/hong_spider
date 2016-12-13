
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import codecs
import json

import datetime
#import MySQLdb.cursors
from scrapy.exceptions import DropItem
from scrapy import log
import twisted
from twisted.enterprise import adbapi
from scrapy import log
from scrapy.exceptions import DropItem
import redis
from pybloomfilter import BloomFilter
import time
import os
from scrapy import log
#import logging
import re
from scrapy.exceptions import CloseSpider
from elasticsearch import Elasticsearch


#匹配物品关键字
def get_thing_array(items):
	res = []
	for k in thing_array.keys():
			for i in thing_array[k].keys():
					for j in thing_array[k][i]:
							if re.search(j,items):
									res.append(j)
	return res


class FilterPipeline(object):
		def __init__(self):
			self.bloomname = "filter"
			self.f = open("/home/hong/文档/sina_working/2to3_test/log.txt",'a')
			self.now = time.time()
			self.es = Elasticsearch("10.13.1.126:9200")
			self.one_month_ago = datetime.datetime(time.localtime(self.now).tm_year,time.localtime(self.now).tm_mon-1,time.localtime(self.now).tm_mday)
		
		def open_spider(self,spider):
			self.bloomname = "filter"
			isexists = os.path.exists(self.bloomname+".bloom")
			if isexists:
				print("打开一个存在的filter文件",file=self.f)
				self.bf = BloomFilter.open(self.bloomname+".bloom")
			else:
				print("创建一个新的filter文件",file=self.f)
				self.bf = BloomFilter(100000000,0.001,self.bloomname+".bloom")
		def process_item(self,item,spider):
			token = item['lost_mid']
			time_temp = re.search(r'(\d+).?(\d+).?(\d+)',str(item['lost_time']))
			time_stamp = datetime.datetime(int(time_temp.group(1)),int(time_temp.group(2)),int(time_temp.group(3)))
			if time.mktime(time_stamp.timetuple()) < time.mktime(self.one_month_ago.timetuple()):
				#print("At Time %s , the item[%s] : the datetime is overtimed._____________"%(time.ctime(),token),file=self.f)
				raise DropItem("****************************The datetime is overtimed!!!!!")
			
			item['lost_title'] = item['lost_describe']
			items = get_thing_array(item['lost_describe'])
			if not items:
					raise DropItem("****************************the items has no match!!!!!")
			else:
					item['lost_describe'] = items
			flag = self.bf.add(token)
			if flag == False:
				return item
			#这里表示：如果没有重复，item接着放到下面的pipeline类中处理
			else:
				self.f.write("At Time %s , the item[%s] is overread url , Not Allowed._____________"%(time.ctime(),token))
				self.f.close()
				raise DropItem("****************************is the overread url!!!!!")
				#time.sleep(10)
		
class Collector_SpiderPipeline(object):
		def __init__(self):
			self.file = codecs.open('/home/hong/文档/sina_working/2to3_test/tempfile.json','a',encoding="utf-8")
		def process_item(self, item, spider):
			line=json.dumps(dict(item),ensure_ascii=False)+"\n"
			self.file.write(line)
			return item
		def spider_closed(self,spider):
			self.file.close()

class SQLPipeline(object):
		def __init__(self):
				self.myfile = open("/home/hong/文档/sina_working/2to3_test/mid.txt",'a')
				self.es = Elasticsearch("10.13.1.126:9200")
		def process_item(self,item,spider):
				data={
						"created_at":datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
						"uid":"other",
						"domain":item['lost_from'],
						"status":"found",
						"from":item['lost_url'],
						"isneed":1,
						"text":item['lost_title'],
						"mid":item['lost_mid'],
						"place":item['lost_location'],
						"items":item['lost_describe'],
						"time":item['lost_time']
				}
				print("mid = %s , %s"%(item['lost_mid'],data['mid']),self.myfile)
				#es = Elasticsearch("10.13.1.126:9200")
				self.es.index(index="liaohong_test",doc_type="search",id=data['mid'],body=data)
		def spider_closed(self,spider):
				self.myfile.close()



thing_array = {   
	"其他": {
		"U盘": [
				"U盘",
				"优盘"
				],
		"摩托车": [
				"摩托车"
				],
		"自行车": [
				"自行车"
				],
		"门票":[
				"门票"
				]
		},
	"卡片": {
		"会员卡": [
				"会员卡"
				],
		"充值卡": [
				"充值卡"
				],
		"学生卡": [
				"学生卡"
				],
		"校园卡": [
				"校园卡"
				],
		"银行卡": [
				"行卡"
				],
		"门禁卡": [
				"门禁卡"
				],
		"饭卡": [
				"饭卡"
				]
		},
	"宠物": {
		"狗": [
				"小狗",
				"幼犬"
				],
		"猫": [
				"小喵",
				"小猫"
				]
		},
		"箱包": {
		"手提包": [
				"手提包",
				"小包",
				"手提袋"
				],
		"旅行箱": [
				"旅行箱"
				],
		"背包": [
				"背包",
				"单肩包"
				],
		"钱包": [
				"钱包",
				"钱夹",
				"钱袋"
				]
		},
	"证照": {
		"户口簿": [
				"户口簿",
				"户口本"
				],
		"房产证": [
				"房产证"
				],
		"身份证": [
				"身份证"
				],
		"车牌": [
				"车牌"
				],
		"驾驶证": [
				"驾驶证",
				"驾驶本",
				"车本"
				]
		},
	"随身物品": {
		"耳机": [
				"耳机",
				"耳塞"
				],
		"手机": [
				"手机",
				"iphone"
				],
		"钥匙": [
				"钥匙"
				],
				"首饰": [
				"项链",
				"手镯",
				"耳环"
				]
		}
}

'''
#由于MYSQLdb只支持python2，这里我们换用pymysql
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
		print("At Time %s , int url : %s ,there is a error : %s._____________"%(time.ctime(),item['lost_url'],e), file=self.f)
		self.f.close()
		log.err(e)
'''
