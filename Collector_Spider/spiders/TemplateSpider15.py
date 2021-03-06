import sys
import imp
import scrapy
from scrapy_redis.spiders import RedisSpider
from scrapy.http import Request
from Collector_Spider.items import CollectorSpiderItem
import requests
import bs4
from bs4 import BeautifulSoup
import lxml
import re
from urllib.error import URLError
import json
import time
import signal
from pybloomfilter import BloomFilter
import os
from scrapy.exceptions import CloseSpider
from urllib.parse import quote_plus
import datetime
import hashlib

def get_ValidUrl(index_url,url_post,post_url_second,url_extra):
	#这里留一个可以附加的条件，如果有其它的data要传递，那么使用这个url_extra，从config文件中获得
	if url_extra:
			return "ERROR"
	else:
			head_url = re.search(r'.+/',index_url).group()
			#存在正则，即把符合正则的提取出来，一般开头必无/
			if post_url_second:
					url_post = re.sub(post_url_second,"",url_post)
			#开头是/，把这个/消除
			if re.search(r'^/',url_post):
					url_post = re.sub(r'^/',"",url_post)
			return (head_url + url_post)

def get_HeadUrl(index_url,flag):
	if flag:
			if re.search(r'(?<=\?).+',index_url):
					return re.sub(r'(?<=\?).+',"%s",index_url)
			else:
					log = open("./log.txt",'a')
					print("At Time %s,Error in get_HeadUrl , at step 1 .\n"%time.ctime(), file=log)
					log.close()
					return -1
	else:
		#这个函数如果没有找到匹配，直接返回原str,都加一个报错
			if re.search(r'\d+',index_url):
					return re.sub(r'\d+',"%s",index_url)
			else:
					log = open("./log.txt",'a')
					print("At Time %s,Error in get_HeadUrl , at step 2 .\n"%time.ctime(), file=log)
					log.close()
					return -1

def format_string(string):
		return string.replace("\n","").replace("\r","").replace("\t","")
		
def format_time(time):
		time_split = re.search(r'(\d+).?(\d+).?(\d+)',time)
		if int(time_split.group(1)) < 100:
                   	return "20"+time_split.group(1)+"-"+time_split.group(2)+"-"+time_split.group(3)
		else:
					return time_split.group(1)+"-"+time_split.group(2)+"-"+time_split.group(3)


