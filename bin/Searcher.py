#!/usr/bin/env python
#coding=gbk
# 索引构建和检索

from EntityNode import EntityNode
import sys, os, re, time
import logging, ConfigParser, pickle
from time import clock


Debug = False
InfoFormat = '[%s] [INFO] [Sogou-Observer,cost=%s,ret=%s,query=[%s],loc=[%s], Owner=OP]'
ErrorFormat = '[%s] [ERROR] [Sogou-Observer,cost=%s,ret=%s,query=[%s],loc=[%s], Owner=OP]'
OtherFormat = '[INFO] [%s] %s'
Config_File_Path = 'conf/index.ini'


def getCunTime():
	return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

class Searcher:
	''' index search '''
	def __init__(self, conf):
		self.loadConfig(conf)
		self.loadIndex()
		self.loadInv()
		self.loadLocInfo()
		self.loadKeshi()
		self.loadDisease()
		print >> sys.stderr, OtherFormat % (getCunTime(), 'init Searcher done.')

	def loadConfig(self, conf = Config_File_Path):
		self.cf = ConfigParser.ConfigParser()
		self.cf.read(conf)

	def getConfigKey(self, field, key):
		value = ''
		try:
			value = self.cf.get(field, key)
		except:
			value = ''
		return value

	def loadIndex(self):
		indexFile = self.getConfigKey('dump', 'index')
		if len(indexFile) == 0:
			print >> sys.stderr, '[ERROR] [%s] %s' % (getCunTime(), 'index file is empty, check config file')
		self.entityIndexDict = pickle.load(open(indexFile,'rb'))
		print >> sys.stderr, '[INFO] [%s] %s' % (getCunTime(), 'Searcher load index done.')


	def loadInv(self):
		invFile = self.getConfigKey('dump', 'inv')
		if len(invFile) == 0:
			print >> sys.stderr, '[ERROR] [%s] %s' % (getCunTime(), 'inv file is empty, check config file')
		self.entityInvDict = pickle.load(open(invFile,'rb'))
		print >> sys.stderr, '[INFO] [%s] %s' % (getCunTime(), 'Searcher load inv done.')

	def loadLocInfo(self):
		locFile = self.getConfigKey('dump', 'loc')
		if len(locFile) == 0:
			print >> sys.stderr, '[ERROR] [%s] %s' % (getCunTime(), 'loc file is empty, check config file')
		self.locationDict = pickle.load(open(locFile,'rb'))
		print >> sys.stderr, '[INFO] [%s] %s' % (getCunTime(), 'Searcher load loc done.')
	
	# 加载科室信息
	def loadKeshi(self):
		keshiFile = self.getConfigKey('dump', 'keshi')
		if len(keshiFile) == 0 or not os.path.exists(keshiFile):
			print >> sys.stderr, '[ERROR] [%s] %s' % (getCunTime(), 'keshi file is empty, check config file')
		self.keshiDict = dict()
		for line in open(keshiFile):
			segs = line.strip().decode('gbk', 'ignore').split('\t')
			if len(segs) < 2:
				continue
			first, second = segs
			if first not in self.keshiDict:
				info = {'first':first, 'type':'first'}
				self.keshiDict[first] = info
			if second not in self.keshiDict:
				info = {'first':first, 'second':second, 'type':'second'}
				self.keshiDict[second] = info
		print >> sys.stderr, '[INFO] [%s] %s' % (getCunTime(), 'Searcher load keshi done.')
		
	# 加载疾病对应科室的信息
	def loadDisease(self):
		diseaseFile = self.getConfigKey('dump', 'disease')
		if len(diseaseFile) == 0 or not os.path.exists(diseaseFile):
			print >> sys.stderr, '[ERROR] [%s] %s' % (getCunTime(), 'disease file is empty, check config file')
		self.diseaseDict = dict()
		for line in open(diseaseFile):
			segs = line.strip().decode('gbk', 'ignore').split('\t')
			if len(segs) != 4:
				continue
			disease, first, second, type = segs
			if disease not in self.diseaseDict:
				info = {'first':first, 'second':second, 'type':type}
				self.diseaseDict[disease] = info
		print >> sys.stderr, '[INFO] [%s] %s' % (getCunTime(), 'Searcher load disease done.')



	# 计算地域的后缀标识
	def __getLocSuffixFlag(self, locType, isPrefix):
		locRegex = ''
		if locType == 'province':
			locRegex = u'[省市]$'
			if isPrefix:
				locRegex = u'^[省市]'
		elif locType == 'city':
			locRegex = u'[市县]$'
			if isPrefix:
				locRegex = u'^[市县]'
		elif locType == 'area':
			locRegex = u'[市县区]$'
			if isPrefix:
				locRegex = u'^[市县区]'
		return locRegex


	# 计算term中包含的地域
	# 应该只考虑前缀，后缀包含的地名才纳入考虑范围
	# 包含空格的时候
	# 同时去除紧跟的的 省，市，区等字眼
	# 多区域的发现，like 北京市海淀区 这种情况
	def recLocation(self, query):
		query = query.strip()
		qLen = len(query)

		# find location
		loc, locType, qc = '', '', query
		isLocPrefix = True
		for size in xrange(2, 6):
			if size > qLen:
				break
			if query[:size] in self.locationDict:
				loc, qc = query[:size], query[size:]
				break
			if query[0-size:] in self.locationDict:
				loc, qc = query[0-size:], query[:0-size]
				isLocPrefix = False
				break

		if len(loc) > 0:
			if Debug:
				print ('%s : %s' % (query, str(self.locationDict[loc][0]))).encode('gbk', 'ignore')
			locType = self.locationDict[loc][0]['type']
			locFlagRegex = self.__getLocSuffixFlag(locType, isLocPrefix)
			if Debug:
				print 'qc: %s\t locFlagRegex: %s' % (qc, locFlagRegex)
			qc = re.sub(locFlagRegex, '', qc).strip()
			if len(qc) == 0:
				qc = query
		return loc, locType, qc


	# query中识别出来的实体列别
	def __getQueryType(self, query):
		entityType = ""
		for entityid in self.entityInvDict[query]:
			entityType = self.entityIndexDict[entityid].type
			if Debug:
				print 'query: [%s]  entityType: [%s]' % (query, entityType)
			break
		return entityType
		


	def __suggestion(self, query, loc, locType, locFrom):
		TopN = 10
		result = list()
		# 如果只命中医院类别，而且所在地没有的话，出其他
		onlyHitHos = True
		noHisHosList = list()
		

		if query not in self.entityInvDict:
			return result

		queryType = self.__getQueryType(query)
		for entityid in self.entityInvDict[query]:
			entityType = self.entityIndexDict[entityid].type
			if entityType != queryType:
				if len(result) > 0:
					break
				queryType = entityType
			if len(result) == TopN:
				break
			# 医院 + loc
			if entityType == 'hospital' and len(loc) != 0:
				for infoItem in self.entityIndexDict[entityid].info:
					if locType in infoItem and infoItem[locType] == loc:
						itemName = self.entityIndexDict[entityid].name
						if itemName not in result:
							result.append(itemName)
					# 非本地医院命中
					elif len(noHisHosList) < TopN:
						itemName = self.entityIndexDict[entityid].name
						if itemName not in noHisHosList:
							noHisHosList.append(itemName)
			# 科室/疾病 + loc
			elif entityType == 'department' or entityType == 'disease':
				if locFrom == 'user':
					result = list()
				else:
					itemName = self.entityIndexDict[entityid].name
					if itemName not in result:
						result.append(itemName)
		if Debug:
			print ("{'type': '%s', 'sugg':'[%s]'}" % (queryType, ','.join(result))).encode('gbk', 'ignore')

		if queryType == 'hospital' and len(result) == 0:
			result = noHisHosList
		#print ("{'type': '%s', 'sugg':'[%s]'}" % (queryType, ','.join(result))).encode('gbk', 'ignore')

		return {'type': queryType, 'sugg':result}


	def __parseUserLoc(self, uLoc=''):
		loc, locType = '', ''
		segs = uLoc.split(',')
		province, city, area = '', '', ''
		if len(segs) >= 1:
			province = segs[0]
		if len(segs) >= 2:
			city = segs[1]
		if len(segs) >= 3:
			area = segs[2]
		if len(city) != 0:
			loc = city
			locType = 'city'
		elif len(province) != 0:
			loc = province
			locType = 'province'
		return (loc, locType)
		

	# suggestion
	# 最多取Top N个结果
	def suggestion(self, query, uLoc=''):
		result = ""
		start = clock()
		# get location
		loc, locType, qcQuery = self.recLocation(query)
		locFrom = 'user'
		if Debug:
			print 'query: %s, type: %s, qc: %s' % (loc, locType, qcQuery)
		if len(loc) == 0:
			loc, locType = self.__parseUserLoc(uLoc)
			locFrom = 'poi'
		# 优先使用 原始query

		if query in self.entityInvDict:
			result = self.__suggestion(query, loc, locType, locFrom)
		elif qcQuery in self.entityInvDict:
			result = self.__suggestion(qcQuery, loc, locType, locFrom)

		end = clock()
		cost = str(end - start)
		ret = 0
		if len(result) != 0:
			ret = 1
		print >> sys.stderr, InfoFormat % (getCunTime(), cost, str(ret), query.encode('gbk', 'ignore'), uLoc.encode('gbk', 'ignore'))

		return result

	# 精准命中 科室或者疾病
	def accurateHit(self, query):
		queryType, keywords, entityInfo = '', query, None
		if query in self.keshiDict:
			queryType = 'department'
			entityInfo = self.keshiDict[query]
		if query in self.diseaseDict:
			queryType = 'disease'
			entityInfo = self.diseaseDict[query]
		return queryType, keywords, entityInfo

	# 根据 医院 > 科室 > 疾病 的优先级进行命中
	# 如果命中医院，需要医院的地点与loc一致
	def priorityHit(self, query, loc, locType):
		
		#keywords = query
		#queryType = self.__getQueryType(query)
		#firstEntityid = self.entityInvDict[query][0]
		#entityInfo = self.entityIndexDict[firstEntityid].info[0]
		#return queryType, keywords, entityInfo

		hit = False
		queryType, keywords, entityInfo = '', '', None
		for entityid in self.entityInvDict[query]:
			entityType = self.entityIndexDict[entityid].type
			# 命中医院的话，需要保障是本地的医院
			if entityType == 'hospital' and len(loc) != 0:
				for infoItem in self.entityIndexDict[entityid].info:
					if locType in infoItem and infoItem[locType] == loc:
						hit = True
						break
			else:
				hit = True
			if hit:
				# 非医院的话，直接返回即可
				keywords = query
				queryType = entityType
				entityInfo = self.entityIndexDict[entityid].info[0]
				return queryType, keywords, entityInfo
		return queryType, keywords, entityInfo
								





	# 注意包含空格的情况
	# 给出分词结果即可
	# output: {"type":"",  "keyword":[],  "loc": {}, "info":{}}
	#    suggestion 是取topN  search 只要取出第一个就OK
	# 疾病，科室是需要info信息去找医院的
	def search(self, query, uLoc=''):
		start = clock()
		result = list()
		queryContainLoc = True
		# get location
		loc, locType, qcQuery = self.recLocation(query)
		if Debug:
			print 'query: [%s],   loc type: [%s],    qc: [%s]' % (query, locType, qcQuery)
		# 这里需要做修改，参数要传进来
		if len(loc) == 0:
			queryContainLoc = False
			loc, locType = self.__parseUserLoc(uLoc)

		queryType, keywords, location, entityInfo = '', '', dict(), None
		if query in self.keshiDict or query in self.diseaseDict:
			queryType, keywords, entityInfo = self.accurateHit(query)
		elif qcQuery in self.keshiDict or qcQuery in self.diseaseDict:
			queryType, keywords, entityInfo = self.accurateHit(qcQuery)
		elif query in self.entityInvDict:
			queryType, keywords, entityInfo = self.priorityHit(query, loc, locType)
		elif qcQuery in self.entityInvDict:
			queryType, keywords, entityInfo = self.priorityHit(qcQuery, loc, locType)

		# location
		if loc in self.locationDict:
			location = self.locationDict[loc][0]

		result = {'type':queryType, 'keywords':keywords, 'location':location, 'info': entityInfo}
		if Debug:
			print 'query: %s, result: %s' % (query, str(result))
		#print 'query: %s, result: %s' % (query, str(result))

		end = clock()
		cost = str(end - start)
		ret = 1
		if len(keywords) == 0:
			ret = 0
		print >> sys.stderr, InfoFormat % (getCunTime(), cost, str(ret), query.encode('gbk', 'ignore'), uLoc.encode('gbk', 'ignore'))

		return result
		


