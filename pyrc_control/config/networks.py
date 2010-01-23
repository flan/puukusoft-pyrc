# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_control.config.networks

Purpose
=======
 Provide access routines for PyRC's network configuration data.
 
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
	This function is used to load network data.
	
	@return: Nothing.
	
	@raise Ft.Lib.UriException: If the data cannot be located.
	@raise Ft.Xml.ReaderException: If the data is invalid.
	"""
	global _xml_handler
	if not _xml_handler:
		_xml_handler = parsers.XMLWrapper(GLOBAL.PTH_CONFIG_PATH + os.sep + GLOBAL.PTH_NETWORKS_CONFIG_FILE)
	_xml_handler.open()
	
def unload():
	"""
	This function is used to unload the data from memory.
	
	@return: Nothing.
	
	@raise IOError: If the data cannot be saved.
	"""
	_xml_handler.close()
	
def getNetwork(network_id):
	"""
	This function is used to get a dictionary describing the network identified
	by the given ID.
	
	@type network_id: basestring
	@param network_id: The ID to search for.
	
	@rtype: dict|None
	@return: A dictionary of the type returned by _getNetworkDetailsFromNode(),
	    or None if the ID could not be found.
	"""
	try:
		_xml_handler.lock()
		network = _xml_handler.getNode("/networks/network[@id='%s']" % network_id)
		return _getNetworkDetailsFromNode(network)
	finally:
		_xml_handler.unlock()
		
def getNetworkByAddress(address):
	"""
	This function is used to get a dictionary describing the network that
	contains the specified address.
	
	@type address: basestring
	@param address: The address to search for.
	
	@rtype: dict|None
	@return: A dictionary of the type returned by _getNetworkDetailsFromNode(),
	    or None if the address could not be found.
	"""
	try:
		_xml_handler.lock()
		networks = _xml_handler.getNodes("/networks/network")
		for i in networks:
			network = _getNetworkDetailsFromNode(i)
			for j in network['addresses'][1]:
				if j[0].lower() == address:
					return network
					
		return None
	finally:
		_xml_handler.unlock()
		
def getAllNetworks():
	"""
	This function is used to get a dictionary of all defined networks.
	
	@rtype: dict
	@return: A dictionary of dictionaries of the type returned by
	    _getNetworkDetailsFromNode(), keyed by network id.
	"""
	try:
		_xml_handler.lock()
		networks = _xml_handler.getNodes("/networks/network")
		network_list = {}
		for i in networks:
			network = _getNetworkDetailsFromNode(i)
			network_list[network['id']] = network
			
		return network_list
	finally:
		_xml_handler.unlock()
		
def _getNetworkDetailsFromNode(node):
	"""
	This function is used to process a <network/> node from the XML tree and
	return the details it contains.
	
	@type node: Node|None
	@param node: The node retrieved from the XML tree. This may be None.
	
	@rtype: dict|None
	@return: The information stored in the <network/> node, represented as a
	    dictionary, or None if the node does not exist. The dictionary's
	    structure follows::
		 {
		  'id': <network_id:unicode>,
		  'name': <user-specified_network_name:unicode|None>,
		  'description': <user-specified_network_description:unicode|None>,
		  'autoconnect': <auto_connect:bool>,
		  'workerthreads': <worker_threads:int>,
		  'proxy': <proxy_identifier:unicode|None>,
		  'addresses': <(randomize_addresses:bool, addresses_data:list)>,
		  'profiles': <(use_all:bool, profile_data:tuple)>,
		  'channels': <channel_names:tuple>
		 }
	"""
	if node:
		#Get network data.
		id = parsers.xml_getAttributeValue(node, 'id')
		autoconnect = C_FUNCS.evaluateTruth(parsers.xml_getAttributeValue(node, 'autoconnect'))
		workerthreads = parsers.xml_getAttributeValue(node, 'workerthreads')
		if workerthreads:
			workerthreads = int(workerthreads)
		else:
			workerthreads = GLOBAL.USR_SERVER_THREADS	
		proxy = parsers.xml_getAttributeValue(node, 'proxy')
		
		name = parsers.xml_getSubNodeValue(node, "name")
		description = parsers.xml_getSubNodeValue(node, "description")
		
		#Get address data.
		address_node = node.xpath("addresses")[0]
		addresses_random = parsers.xml_getAttributeValue(address_node, 'randomorder')
		if not addresses_random or C_FUNCS.evaluateTruth(addresses_random):
			addresses_random = True
		else:
			addresses_random = False
			
		addresses = []
		for i in address_node.xpath("address"):
			addresses.append((
			 parsers.xml_getSubNodeValue(i, "url"),
			 int(parsers.xml_getSubNodeValue(i, "port")),
			 C_FUNCS.evaluateTruth(parsers.xml_getAttributeValue(i, 'secure')),
			 parsers.xml_getAttributeValue(i, 'proxy')
			))
			
		#Get profile data.
		profiles_use_all = True
		profiles = []
		profile_nodes = node.xpath("profiles")
		if profile_nodes:
			profile_node = profile_nodes[0]
			profiles_use_all = parsers.xml_getAttributeValue(profile_node, 'useall')
			if not profiles_use_all or C_FUNCS.evaluateTruth(profiles_use_all):
				profiles_use_all = True
			else:
				profiles_use_all = False
				
			for i in profile_node.xpath("profile"):
				profiles.append(parsers.xml_getNodeValue(i))
				
		#Get channel data.
		channels = []
		channel_nodes = node.xpath("channels")
		if channel_nodes:
			channel_node = channel_nodes[0]
			for i in channel_node.xpath("channel"):
				channels.append(parsers.xml_getNodeValue(i))
				
		return {
		 'id': id,
		 'name': name,
		 'description': description,
		 'autoconnect': autoconnect,
		 'workerthreads': workerthreads,
		 'proxy': proxy,
		 'addresses': (addresses_random, addresses),
		 'profiles': (profiles_use_all, tuple(profiles)),
		 'channels': tuple(channels)
		}
	return None
	