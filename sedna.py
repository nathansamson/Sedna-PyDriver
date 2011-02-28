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
		if how not in ['commit','rollback']:
			raise SednaException("expecting %s or %s, not %s"%(repr('commit'),repr('rollback'),repr(how)))
		if {'commit':libsedna.SEcommit, 'rollback':libsedna.SErollback}[how](self.sednaConnection) not in [libsedna.SEDNA_COMMIT_TRANSACTION_SUCCEEDED, libsedna.SEDNA_ROLLBACK_TRANSACTION_SUCCEEDED]:
			self.__raiseException()
		return self

	def execute(self,query):
		"""Execute query.

			query: query to execute (string)"""
		if isinstance(query, unicode):
			query = query.encode("utf-8")
		if libsedna.SEexecute(self.sednaConnection,query) not in [libsedna.SEDNA_QUERY_SUCCEEDED, libsedna.SEDNA_UPDATE_SUCCEEDED, libsedna.SEDNA_BULK_LOAD_SUCCEEDED]:
			self.__raiseException()
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
		
	def loadDocument(self, data, doc, collection=None):
		"""Load document.

			data: either file object, or string with XML to load
			doc: database document name data is loaded as
			collection: collection name data is loaded into"""
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
			self.__raiseException()
	
	def __raiseException(self):
		raise SednaException(libsedna.SEgetLastErrorMsg(self.sednaConnection))
