# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.resources.user_functions

Purpose
=======
 Provide user-hostmask-related parsing functions.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2005-2007
"""
import re

import tld_table

import pyrc_common.dictionaries.information as informationDictionaries
#The following dictionaries are used by this module:
##User Data

_USR_REGEXP = re.compile("(.*?)!(.*?)@(.*)") #: The regular expression used to split raw user data.

def splitUserData(raw_user_string):
	"""
	This function takes a "nick!ident@hostmask" string and breaks it into its
	component elements.
	
	@type raw_user_string: basestring
	@param raw_user_string: A string like "flan!~flonne@cg.shawcable.net".
	
	@rtype: tuple
	@return: A tuple(3) of the following form::
	     (<nickname:unicode>, <ident:unicode|None>, <hostmask:unicode|None>)
	    
	    Note: ident and hostmask will be None only if raw_user_string wasn't
	    of the expected form. In such a case, nickname will be the entire
	    raw_user_string.
	"""
	#Sanitize input
	raw_user_string = unicode(raw_user_string)
	
	m = _USR_REGEXP.match(raw_user_string)
	if m:
		return (m.group(1), m.group(2), m.group(3))
	else:
		return (raw_user_string, None, None)
		
def generateUserData(user_data):
	"""
	This function takes a (nickname, ident, hostmask) tuple and uses it to
	generate a "User Data" dictionary.
	
	@type user_data: tuple
	@param user_data: A tuple of the following form::
	     (<nickname:unicode>, <ident:unicode|None>, <hostmask:unicode|None>)
	
	@rtype: dict
	@return: A dictionary of the form returned by
	    common.dictionaries.information.User_Data().
	"""
	country = None
	if user_data[2]:
		country = tld_table.tldLookup(user_data[2])
		
	return informationDictionaries.User_Data(user_data[0], user_data[1], user_data[2], country, None, None, None, None, None)
	