# hong_spider
there is a spider in python3.5.1.
这里记录一些爬取遇到的问题，以及操作的说明：

1.错误匹配
例子：
		背包内有尹学成工作证充电宝		匹配到了背包，而被当作有效匹配
				
						原先目标是充电宝，且充电宝不被匹配词库包含，这条记录应该丢弃

						2.关于config文件
								在config.json中的，是关于每个站点的定制，暂时分了三个层次，有一层页面（单独一个json页，或者一个正常网页），所有信息都包含在那单独的一页中
										二层页面，在一层页面中，存在很多的直接信息，那些信息都是我们需要的信息，所以为目标信息。但是有多个这样的页面，所以需要构造多个同级页面，不断去提起每个页面中的信息
												三层页面，在每一层页面中，存在很多的link，而真正的详细信息（目标信息）在link页面中，我们需要构造多个一级页面，然后提取这些页面的所有link，最后在link页面中提取有效信息


												3.关于命令
														这里，每一个TemplateSpider都是一个独立的进程，除了spider的name（还有个别几个标注的域名之外），几乎代码都是一样的。
																在config.json中稍作修改就能配置一个新的爬虫进程，具体步骤如下：
																			1.拷贝TemplateSpider.py到一个新的TemplateSpider数字.py，然后更改spider中的name
																						2.在config.json中添加同样name的定制文件，具体定制文件怎么写如下：
																											I.Index_Url：是我们找到的url的真实地址，包括？后面的附带的参数，一般我们假定这个网页都是由一个类似pageno=数字，来决定多个同级页面，之后Max_Page：使用requests库，对Index_Url作一次请求，根据返回找到有效信息最大页面数目{先根据css selector找到最大页面的那一段文字，再用正则匹配出来最大数字}。
																																之后就能通过Index_Url来构造多个同级页面了，供之后的信息提取
																																					II.之后的二级，就直接用xpath从每个一级页面中提取想要的信息即可;三级页面的话，中间可能提取到的link是一个相对链接，我在代码中写了一个简单的相对路径转化成绝对路径的func，构造出来绝对路径，最后就使用Xpath来提取页面详细信息即可
																																										III.一级json页面的提取，一般是一个json页面，然后有个start = 0和 limit = 数字,我们的Max_Page这时候的作用是找到limit的最大值，也就是这一页面有多少条记录，全部提取;普通页面的话，直接略去Max_Page，直接xpath提取
																																															IV.运行时的一些状态输出在log.txt文件中，没有做更详细的日志处理，只是一些简要的可能debug用的到的信息。
																																																				V.如果没看到log.txt，或template.json，或filter.bloom文件，执行一次命令这些文件即会生成;
																																																									Collector_SpiderPipeline模块是测试用模块，要将数据存入es中，只需要在CollectorSpider/settings.py中，将SQLPipeline前面的注释删除，就能启动SQLPipeline模块，一般生成的filter.bloom文件就别去管它了，它是保证增量爬取的前提。

																																																									4.使用
																																																											自定义了一个scrapy框架的命令，crawlall，意思是启动所有的爬虫，运行时只需要scrapy crawlall，即可启动所有的爬虫。
																																																													每个爬虫自定义的时间是10min，但是很多爬虫跑不到10min就会停了，比如大多数一级页面，数据量少。
																																																															每个爬虫定义的下载间隔是0.5s，为了防ban的简单策略，如果遇到更高等级的防ban，可以考虑使用ip池，增加downloadmiddler.py下载中间件即可.