class CollectorSpider(scrapy.Spider):
	name ='chengdu_taix'
	allowed_domain = [""]

	def __init__(self,*args,**kwargs):
			super(CollectorSpider,self).__init__(*args,**kwargs)
			#用一个list来存放所有的json配置中的k,v，变成了一个元祖list，遍历这个list
			#scrapy.log.start("./log.txt",loglevel=INFO,logstdout=True)
			self.log = open("/home/hong/文档/sina_working/2to3_test/log.txt",'a')
			print("\n\n__________________________分割线___________________________________", file=self.log)
			print("At Time %s : 爬虫启动............"%time.ctime(), file=self.log)
			self.now = time.time()
			self.one_month_ago = datetime.datetime(time.localtime(self.now).tm_year,time.localtime(self.now).tm_mon-1,time.localtime(self.now).tm_mday)
			self.config = []
			self.Index_Url = ""
			self.flag = 0
			#这里必须初始化bf，否则首次循环下面会报错
			self.bf = ""
			self.isexists=os.path.exists("/home/hong/文档/sina_working/2to3_test/filter.bloom")
			if self.isexists:
					print("存在filter.bloom，打开!!!!",file=self.log)
					self.bf = BloomFilter.open("/home/hong/文档/sina_working/2to3_test/filter.bloom")

	def start_requests(self):
		with open('config.json','r') as f:
				data = json.load(f)
				for i in data.items():
						if i[0] == self.name:
								self.config.append(i)
								print(i[0])
				f.close()

		for v in self.config:
				if len(v[1]) == 1:
						self.Index_Url = v[1][0]['Index_Url']
						print("At Time %s : 爬虫开始爬取层数为1的页面Title = %s , Index_Url = %s "%(time.ctime(),v[0],self.Index_Url), file=self.log)
						Max_Page = v[1][0]['Max_Page']
						Final_Url = v[1][0]['Final_Url']
						One_Xpath = v[1][0]['One_Xpath']

						if Max_Page:
								headers={'User-Agent':"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36"}
								response = requests.get(self.Index_Url,headers = headers)
								soup = BeautifulSoup(response.content,"lxml")
								result = str(soup.select(Max_Page['soup']))
								pageNums = re.search(Max_Page['re'],result).group()
						if Final_Url:
								url = re.sub(Final_Url,"{limit}",self.Index_Url)
								real_url = url.format(limit=pageNums)
						else:
								real_url = self.Index_Url
						request = Request(real_url,callback = self.parse)
						request.meta['One_Xpath'] = One_Xpath
						yield request

				if len(v[1]) == 2:
						self.Index_Url = v[1][0]['Index_Url']
						print("At Time %s : 爬虫开始爬取层数为2的页面Title = %s , Index_Url = %s "%(time.ctime(),v[0],self.Index_Url), file=self.log)
						print("!!!!!!!!!!!!!!!!!!!!!!!!!Index_Url = %s"%self.Index_Url)
						Max_Page = v[1][0]['Max_Page']
						#Head_Url = v[1][0]['Head_Url']
						Post_Data = v[1][0]['Post_Data']

						Two_Xpath = v[1][1]['Two_Xpath']
						headers={'User-Agent':"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36"}
						response = requests.get(self.Index_Url,headers = headers)

						soup = BeautifulSoup(response.content,"lxml")
						result = str(soup.select(Max_Page['soup']))
						pageNums = re.search(Max_Page['re'],result).group()
						#urls = re.sub(Head_Url,"%s",self.Index_Url)
						if Post_Data:
								self.flag = 1
						urls = get_HeadUrl(self.Index_Url,self.flag)
						if urls == -1:
								raise CloseSpider("______________________________ 构造url失败，爬取结束，请查看日志！_____________________________")

						postdata = ""
						if Post_Data:
								keys = list(Post_Data.keys())
								for key in keys:
										if Post_Data[key]:
												if re.search(Post_Data[key],str(soup)):
														postdata += (key+"="+str((re.search(Post_Data[key],str(soup)).group())).replace("\"","") + "&")
												else:
														postdata += (key+"="+Post_Data[key]+"&")
										else:
												postdata += (key+"={page}&")
						if not postdata:
								urls = urls.replace("%s","{page}")
						else:
								urls = urls%postdata

						for i in range(1,int(pageNums)):
								url = urls.format(page=str(i))
								request = Request(url,callback = self.parse)
								request.meta['Two_Xpath'] = Two_Xpath
								yield request
				elif len(v[1]) == 3:
						self.Index_Url = v[1][0]['Index_Url']
						print("At Time %s : 爬虫开始爬取层数为3的页面Title = %s , Index_Url = %s "%(time.ctime(),v[0],self.Index_Url), file=self.log)
						Max_Page = v[1][0]['Max_Page']
						#Head_Url = v[1][0]['Head_Url']
						Post_Data = v[1][0]['Post_Data']

						Valid_Url = v[1][1]['Valid_Url']

						Three_Xpath = v[1][2]['Three_Xpath']
						headers={'User-Agent':"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36"}
						response = requests.get(self.Index_Url,headers = headers)

						soup = BeautifulSoup(response.content,"lxml")
						result = str(soup.select(Max_Page['soup']))
						pageNums = re.search(Max_Page['re'],result).group()
						#urls = re.sub(Head_Url,"%s",self.Index_Url)
						print("最大页数是:%s"%pageNums)
						if Post_Data:
								self.flag = 1
						urls = get_HeadUrl(self.Index_Url,self.flag)
						if urls == -1:
								raise CloseSpider("______________________________ 构造url失败，爬取结束，请查看日志！_____________________________")
							#print urls
						postdata = ""
						if Post_Data:
								keys = list(Post_Data.keys())
								for key in keys:
										if Post_Data[key]:
												if re.search(Post_Data[key],str(soup)):
														postdata += (key+"="+quote_plus((re.search(Post_Data[key],str(soup)).group()).replace('"',""))+"&")
												else:
														postdata += (key+"="+Post_Data[key]+"&")
										else:
												postdata += (key+"={page}&")
						if not postdata:
								urls = urls.replace("%s","{page}")
						else:
								urls = urls%postdata
						for i in range(1,int(pageNums)):
								url = urls.format(page=str(i))
								request = Request(url,callback = self.parse_first)
								request.meta['Valid_Url'] = Valid_Url
								request.meta['Three_Xpath'] = Three_Xpath
								yield request

	def parse_first(self,response):
		Valid_Url = response.meta['Valid_Url']
		Three_Xpath = response.meta['Three_Xpath']

		test_url = response.xpath(Valid_Url['Post_Url'][0]).extract()[0]
		if (not re.search(r'^http://',test_url)) and (not re.search(r'^https://',test_url)):
				print("这不是正常的网页，进入策略2，构造url.........")
				for i in response.xpath(Valid_Url['Post_Url'][0]).extract():
						if len(Valid_Url['Post_Url']) > 1:
								url = get_ValidUrl(self.Index_Url,str(i),Valid_Url['Post_Url'][1],"")
						else:
								url = get_ValidUrl(self.Index_Url,str(i),"","")
						print("$$$$$$$$$$$$$$$$$$$$$$$"+url)
						request = Request(url,callback = self.parse)
						request.meta['Three_Xpath'] = Three_Xpath
						yield request
		else:
				print("得到正常网页，进入策略1，直接访问url.........")
				for i in response.xpath(Valid_Url['Post_Url'][0]).extract():
						request = Request(i,callback = self.parse)
						request.meta['Three_Xpath'] = Three_Xpath
						yield request

	def parse(self,response):
		item = CollectorSpiderItem()
		One_Xpath = response.meta.get('One_Xpath',None)
		Two_Xpath = response.meta.get('Two_Xpath',None)
		Three_Xpath = response.meta.get('Three_Xpath',None)

		if One_Xpath:
			for i in response.xpath(One_Xpath['Lost_Xpath']):
				item['lost_url'] = response.url
				item['lost_from'] = "" if not re.search(One_Xpath['Lost_From'],response.url).group() else re.search(One_Xpath['Lost_From'],response.url).group()
				item['lost_id'] = format_string("" if not i.xpath(One_Xpath['Lost_Id'] if One_Xpath['Lost_Id'] else "/").extract() else i.xpath(One_Xpath['Lost_Id'] if One_Xpath['Lost_Id'] else "/").extract()[0])
				item['lost_title'] = format_string("" if not i.xpath(One_Xpath['Lost_Title'] if One_Xpath['Lost_Title'] else "/").extract() else i.xpath(One_Xpath['Lost_Title'] if One_Xpath['Lost_Title'] else "/").extract()[0])
				item['lost_describe'] = format_string("" if not i.xpath(One_Xpath['Lost_Describe'] if One_Xpath['Lost_Describe'] else "/").extract() else i.xpath(One_Xpath['Lost_Describe'] if One_Xpath['Lost_Describe'] else "/").extract()[0])
				item['lost_person'] = format_string("" if not i.xpath(One_Xpath['Lost_Person'] if One_Xpath['Lost_Person'] else "/").extract() else i.xpath(One_Xpath['Lost_Person'] if One_Xpath['Lost_Person'] else "/").extract()[0])
				item['lost_time'] = format_time(format_string("" if not i.xpath(One_Xpath['Lost_Time'] if One_Xpath['Lost_Time'] else "/").extract() else i.xpath(One_Xpath['Lost_Time'] if One_Xpath['Lost_Time'] else "/").extract()[0]))
				item['lost_location'] = One_Xpath['Lost_Location'][1]+(format_string("" if not i.xpath(One_Xpath['Lost_Location'][0] if One_Xpath['Lost_Location'][0] else "/").extract() else i.xpath(One_Xpath['Lost_Location'][0] if One_Xpath['Lost_Location'][0] else "/").extract()[0]))
				item['lost_mid'] = hashlib.md5((item['lost_url']+item['lost_id']+item['lost_describe']).encode('utf-8')).hexdigest()[8:-8]
				if os.path.exists("/home/hong/文档/sina_working/2to3_test/filter.bloom"):
					#token = str(item['lost_url'])+str(item['lost_id'])+str(item['lost_describe'])
					token = item['lost_mid']
					if self.bf.__contains__(token):
						print("\ntime waiting......\ntime waiting......\ntime waiting......\n\nAt Time %s , The spider TOKEN : %s has been destroied_______________"%(time.ctime(),token), file=self.log)
						self.log.close()
						#time.sleep(10)
						raise CloseSpider("______________________________ item已经捕获重复，爬取结束！_____________________________")
				yield item

		elif Two_Xpath:
			for i in response.xpath(Two_Xpath['Lost_Xpath']):
				#item['lost_mid'] = resposne.url
				item['lost_url'] = response.url
				item['lost_from'] = "" if not re.search(Two_Xpath['Lost_From'],response.url).group() else re.search(Two_Xpath['Lost_From'],response.url).group()
				item['lost_id'] = format_string("" if not i.xpath(Two_Xpath['Lost_Id'] if Two_Xpath['Lost_Id'] else "/").extract() else i.xpath(Two_Xpath['Lost_Id'] if Two_Xpath['Lost_Id'] else "/").extract()[0])
				item['lost_title'] = format_string("" if not i.xpath(Two_Xpath['Lost_Title'] if Two_Xpath['Lost_Title'] else "/").extract() else i.xpath(Two_Xpath['Lost_Title'] if Two_Xpath['Lost_Title'] else "/").extract()[0])
				item['lost_describe'] = format_string("" if not i.xpath(Two_Xpath['Lost_Describe'] if Two_Xpath['Lost_Describe'] else "/").extract() else i.xpath(Two_Xpath['Lost_Describe'] if Two_Xpath['Lost_Describe'] else "/").extract()[0])
				item['lost_person'] = format_string("" if not i.xpath(Two_Xpath['Lost_Person'] if Two_Xpath['Lost_Person'] else "/").extract() else i.xpath(Two_Xpath['Lost_Person'] if Two_Xpath['Lost_Person'] else "/").extract()[0])
				item['lost_time'] = format_time(format_string("" if not i.xpath(Two_Xpath['Lost_Time'] if Two_Xpath['Lost_Time'] else "/").extract() else i.xpath(Two_Xpath['Lost_Time'] if Two_Xpath['Lost_Time'] else "/").extract()[0]))
				item['lost_location'] = Two_Xpath['Lost_Location'][1] + format_string("" if not i.xpath(Two_Xpath['Lost_Location'][0] if Two_Xpath['Lost_Location'][0] else "/").extract() else i.xpath(Two_Xpath['Lost_Location'][0] if Two_Xpath['Lost_Location'][0] else "/").extract()[0])
				item['lost_mid'] = hashlib.md5((item['lost_url']+item['lost_id']+item['lost_describe']).encode('utf-8')).hexdigest()[8:-8]
				#time_temp = re.search(r'\d+-\d+-\d+',str(item['lost_time'])).group()
				#if not re.search(r'20',time_temp):
				#	time_temp = "20"+time_temp
				#print "time_temp = %s"%time_temp
				#time_stamp = datetime.datetime(int(re.search(r'\d+',time_temp).group()),int(re.search(r'(?<=-)\d+',time_temp).group()),int(re.search(r'\d+$',time_temp).group()))
				#if time.mktime(time_stamp.timetuple()) < time.mktime(self.one_month_ago.timetuple()):
				#	print >> self.log,"At Time %s , the item[%s] : the datetime is overtimed._____________"%(time.ctime(),time_stamp)
				#	raise CloseSpider("_____________________________The datetime is overtimed，爬取结束!!_______________________")

				if os.path.exists("/home/hong/文档/sina_working/2to3_test/filter.bloom"):
					#token = str(item['lost_url'])+str(item['lost_id'])+str(item['lost_describe'])
					token = item['lost_mid']
					if self.bf.__contains__(token):
						#self.log.write("TRUE，存在重复元素，到达这里没有?")
						print("\ntime waiting......\ntime waiting......\ntime waiting......\n\nAt Time %s , The spider TOKEN : %s has been destroied_______________"%(time.ctime(),token), file=self.log)
						self.log.close()
						#time.sleep(10)
						raise CloseSpider("______________________________ item已经捕获重复，爬取结束！_____________________________")
					
				yield item
		else:
			item['lost_url'] = response.url
			item['lost_from'] = "" if not re.search(Three_Xpath['Lost_From'],response.url).group() else re.search(Three_Xpath['Lost_From'],response.url).group()
			item['lost_id'] = format_string("" if not response.xpath(Three_Xpath['Lost_Id'] if Three_Xpath['Lost_Id'] else "/").extract() else response.xpath(Three_Xpath['Lost_Id'] if Three_Xpath['Lost_Id'] else "/").extract()[0])
			item['lost_title'] = format_string("" if not response.xpath(Three_Xpath['Lost_Title'] if Three_Xpath['Lost_Title'] else "/").extract() else response.xpath(Three_Xpath['Lost_Title'] if Three_Xpath['Lost_Title'] else "/").extract()[0])
			item['lost_describe'] = format_string("" if not response.xpath(Three_Xpath['Lost_Describe'] if Three_Xpath['Lost_Describe'] else "/").extract() else response.xpath(Three_Xpath['Lost_Describe'] if Three_Xpath['Lost_Describe'] else "/").extract()[0])
			item['lost_person'] = format_string("" if not response.xpath(Three_Xpath['Lost_Person'] if Three_Xpath['Lost_Person'] else "/").extract() else response.xpath(Three_Xpath['Lost_Person'] if Three_Xpath['Lost_Person'] else "/").extract()[0])
			item['lost_time'] = format_time(format_string("" if not response.xpath(Three_Xpath['Lost_Time'] if Three_Xpath['Lost_Time'] else "/").extract() else response.xpath(Three_Xpath['Lost_Time'] if Three_Xpath['Lost_Time'] else "/").extract()[0]))
			#print(type(Three_Xpath['Lost_Location'][1]))
			item['lost_location'] = Three_Xpath['Lost_Location'][1] + format_string("" if not response.xpath(Three_Xpath['Lost_Location'][0] if Three_Xpath['Lost_Location'][0] else "/").extract() else response.xpath(Three_Xpath['Lost_Location'][0] if Three_Xpath['Lost_Location'][0] else "/").extract()[0])
			item['lost_mid'] = hashlib.md5((item['lost_url']+item['lost_id']+item['lost_describe']).encode('utf-8')).hexdigest()[8:-8]
			if os.path.exists("/home/hong/文档/sina_working/2to3_test/filter.bloom"):
				#token = str(item['lost_url']+item['lost_id']+item['lost_describe'])
				token = item['lost_mid']
				if self.bf.__contains__(token):
					print("\ntime waiting......\ntime waiting......\ntime waiting......\n\nAt Time %s , The spider TOKEN : %s has been destroied_______________"%(time.ctime(),token), file=self.log)
					self.log.close()
					#time.sleep(10)
					raise CloseSpider("______________________________ url已经捕获重复，爬取结束！_____________________________")
			yield item


