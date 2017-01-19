#!/usr/bin/env python
#coding=gbk
# 索引构建和检索

from EntityNode import EntityNode
import sys, os
import logging, ConfigParser, pickle

Debug = True

Log_Format = '%(asctime)s %(filename)s[line:%(lineno)d] [%(levelname)s] %(message)s'
logging.basicConfig(level=logging.DEBUG,
	format = Log_Format,
	filename = 'log/Indexer.log')

Config_File_Path = 'conf/index.ini'

# Inv:  substr --> [eid1, eid2, eid3 ....... eidN]
# Idx:  eid --> { id: idv
#				  type: typev
#				  name: namev
#				  normname: normnamev
#				  info: infov
#				}




class Indexer:
	''' index maker and index search '''
	def __init__(self):
		self.loadConfig()
		self.entityid = 0
		self.entityIndexDict = dict()
		self.entityInvDict = dict()
		self.locationDict = dict()


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


	def loadHospitalLocInfo(self, field = 'hospital', coding='gbk'):
		locDic = dict()
		locFile = self.getConfigKey(field, 'locFile')
		if len(locFile) == 0:
			return locDic
		lines = [line.strip('\n').decode(coding, 'ignore') for line in open(locFile) if len(line.strip()) > 0]
		for locItem in lines:
			segs = locItem.split('\t')
			if len(segs) != 4:
				continue

			# location info
			name, province, city, area = segs
			locInfo = {'province':province.strip(), 'city':city.strip(), 'area':area.strip()}
			if name not in locDic:
				locDic[name] = [locInfo]
		logging.info('load hospital location info done. total %d' % len(locDic))
		return locDic


	def testloadHospitalLocInfo(self):
		self.loadHospitalLocInfo()


	def loadHospitalName(self, field = 'hospital', coding='gbk'):
		nameList = []
		aliasDict = dict()
		nameFile = self.getConfigKey(field, 'nameFile')
		if len(nameFile) == 0:
			return (nameList, aliasDict)
		lines = [line.strip('\n').decode(coding, 'ignore') for line in open(nameFile) if len(line.strip()) > 0]
		for line in lines:
			segs = line.split('\t')
			if len(segs) != 2:
				continue
			name, alias = segs
			if name not in nameList:
				nameList.append(name)
			if name == alias:
				continue
			if name not in aliasDict:
				aliasDict[name] = []
			if alias not in aliasDict[name]:
				aliasDict[name].append(alias)
		logging.info('load hospital name list done. total %d' % len(nameList))
		return (nameList, aliasDict)
	
	
	def getTermList(self, nameList):
		# 可以去停用词
		# 可以去除括号等操作，减少无效term
		termList = []
		for name in nameList:
			for idx in xrange(0, len(name)):
				for size in xrange(1, len(name)-idx + 1):
					term = name[idx : idx + size]
					if term not in termList:
						termList.append(term)
		return termList

	def testgetTermList(self):
		str = ['abc']
		print self.getTermList(str)


	def dumpIndex(self):
		indexFile = self.getConfigKey('dump', 'index')
		if len(indexFile) == 0:
			logging.error('index file is empty, check config file')
		pickle.dump(self.entityIndexDict, open(indexFile,'wb'), 2)


	def dumpInv(self):
		invFile = self.getConfigKey('dump', 'inv')
		if len(invFile) == 0:
			logging.error('inv file is empty, check config file')
		pickle.dump(self.entityInvDict, open(invFile,'wb'), 2)

	def dumpLoc(self):
		locFile = self.getConfigKey('dump', 'loc')
		if len(locFile) == 0:
			logging.error('loc file is empty, check config file')
		pickle.dump(self.locationDict, open(locFile,'wb'), 2)

	def dump(self):
		self.dumpIndex()
		self.dumpInv()
		self.dumpLoc()


	def __indexImp(self, field, name, nameList, info):
		# 正排
		self.entityid += 1
		entity = EntityNode(self.entityid, field, name, info) 		
		self.entityIndexDict[self.entityid] = entity
		# 倒排
		termList = self.getTermList(nameList)
		for term in termList:
			if term not in self.entityInvDict:
				self.entityInvDict[term] = []
			# 可以限制倒排链的大小
			if self.entityid not in self.entityInvDict[term]:
				self.entityInvDict[term].append(self.entityid)

		#if self.entityid % 89 == 0:
		#	print 'name: ', name
		#	print 'field: ', field
		#	print 'info: ', type(info)
		#	print 'entity: ', entity


	# 这里有一个前提：所有的医院名称都不相同，按照名称作为实体标识的
	def indexHospital(self):
		field = 'hospital'
		hospitalInfoDict = self.loadHospitalLocInfo(field)
		hospitalNameList, hospitalAliasDict = self.loadHospitalName(field)

		idx = 0
		for name in hospitalNameList:
			hosInfo = []
			if name in hospitalInfoDict:
				hosInfo = hospitalInfoDict[name]
			nameList = [name]
			if name in hospitalAliasDict:
				nameList += hospitalAliasDict[name]

			self.__indexImp(field, name, nameList, hosInfo)
			continue


			# 正排信息
			self.entityid += 1
			entity = EntityNode(self.entityid, field, name, hosInfo) 		
			self.entityIndexDict[self.entityid] = entity
			# 倒排信息
			termList = self.getTermList(nameList)
			for term in termList:
				if term not in self.entityInvDict:
					self.entityInvDict[term] = []
				# 可以限制倒排链的大小
				if self.entityid not in self.entityInvDict[term]:
					self.entityInvDict[term].append(self.entityid)
			if Debug:
				idx += 1
				if idx % 1000 == 0:
					print 'name: ', name
					print 'entity: ', entity
					print 'term: ', (','.join(termList)).encode('gbk', 'ignore')
		logging.info('index for hospital done.')


	def loadDepartmentInfo(self, field = 'department', coding='gbk'):
		deptInfoDict = dict()
		deptFile = self.getConfigKey(field, 'nameFile')
		if len(deptFile) == 0:
			logging.error('department file is empty, check config file')
			return deptInfoDict
		# load first-second department pair
		firstDeptList, secondDeptDict = [], dict()
		for line in open(deptFile):
			line = line.strip('\n').decode(coding, 'ignore')
			segs = line.split('\t')
			if len(segs) != 2:
				continue
			firstDept, secondDept = segs
			if firstDept not in firstDeptList:
				firstDeptList.append(firstDept)
			if secondDept not in secondDeptDict:
				secondDeptDict[secondDept] = []
			if firstDept not in secondDeptDict[secondDept]:
				secondDeptDict[secondDept].append(firstDept)
		# create info for each department
		for second in secondDeptDict:
			if len(second) == 0:
				continue
			infoList = []
			for first in secondDeptDict[second]:
				if len(first) == 0:
					continue
				info = {'type':'second', 'first':first, 'second':second}
				infoList.append(info)
			deptInfoDict[second] = infoList

		for first in firstDeptList:
			if len(first) == 0 or first in deptInfoDict:
				continue
			info = {'type':'first', 'first':first}
			deptInfoDict[second] = [info]

		logging.info('load department info done. total %d' % len(deptInfoDict))
		return deptInfoDict



	def indexDepartment(self):
		field = 'department'
		deptInfoDict = self.loadDepartmentInfo(field)
		for name in deptInfoDict:
			if len(name) == 0:
				continue
			deptInfo = deptInfoDict[name]
			self.__indexImp(field, name, [name], deptInfo)
			continue

			# 正排
			self.entityid += 1
			entity = EntityNode(self.entityid, field, name, deptInfo) 		
			self.entityIndexDict[self.entityid] = entity
			# 倒排
			termList = self.getTermList([name])
			for term in termList:
				if term not in self.entityInvDict:
					self.entityInvDict[term] = []
				# 可以限制倒排链的大小
				if self.entityid not in self.entityInvDict[term]:
					self.entityInvDict[term].append(self.entityid)
		logging.info('index for department done.')
			

	
	def loadDiseaseInfo(self, field = 'disease', coding='gbk'):
		diseaseInfoDict = dict()
		diseaseFile = self.getConfigKey(field, 'infoFile')
		if len(diseaseFile) == 0:
			logging.error('disease file is empty, check config file')
			return deptInfoDict
		# load disease-department pair
		diseaseInfoDict = dict()
		for line in open(diseaseFile):
			line = line.strip('\n').decode(coding, 'ignore')
			segs = line.split('\t')
			if len(segs) != 3:
				continue
			disease, firstDept, secondDept = segs
			if disease not in diseaseInfoDict:
				diseaseInfoDict[disease] = []
			info = {'first': firstDept, 'second': secondDept}
			diseaseInfoDict[disease].append(info)
		return diseaseInfoDict


	def indexDisease(self):
		field = 'disease'
		diseaseInfoDict = self.loadDiseaseInfo(field)
		for name in diseaseInfoDict:
			diseaseInfo = diseaseInfoDict[name]
			if len(name) == 0:
				continue
			self.__indexImp(field, name, [name], diseaseInfo)
			continue

			# 正排
			self.entityid += 1
			entity = EntityNode(self.entityid, field, name, diseaseInfo) 		
			self.entityIndexDict[self.entityid] = entity
			# 倒排
			termList = self.getTermList([name])
			for term in termList:
				if term not in self.entityInvDict:
					self.entityInvDict[term] = []
				# 可以限制倒排链的大小
				if self.entityid not in self.entityInvDict[term]:
					self.entityInvDict[term].append(self.entityid)
		logging.info('index for disease done.')



	def __addLocInfo(self, key, info):
		if key not in self.locationDict:
			self.locationDict[key] = []
		self.locationDict[key].append(info)


	def indexLocation(self):
		field = 'loc'
		areaFile = self.getConfigKey(field, 'nameFile')
		if len(areaFile) == 0:
			logging.error('area file is empty, check config file')
		items = []
		for line in open(areaFile):
			line = line.strip('\n').decode('gbk', 'ignore')
			segs = line.split('\t')
			if len(segs) != 3:
				continue

			province, city, area = segs
			if len(province) != 0:
				item = province
				if item not in items:
					items.append(item)
					info = {'type':'province', 'province':province}
					self.__addLocInfo(province, info)
			if len(province) != 0 and len(city) != 0:
				item = '%s\t%s' % (province, city)
				if item not in items:
					items.append(item)
					info = {'type':'city', 'province':province, 'city':city}
					self.__addLocInfo(city, info)
			if len(province) != 0 and len(city) != 0 and len(area) != 0:
				item = '%s\t%s\t%s' % (province, city, area)
				if item not in items:
					items.append(item)
					info = {'type':'area', 'province':province, 'city':city, 'area':area}
					self.__addLocInfo(area, info)
		logging.info('load area info done.')
		pass


	def index(self):
		self.indexHospital()
		self.indexDepartment()
		self.indexDisease()
		self.indexLocation()
		self.dump()
		print len(self.entityIndexDict)


if __name__ == '__main__':
	indexer = Indexer()	
	indexer.index()
	

