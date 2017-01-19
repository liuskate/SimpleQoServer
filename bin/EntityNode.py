#!/usr/bin/env python
#coding=gbk

# 用于正派索引的每个节点

class EntityNode:

	def __init__(self, id, type, name, info):
		self.__id = id
		self.__type = type
		self.__name = name
		self.__info = info

	def get_id(self):
		return self.__id

	def set_id(self, id):
		self.__id = id

	id = property(get_id)

	def get_name(self):
		return self.__name

	def get_type(self):
		return self.__type

	def get_info(self):
		return self.__info

	name = property(get_name)
	type = property(get_type)
	info = property(get_info)

	def __str__(self):
		infoStrList = []
		for infoItem in self.info:
			itemStrList = []
			for key in infoItem:
				itemStrList.append('"%s":"%s"' % (key, infoItem[key]))
			infoStrList.append('{%s}' % ','.join(itemStrList))
		return ('{"type":"%s", "name":"%s", "info":[%s]}' % (self.type, self.name, ','.join(infoStrList))).encode('gbk', 'ignore')











