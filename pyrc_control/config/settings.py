# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_control.config.settings

Purpose
=======
 Provide access routines for PyRC's settings configuration data.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
import os

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.C_FUNCS as C_FUNCS

import pyrc_shared.parsers as parsers

_xml_handler = None #: A reference to a shared.parsers.XMLWrapper object used to manipulate the XML tree.

def load():
	"""
	This function is used to load settings data.
	
	@return: Nothing.
	
	@raise Ft.Lib.UriException: If the data cannot be located.
	@raise Ft.Xml.ReaderException: If the data is invalid.
	"""
	global _xml_handler
	if not _xml_handler:
		_xml_handler = parsers.XMLWrapper(GLOBAL.PTH_CONFIG_PATH + os.sep + GLOBAL.PTH_SETTINGS_CONFIG_FILE)
	_xml_handler.open()
	
def unload():
	"""
	This function is used to unload the data from memory.
	
	@return: Nothing.
	
	@raise IOError: If the data cannot be saved.
	"""
	_xml_handler.close()
	
def getCTCPs():
	"""
	This function is used to get a list of static CTCPs for use by PyRC.
	
	@rtype: tuple
	@return: A tuple containing a list of all CTCPs defined for use by PyRC.
	    Its elements have the following form::
	     (<request:unicode>, <response:unicode>, <final:bool>)
	"""
	try:
		_xml_handler.lock()
		ctcps = []
		for i in _xml_handler.getNodes("/settings/ctcps/ctcp"):
			value = C_FUNCS.evaluateTruth(parsers.xml_getAttributeValue(i, 'final'))
			request = parsers.xml_getSubNodeValue(i, "request")
			response = parsers.xml_getSubNodeValue(i, "response")
			
			ctcps.append((request, response, value))
			
		return tuple(ctcps)
	finally:
		_xml_handler.unlock()
		
def getFormat(format_path):
	"""
	This function is used to get a format value from the settings data.
	
	@type option_path: basestring
	@param option_path: The path of the format to be retrieved, dot-separated.
	
	@rtype: unicode|None
	@return: The requested value, or None if the value could not be found.
	"""
	try:
		_xml_handler.lock()
		return parsers.xml_getNodeValue(_xml_handler.getNode("/settings/formats/" + format_path.replace(".", "/")))
	finally:
		_xml_handler.unlock()
		
def getInterface():
	"""
	This function is used to get the interface value from the settings data.
	
	@rtype: unicode|None
	@return: The interface value, or None if no interface is specified.
	"""
	try:
		_xml_handler.lock()
		node = _xml_handler.getNode("/settings/interface")
		if not node:
			return
		return parsers.xml_getNodeValue(node)
	finally:
		_xml_handler.unlock()
		
def getOption(option_path):
	"""
	This function is used to get an option value from the settings data.
	
	@type option_path: basestring
	@param option_path: The path of the option to be retrieved, dot-separated.
	
	@rtype: unicode|None
	@return: The requested value, or None if the value could not be found.
	"""
	try:
		_xml_handler.lock()
		return parsers.xml_getNodeValue(_xml_handler.getNode("/settings/options/" + option_path.replace(".", "/")))
	finally:
		_xml_handler.unlock()
		
def getPlugins():
	"""
	This function is used to get a list of the plugins registered for use with
	PyRC.
	
	@rtype: tuple
	@return: A tuple containing the names of all plugins registered for use with
	    PyRC. Its elements have the following form::
	     (<module_name:unicode>, <load:bool>)
	"""
	try:
		_xml_handler.lock()
		plugins = []
		for i in _xml_handler.getNodes("/settings/plugins/plugin"):
			value = parsers.xml_getAttributeValue(i, 'load')
			if value:
				value = C_FUNCS.evaluateTruth(value)
			else:
				value = True
				
			plugins.append((parsers.xml_getNodeValue(i), value))
			
		return tuple(plugins)
	finally:
		_xml_handler.unlock()
		