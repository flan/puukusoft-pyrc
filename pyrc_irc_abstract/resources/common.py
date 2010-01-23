# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.resources.common

Purpose
=======
 Provide general functions required by multiple modules to process data from IRC
 networks.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
def splitModes(modestring_raw):
	"""
	This function takes a raw modestring and splits its constituents.
	
	The output is a tuple or tuples that spell out the details of each mode
	encountered.
	
	Sample I/O::
	 -vv+hhh flan PyRC flan basket PyRC
	    (('v', 'flan', False), ('v', 'PyRC', False), ('h', 'flan', True),
	     ('h', 'basket', True), ('h', 'PyRC', True))
	 +sntrCT
	    (('s', None, True), ('n', None, True), ('t', None, True),
	     ('r', None, True), ('C', None, True), ('T', None, True))
	 +sntrcVCf [5j#R,30m#M,5n#N10,6t#b]:10
	    (('s', None, True), ('n', None, True), ('t', None, True),
	     ('r', None, True), ('c', None, True), ('V', None, True),
	     ('C', None, True), ('f', '[5j#R,30m#M,5n#N10,6t#b]:10', True))
	
	@type modestring_raw: basestring
	@param modestring_raw: The raw modestring received from the IRC server.
	
	@rtype: tuple
	@return: A tuple of tuples of the following form::
	     (<mode:unicode>, <parameter:unicode|None>, <granted:bool>)
	    
	    - 'mode' is a single-character flag representing the mode.
	    - 'parameter' is the parameter associated with the mode, like a channel
	      key or nickname
	    - 'granted' is True if the mode is set or being set, and False if the
	      mode is being removed.
	
	@raise ProcessingError: If there are more parameters than modes.
	"""
	tokens = modestring_raw.split()
	changes = []
	grant = True
	for i in tokens[0]: #Build a list of changed/set modes.
		if i == '+':
			grant = True
		elif i == '-':
			grant = False
		else:
			changes.append((unicode(i), None, grant))
			
	tokens = tokens[1:]
	if len(tokens) > len(changes):
		raise ProcessingError(u"More modes than expected. The IRC spec has been violated.")
	pairs = []
	while tokens: #Pair parameters with modes.
		change = changes.pop()
		pairs.insert(0, (change[0], unicode(tokens.pop()), change[2]))
		
	return tuple(changes + pairs) #Combine standalone changes and paired changes
	