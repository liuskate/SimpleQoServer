#coding=gbk
import sys, os
import json as _Json
import logging as _Logging
import os.path as _Os_path
import tornado.ioloop as _Ioloop
import tornado.web as _Web
from Searcher import Searcher
import ConfigParser

_Program = _Os_path.basename(sys.argv[0])
_Logger = _Logging.getLogger(_Program)
_Logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
_Logging.root.setLevel(level=_Logging.INFO)
_searcher = None

class SegHandler(_Web.RequestHandler):
	def get(self):
		query=self.get_argument('q')
		seg_list=[]
		for seg in _Jieba.cut(query):
			seg_list.append(seg)
		self.write( {"request_query":query,"seg_list":seg_list})



class SearchHandler(_Web.RequestHandler):
	def get(self):
		result = {}
		try:
			query = self.get_argument('q')
			loc = self.get_argument('loc')
			result = _searcher.search(query, loc)
		except:
			print "error"
		self.write( {"query":query, "data":result})
			

class SuggestionHandler(_Web.RequestHandler):
	def get(self):
		result = {}
		try:
			query = self.get_argument('q')
			loc = self.get_argument('loc')
			result = _searcher.suggestion(query, loc)
		except:
			print "error"
		self.write( {"query":query, "data":result})
		


def make_app():
	return _Web.Application([(r"/api/qo", SearchHandler), (r"/api/sugg", SuggestionHandler)])


def getPort(conf):
	cf = ConfigParser.ConfigParser()
	cf.read(conf)
	port = 9889
	try:
		port = cf.getint('server', 'port')
	except:
		print >> sys.stderr, "[ERROR]: read conf file error"
	print port
	return port

def getConf():
	if len(sys.argv) < 2:
		print "[Usage]: python %s confFile" % (sys.argv[0])
		sys.exit(2)
	conf = sys.argv[1]
	if not os.path.exists(conf):
		print "[Error]: conf file %s is not exist" % (sys.argv[1])
		sys.exit(2)
	return conf


def initial(conf):
	global _searcher
	#print _searcher is None
	_searcher = Searcher(conf)
	#print _searcher is None

if __name__ == "__main__":
	conf = getConf()
	initial(conf)
	app = make_app()
	app.listen(getPort(conf))
	_Ioloop.IOLoop.current().start()