if __name__ == '__main__':
	searcher = Searcher(Config_File_Path)
	print 'load index done.'

	
	#searcher.testIndex()

	#searcher.recLocation(u'北京市海淀区医院')
	#searcher.recLocation(u'苏州')
	#searcher.recLocation(u'鼓楼区')


	#searcher.suggestion(u'北京 口腔医院')
	#searcher.suggestion(u'北京市口腔医院')
	#searcher.suggestion(u' 医院 北京')
	#searcher.suggestion(u'小儿')
	#searcher.suggestion(u'北京内科')
	#searcher.suggestion(u'感冒')
	#searcher.search(u'同仁')
	#searcher.search(u'北京 口腔医院')
	#result = searcher.search(u'北京')
	#resultStr = ','.join([str(item) for item in result])
	#print type(resultStr.decode('gbk', 'ignore'))
	#for item in result:
	#	print item
	#print ('[%s]' % ','.join(result))
	#searcher.search(u'小儿外')
	#searcher.suggestion(u'白内障', u'北京,北京,')
	#searcher.search(u'白内障', u'北京,北京,')
	#searcher.suggestion(u'手外科')
	#searcher.suggestion(u'复旦大学附属中山')
	#searcher.search(u'北京朝阳口腔')
	#searcher.search(u'吉林 神经')
	#searcher.search(u'鼻窦恶性')
	#searcher.search(u'北京大学口')
	
	searcher.search(u'手外科', u'北京,北京,北京')
	searcher.search(u'小儿肾内科', u'北京,北京,北京')
	searcher.search(u'口腔科', u'北京,北京,北京')
	searcher.search(u'北京 口腔科', u'北京,北京,北京')
	searcher.search(u'北京 肺癌', u'北京,北京,北京')
	searcher.search(u'肝癌北京', u'北京,北京,北京')
	searcher.search(u'荨麻疹', u'北京,北京,北京')
	searcher.search(u'北京 心脏病', u'北京,北京,北京')
	searcher.search(u'白血病', u'北京,北京,北京')
	searcher.search(u'上海 心血管', u'北京,北京,北京')
	searcher.search(u'上海 心血管科', u'北京,北京,北京')
	searcher.search(u'肺癌', u'北京,北京,北京')
	searcher.search(u'杭州皮肤科', u'北京,北京,北京')
	searcher.search(u'北京高血压', u'北京,北京,北京')
	searcher.search(u'北京性病', u'北京,北京,北京')


	


