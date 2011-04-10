##############################################################################
## File:  sedna.py
##
## Copyright (C) 2009, Apache License 2.0 
## The Institute for System Programming of the Russian Academy of Sciences
## 
## High level Sedna Python API module.
## See 'examples' folder for examples of using Sedna Python driver.
##############################################################################

""" This module provides access to the Sedna XML database.

This exports:

SednaConnection - class which provides transactions
and query execution facilities.

SednaException  - encapsulates Sedna errors. 
"""

import uuid
import libsedna
import cStringIO

class SednaException(Exception):
	pass

class SednaConnectionDefaultProccessor:
	def initial(self):
		return cStringIO.StringIO()
	def combine(self,state,value):
		state.write(value)
		return state
	def postproccess(self,state):
		temp = state.getvalue();
		state.truncate(0)
		return (state,temp)
	def hook(self,value):
		return value;

class SednaConnection:

	def __init__(self,host,db,login="SYSTEM",passwd="MANAGER"):
		"""Initializes new SednaConnection

			host: host name or IP address
			db: database name
			login: user name (default SYSTEM)
			passwd: user password (default MANAGER)

			Raises SednaException if connection could not be established."""
		self.sednaConnection = libsedna.SednaConnection()
		if libsedna.SEconnect(self.sednaConnection,host,db,login,passwd) != libsedna.SEDNA_SESSION_OPEN:
			self.__raiseException()
		if libsedna.SEsetConnectionAttrInt(self.sednaConnection,libsedna.SEDNA_ATTR_AUTOCOMMIT,libsedna.SEDNA_AUTOCOMMIT_OFF) != libsedna.SEDNA_SET_ATTRIBUTE_SUCCEEDED:
			self.__raiseException()
		self.__modules = {}
		self.__temp_documents = []
	
	def close(self):
		"""Close the connection. A closed connection cannot be used for further operations."""
		if libsedna.SEclose(self.sednaConnection)!= libsedna.SEDNA_SESSION_CLOSED:
			self.__raiseException()
	
	def beginTransaction(self):
		"""Start a new transaction."""
		if libsedna.SEbegin(self.sednaConnection)!= libsedna.SEDNA_BEGIN_TRANSACTION_SUCCEEDED:
			self.__raiseException()
		return self

	def endTransaction(self,how):
		"""Finish the transaction.

			how: either 'commit' or 'rollback'"""
		for doc in self.__temp_documents:
			self.dropDocument(doc)
		self.__temp_documents = []
		if how not in ['commit','rollback']:
			raise SednaException("expecting %s or %s, not %s"%(repr('commit'),repr('rollback'),repr(how)))
		if {'commit':libsedna.SEcommit, 'rollback':libsedna.SErollback}[how](self.sednaConnection) not in [libsedna.SEDNA_COMMIT_TRANSACTION_SUCCEEDED, libsedna.SEDNA_ROLLBACK_TRANSACTION_SUCCEEDED]:
			self.__raiseException()
		return self

	def commit(self):
		return self.endTransaction('commit')
	
	def rollback(self):
		return self.endTransaction('rollback')

	def installModule(self, module, replace = False):
		qs = 'LOAD'
		if replace: qs += ' OR REPLACE'
		qs += ' MODULE "%s"' % module
		return self.execute(qs)
	
	def removeModule(self, namespace):
		return self.execute("DROP MODULE '%s'" % namespace)

	def execute(self,query,**kwargs):
		"""Execute query.

			query: query to execute (string)"""
		if isinstance(query, unicode):
			query = query.encode("utf-8")
		
		for arg in kwargs:
			kwargs[arg] = kwargs[arg].encode("utf-8").replace('&', '&amp;').replace('"', '&quot;').\
			                                          replace("'", "&apos;").replace('<', '&lt;').\
			                                          replace('>', '&gt;')
		
		imports = ""
		for name in self.__modules:
			imports += "import module namespace %s = '%s';\n" % (name, self.__modules[name])
		
		query = imports + (query % kwargs)

		if libsedna.SEexecute(self.sednaConnection,query) not in [libsedna.SEDNA_QUERY_SUCCEEDED, libsedna.SEDNA_UPDATE_SUCCEEDED, libsedna.SEDNA_BULK_LOAD_SUCCEEDED]:
			self.__raiseException()
		return self
	
	def update(self, query, begin_transaction = True, commit_transaction = True,
	                 close_connection = False, **kwargs):
		if begin_transaction:
			self.beginTransaction()
		self.execute(query, **kwargs)
		if commit_transaction:
			self.commit()
			if close_connection:
				self.close()
				return None
		return self
	
	def status(self):
		"""status(self) -> string

			Get current connection status. Either: 'ok', 'closed' or 'failed'"""	
		return {libsedna.SEDNA_CONNECTION_OK:'ok', libsedna.SEDNA_CONNECTION_CLOSED:'closed', libsedna.SEDNA_CONNECTION_FAILED:'failed'}[libsedna.SEconnectionStatus(self.sednaConnection)]
	
	def transactionStatus(self):
		"""transactionStatus(self) -> string

			Get current transaction status. Either: 'active' or 'none'"""
		return {libsedna.SEDNA_TRANSACTION_ACTIVE:'active', libsedna.SEDNA_NO_TRANSACTION:'none'} [libsedna.SEtransactionStatus(self.sednaConnection)]
	
	def isTransactionActive(self):
		return True if libsedna.SEtransactionStatus(self.sednaConnection) == libsedna.SEDNA_TRANSACTION_ACTIVE else False
	
	def resultSequence(self,hook=None,proccessor=None,bufferSize=4096):
		"""Retrieve result of query execution"""
		if proccessor == None:
			proccessor = SednaConnectionDefaultProccessor()
		if hook == None:
			hook = proccessor.hook
		buf = '\000' * bufferSize
		state = proccessor.initial()
		status = libsedna.SEnext(self.sednaConnection)
		while status == libsedna.SEDNA_NEXT_ITEM_SUCCEEDED:
			while True:
				status = libsedna.SEgetData(self.sednaConnection, buf, bufferSize)
				if status == 0:
					break
				if status < 0:
					self.__raiseException()
				state = proccessor.combine(state,hook(buf[:status]))
			(state,result) = proccessor.postproccess(state)
			yield result
			status = libsedna.SEnext(self.sednaConnection)
		if status not in [libsedna.SEDNA_RESULT_END, libsedna.SEDNA_NO_ITEM]:
			self.__raiseException()
	
	
	def _feed_data(self, data, doc, collection):
		if libsedna.SEloadData(self.sednaConnection, data, len(data), doc, collection) not in [libsedna.SEDNA_DATA_CHUNK_LOADED]:
			self.__raiseException()
	
	def loadTemporaryDocument(self, data):
		"""Load tempory document. The document will be dropped at the end of
			the transaction.

			data: either file object, or string with XML to load
			
			Returns the (unique) name of the document.
			"""
		return self._loadDocument(data)
	
	def loadDocument(self, data, doc, collection=None):
		"""Load document.

			data: either file object, or string with XML to load
			doc: database document name data is loaded as.
			collection: collection name data is loaded into

			"""
		self._loadDocument(data, doc, collection)
		
	def _loadDocument(self, data, doc=None, collection=None):
		"""Load document.

			data: either file object, or string with XML to load
			doc: database document name data is loaded as, if not given a temporary document with a random name will be created.
			     if doc is not given the document will be dropped when the transaction ends (commit or rollback).
			collection: collection name data is loaded into
			
			Returns the name of the document.
			"""
		temp = False
		if doc == None:
			temp = True
			doc = str(uuid.uuid4().int)
			while doc in self.__temp_documents:
				doc = str(uuid.uuid4().int)
			self.__temp_documents.append(doc)
		if isinstance(data,file):
			while True:
				d = data.read(4096)
				if d == "":
					break
				self._feed_data(d, doc, collection)
		elif isinstance(data, str):
			self._feed_data(data, doc, collection)
		elif isinstance(data, unicode):
			data = data.encode("utf-8")
			self._feed_data(data, doc, collection)
		else: #assume itreator
			for d in data:
				if isinstance(d, unicode):
					d = d.encode("utf-8")
				self._feed_data(d, doc, collection)
		if libsedna.SEendLoadData(self.sednaConnection) not in [libsedna.SEDNA_BULK_LOAD_SUCCEEDED]:
			if temp:
				del self.__temp_documents[self.__temp_documents.index(doc)]
			self.__raiseException()
		return doc
	
	def dropDocument(self, doc):
		return self.execute("""DROP DOCUMENT "%(doc)s" """ % {'doc': doc})
	
	def loadModule(self, name, namespace):
		if name in self.__modules:
			raise SednaException("Module already loaded")
		self.__modules[name] = namespace
		return self
	
	def unLoadModule(self, name):
		if name not in self.__modules:
			raise SednaException("Module not loaded")
		del self.__modules[name]
		return self
	
	def __raiseException(self):
		raise SednaException(libsedna.SEgetLastErrorMsg(self.sednaConnection))
