# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_control.config.profiles

Purpose
=======
 Provide access routines for PyRC's profile configuration data.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
import os
import getpass

import pyrc_common.GLOBAL as GLOBAL

import pyrc_shared.parsers as parsers

_xml_handler = None #: A reference to a shared.parsers.XMLWrapper object used to manipulate the XML tree.

def load():
	"""
	This function is used to load profile data.
	
	@return: Nothing.
	
	@raise Ft.Lib.UriException: If the data cannot be located.
	@raise Ft.Xml.ReaderException: If the data is invalid.
	"""
	global _xml_handler
	if not _xml_handler:
		_xml_handler = parsers.XMLWrapper(GLOBAL.PTH_CONFIG_PATH + os.sep + GLOBAL.PTH_PROFILES_CONFIG_FILE)
	_xml_handler.open()
	
def unload():
	"""
	This function is used to unload the data from memory.
	
	@return: Nothing.
	
	@raise IOError: If the data cannot be saved.
	"""
	_xml_handler.close()
	
def getProfile(profile_id):
	"""
	This function is used to get a specific profile from the XML tree.
	
	@type profile_id: basestring
	@param profile_id: The ID of the profile to retrieve.
	
	@rtype: tuple|None
	@return: A tuple of the form returned by _getProfileDetailsFromNode()
	    containing the specified profile, or None if the profile could not be
	    found.
	"""
	try:
		_xml_handler.lock()
		profile = _xml_handler.getNode("/profiles/profile[@id='%s']" % profile_id)
		return _getProfileDetailsFromNode(profile)
	finally:
		_xml_handler.unlock()
		
def getDefaultProfile():
	"""
	This function is used to get the default, "default", if it exists, profile
	for use when authenticating to an IRC network.
	
	If "default" does not exist, the user's current login name will be used for
	the nick, ident, and real name parameters.
	
	@rtype: tuple
	@return: A tuple of the form returned by _getProfileDetailsFromNode()
	    containing the user's default profile.
	"""
	try:
		_xml_handler.lock()
		profile = getProfile('default')
		if profile:
			return profile
		else:
			name = unicode(getpass.getuser())
			return ((name,), name, name)
	finally:
		_xml_handler.unlock()
		
def getAllProfiles():
	"""
	This function is used to get a collection of all defined profiles.
	
	@rtype: dict
	@return: A dictionary of tuples of the type returned by
	    _getProfileDetailsFromNode(), keyed by profile ID.
	"""
	try:
		_xml_handler.lock()
		profiles = {}
		profile_nodes = _xml_handler.getNodes("/profiles/profile")
		for i in profile_nodes:
			profile = _getProfileDetailsFromNode(i)
			if profile:
				profiles[parsers.xml_getAttributeValue(i, 'id')] = profile
				
		return profiles
	finally:
		_xml_handler.unlock()
		
def _getProfileDetailsFromNode(node):
	"""
	This function is used to process a <profile/> node from the XML tree and
	return the details it contains.
	
	@type node: Node|None
	@param node: The node retrieved from the XML tree. This may be None.
	
	@rtype: tuple|None
	@return: The information stored in the <profile/> node, represented as a
	    tuple, or None if the node does not exist. The tuple's
	    structure follows::
		 (<nicknames:tuple>, <ident:unicode>, <real_name:unicode>)
	"""
	if node:
		nicknames = []
		nickname_node = node.xpath("nicknames")[0]
		for i in nickname_node.xpath("nickname"):
			nicknames.append(parsers.xml_getNodeValue(i))
			
		return (nicknames, parsers.xml_getSubNodeValue(node, "ident"), parsers.xml_getSubNodeValue(node, "realname"))
	return None
	