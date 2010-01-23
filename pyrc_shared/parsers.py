# -*- coding: utf-8 -*-
"""
PyRC module: shared.parsers

Purpose
=======
 Provide generic data processing objects for use by all modules that need to
 manage persistent configuration data.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
import threading
import sys
import ConfigParser

import Ft.Xml.Domlette as dom

_config_wrappers = {} #: A dictionary of ConfigWrapper objects, keyed by filepath. Used to force Singleton access.
_xml_wrappers = {} #: A dictionary of XMLWrapper objects, keyed by filepath. Used to force Singleton access.

class _DataWrapper(object):
	"""
	This class defines a generic data-processing object.
	
	It should not be instantiated directly. Use ConfigWrapper and XMLWrapper.
	"""
	_data = None #: The data structure, if loaded.
	_file = None #: The path of the file managed by this _DataWrapper object.
	_lock = None #: A lock used to prevent multiple simultaneous accesses to the data.
	_modified = False #: True if the data has been modified, indicating the need to save on unload.
	_references = 0 #: A reference counter that tracks the number of times this file has been opened.
	
	def __init__(self, file_path):
		"""
		This function is invoked when a new _DataWrapper object is created.
		
		@type file_path: basestring
		@param file_path: The path of the file managed by this object.
		
		@return: Nothing.
		"""
		self._lock = threading.RLock()
		self._file = file_path
		
	def open(self):
		"""
		This function is called to load the data structure into memory.
		
		The data will not be reloaded unnecessarily. Instead, the number of
		calls to this function is recorded, and the tree will not be closed
		until every	load request has resolved with a call to close().
		
		@return: Nothing.
		
		@raise Exception: If the data structure could not be loaded. See
		    implementing classes' _open() functions for details.
		"""
		try:
			self._lock.acquire()
			
			self._references += 1
			
			if self._references > 1: #The data structure is already loaded.
				return
				
			#Load the data structure.
			try:
				self._open()
				self._modified = False
			finally:
				self._references = 0
		finally:
			self._lock.release()
			
	def close(self):
		"""
		This function is called to unload the data structure from memory.
		
		The data will only be unloaded once the number of calls to open()
		matches the number of calls to close().
		
		The data structure will be saved if it has been marked as modified by a
		call to modify().
		
		@return: Nothing.
		
		@raise IOError: If a problem occurs while attempting to save the data.
		"""
		try:
			self._lock.acquire()
			if not self._references: #Prevent negative values.
				return
				
			self._references -= 1
			
			if self._references: #The data cannot be closed yet.
				return
				
			if self._modified:
				self._close()
			self._data = None
		finally:
			self._lock.release()
			
	def lock(self):
		"""
		This function is used to lock the data structure when a thread needs to
		make one or more requests.
		
		@return: Nothing.
		"""
		self._lock.acquire()
		
	def unlock(self):
		"""
		This function is used to unlock the data structure once a thread has
		finished making its requests.
		
		@return: Nothing.
		"""
		self._lock.release()
		
	def modify(self):
		"""
		This function is used to mark the data structure as modified, indicating
		that it must be saved when it is unloaded.
		
		@return: Nothing.
		"""
		self._modified = True
		
	def getData(self):
		"""
		This function is used to get the data structure.
		
		@rtype: Document
		@return: The data structure.
		"""
		return self._data
		
		
class ConfigWrapper(_DataWrapper):
	"""
	This class defines a generic config-processing object that handles file
	management and dataset access control.
	"""	
	_file_object = None #: A handle for the file managed by this ConfigWrapper.
	
	def __init__(self, file_path):
		"""
		This function is invoked when a new ConfigWrapper object is created.
		
		If another ConfigWrapper exists to manage the same file, this one will
		become that one, else a new one will be created.
		
		@type file_path: basestring
		@param file_path: The path of the file managed by this object.
		
		@return: Nothing.
		
		@raise InstantiationError: If the specified filepath is known to be
		    something other than a config file.
		"""
		wrapper = _config_wrappers.get(file_path)
		if wrapper:
			self = wrapper
		else:
			if file_path in _xml_wrappers:
				raise InstantiationError(u"The specified filepath has already been identified as an XML file.")
			_config_wrappers[file_path] = self
			_DataWrapper.__init__(self, file_path)
			
	def _open(self):
		"""
		This function is called to load the dataset into memory.
		
		@return: Nothing.
		
		@raise IOError: If the config file could not be read.
		"""
		self._data = configParser.ConfigParser()
		self._data.readfp(open(self._file, 'r'))
		
	def _close(self):
		"""
		This function is called to save the dataset.
		
		@return: Nothing.
		
		@raise IOError: If a problem occurs while attempting to save the data.
		"""
		self._data.write(open(self._file, 'w'))
		
	def getValue(self, option):
		"""
		This function is used to retrieve a value from the dataset.
		
		@type option: basestring
		@param option: The dot-delimited path of the option to get.
		
		@rtype: string
		@return: The requested value.
		
		@raise ConfigParser.NoSectionError: If the specified section does not
		    exist.
		@raise ConfigParser.NoOptionError: If the specified option does not
		    exist.
		"""
		(section, option) = option.split('.', 1)
		return self._data.get(section, option)
		
	def setValue(self, option, value):
		"""
		This function is used to set a value in the dataset.
		
		@type option: basestring
		@param option: The dot-delimited path of the option to set.
		@type value: variable
		@param value: The value to store as the specified option. This value
		    will be coerced to a string.
		
		@return: Nothing.
		"""
		(section, option) = option.split('.', 1)
		if not self._data.has_section(section):
			self._data.add_section(section)
			
		self._data.set(section, option, value)
		self.modify()
		
		
class XMLWrapper(_DataWrapper):
	"""
	This class defines a generic XML-processing object that handles file
	management and tree access control.
	"""	
	def __init__(self, file_path):
		"""
		This function is invoked when a new ConfigWrapper object is created.
		
		If another XMLWrapper exists to manage the same file, this one will
		become that one, else a new one will be created.
		
		@type file_path: basestring
		@param file_path: The path of the file managed by this object.
		
		@return: Nothing.
		
		@raise InstantiationError: If the specified filepath is known to be
		    something other than an XML file.
		"""
		wrapper = _xml_wrappers.get(file_path)
		if wrapper:
			self = wrapper
		else:
			if file_path in _config_wrappers:
				raise InstantiationError(u"The specified filepath has already been identified as a non-XML file.")
			_config_wrappers[file_path] = self
			_DataWrapper.__init__(self, file_path)
			
	def _open(self):
		"""
		This function is called to load the XML tree into memory.
		
		@return: Nothing.
		
		@raise Ft.Lib.UriException: If the source path is invalid.
		@raise Ft.Xml.ReaderException: If the XML tree is invalid.
		"""
		self._data = dom.ValidatingReaderBase().parseUri(self._file)
		
	def _close(self):
		"""
		This function is called to save the XML tree.
		
		@return: Nothing.
		
		@raise IOError: If a problem occurs while attempting to save the tree.
		"""
		output_file = open(self._file, 'w')
		dom.PrettyPrint(self._data, output_file)
		output_file.close()
		
	def getNodes(self, xpath_string):
		"""
		This function is used to execute an XPath query on the root of the XML
		tree to get a list of matching nodes.
		
		@type xpath_string: basestring
		@param xpath_string: The XPath query to use.
		
		@rtype: list
		@return: A list of all nodes found by the XPath query.
		"""
		return self._data.documentElement.xpath(xpath_string)
		
	def getNode(self, xpath_string):
		"""
		This function is used to execute an XPath query on the root of the XML
		tree to get the first (generally only) node that matches.
		
		@type xpath_string: basestring
		@param xpath_string: The XPath query to use.
		
		@rtype: Node|None
		@return: The node found by the XPath query or None if the search failed.
		"""
		nodes = self.getNodes(xpath_string)
		if nodes:
			return nodes[0]
		else:
			return None
			
	def getRootNode(self):
		"""
		This function is used to get the root node of the XML tree.
		
		@rtype: Node
		@return: The root node of the XML tree.
		"""
		return self._data.documentElement
		
		
def xml_getSubNodeValue(node, query):
	"""
	This function takes a node from an arbitrary XML tree, performs an XPath
	lookup, and returns the value of the requested node.
	
	@type node: Node
	@param node: The node on which the query should be performed.
	@type query: basestring
	@param query: The XPath query to be performed.
	
	@rtype: unicode
	@return: The value of the requested node or '' if the node does not exist.
	"""
	nodes = node.xpath(query)
	if nodes:
		return xml_getNodeValue(nodes[0])
	else:
		return u''
		
def xml_getNodeValue(node):
	"""
	This function takes an arbitrary #PCDATA node from an arbitrary XML tree and
	returns its value without linebreaks or padding spaces.
	
	@type node: Node
	@param node: The node from which text is to be retrieved.
	
	@rtype: unicode
	@return: The value of the node or '' if the node does not exist.
	"""
	if node:
		return node.firstChild.nodeValue.replace("\n", "").replace("\r", "").strip()
	return u''
	
def xml_getAttributeValue(node, attribute):
	"""
	This function takes an arbitrary node from an arbitrary XML tree and returns
	the value of the specified attribute.
	
	@type node: Node
	@param node: The node from which text is to be retrieved.
	@type attribute: basestring
	@param attribute: The identifier of the attribute to be retrieved.
	
	@rtype: unicode
	@return: The value of the attribute or '' if the attribute does not exist.
	"""
	if node:
		value = node.attributes.get((None, attribute))
		if value:
			return value.value
	return u''
	
class Error(Exception):
	"""
	This class serves as the base from which all exceptions native to this
	module are derived.
	"""
	description = None #: A description of the error.
	
	def __str__(self):
		"""
		This function returns an ASCII version of the description of this Error.
		
		When possible, the Unicode version should be used instead.		
		
		@rtype: str
		@return: The description of this error. 
		"""
		return str(self.description)
		
	def __unicode__(self):
		"""
		This function returns the description of this Error.		
		
		@rtype: unicode
		@return: The description of this error. 
		"""
		return self._description
		
	def __init__(self, description):
		"""
		This function is invoked when creating a new Error object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		self.description = unicode(description)
		
		
class InstantiationError(Error):
	"""
	This class represents problems that might occur during class instantiation.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new InstantiationError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		Error.__init__(self, description)
		