# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_shared.convenience

Purpose
=======
 Provide functionality frequently needed by plugins.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""

import pyrc_common.GLOBAL as GLOBAL
_ial = GLOBAL.irc_interface.processDictionary

def handleChannelMessage(dictionary, allowed_sources, ignore_action=True):
	"""
	This function is used to determine whether a given "Channel Message" or
	"Channel Message Local" Event Dictionary should be evaluated.
	
	Basically, it acts as a filter, and it should be the first function called
	when screening events to find out which ones came from a channel the plugin
	cares about.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to be processed.
	@type allowed_sources: dict
	@param allowed_sources: A dictionary of sequences of allowed sources, keyed
	    by network name.
	    
	    An example follows::
	     {'synIRC': ("#animesuki.os", "#pyrc", "flan")}
	@type ignore_action: bool
	@param ignore_action: An optional value that may be used to control whether
	    messages that are actions should be rejected.
	
	@rtype: tuple|None
	@return: The name of the user who triggered the event, and a boolean value
	    that is True on local events, if the event should be processed, or None
	    if it should be ignored.
	
	@raise DictionaryTypeError: If the given Event Dictionary is not a channel
	    message variant.
	"""
	if dictionary['eventname'] not in ("Channel Message", "Channel Message Local"):
		raise DictionaryTypeError("Invalid dictionary type: %s" % dictionary['eventname'])
		
	if ignore_action and dictionary['action']:
		return None
		
	network = allowed_sources.get(dictionary['networkname'])
	if network and dictionary['channel'] in network:
		if dictionary['eventname'] == "Channel Message":
			return (dictionary['userdata']['username'], False)
		else:
			return (dictionary['username'], True)
			
	return None
	
def respondToChannelMessage(message, dictionary, action=False):
	"""
	This function is used to send a message to a channel in response to a
	"Channel Message" or "Channel Message Local" Event Dictionary.
	
	@type message: basestring
	@param message: The string to send to the channel.
	@type dictionary: dict
	@param dictionary: The Event Dictionary being responded to.
	@type action: bool
	@param action: An optional parameter, used to indicate whether this message
	    should be sent as an action. The default is False.
	
	@return: Nothing.
	
	@raise DictionaryTypeError: If the given Event Dictionary is not a channel
	    message variant.
	"""
	if dictionary['eventname'] not in ("Channel Message", "Channel Message Local"):
		raise DictionaryTypeError("Invalid dictionary type: %s" % dictionary['eventname'])
		
	_ial({
	 'eventname': 'Channel Message',
	 'irccontext': dictionary['irccontext'],
	 'channel': dictionary['channel'],
	 'message': message,
	 'action': action,
	 'send': True
	})
	
def handlePrivateMessage(dictionary, allowed_sources, ignore_action=True):
	"""
	This function is used to determine whether a given "Private Message" or
	"Private Message Local" Event Dictionary should be evaluated.
	
	Basically, it acts as a filter, and it should be the first function called
	when screening events to find out which ones came from a query the plugin
	cares about.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to be processed.
	@type allowed_sources: dict
	@param allowed_sources: A dictionary of sequences of allowed sources, keyed
	    by network name.
	    
	    An example follows::
	     {'synIRC': ("#animesuki.os", "#pyrc", "flan")}
	@type ignore_action: bool
	@param ignore_action: An optional value that may be used to specify whether
	    messages that are actions should be rejected.
	
	@rtype: tuple|None
	@return: The name of the other user in the conversation, and a boolean value
	    that is True on local events, if the event should be processed, or None
	    if it should be ignored.
	
	@raise DictionaryTypeError: If the given Event Dictionary is not a private
	    message variant.
	"""
	if dictionary['eventname'] not in ("Private Message", "Private Message Local"):
		raise DictionaryTypeError("Invalid dictionary type: %s" % dictionary['eventname'])
		
	if ignore_action and dictionary['action']:
		return None
		
	network = allowed_sources.get(dictionary['networkname'])
	if network:
		if dictionary['eventname'] == "Private Message":
			user_name = dictionary['userdata']['username']
			if user_name.lower() in network:
				return (user_name, False)
		else:
			user_name = dictionary['target']
			if user_name.lower() in network:
				return (user_name, True)
				
	return None
	
def respondToPrivateMessage(message, dictionary, action=False):
	"""
	This function is used to send a message to a user in response to a
	"Private Message" or "Private Message Local" Event Dictionary.
	
	@type message: basestring
	@param message: The string to send to the user.
	@type dictionary: dict
	@param dictionary: The Event Dictionary being responded to.
	@type action: bool
	@param action: An optional parameter, used to indicate whether this message
	    should be sent as an action. The default is False.
	
	@return: Nothing.
	
	@raise DictionaryTypeError: If the given Event Dictionary is not a private
	    message variant.
	"""
	user_name = None
	
	if dictionary['eventname'] == "Private Message":
		user_name = dictionary['userdata']['username']
	elif dictionary['eventname'] == "Private Message Local":
		user_name = dictionary['target']
	else:
		raise DictionaryTypeError("Invalid dictionary type: %s" % dictionary['eventname'])
		
	_ial({
	 'eventname': 'Private Message',
	 'irccontext': dictionary['irccontext'],
	 'username': user_name,
	 'message': message,
	 'action': action,
	 'send': True
	})
	
def evaluateRank(data, target, channel=None, context_id=None):
	"""
	This function is used to determine what the rank of a user is, either based
	on an arbitrary username or based on a Channel Message or Channel Message
	Local Event Dictionary.
	
	@type data: basestring|dict
	@param data: The name of the user to be looked up as a string, which implies
	    a need for the specification of channel, or a Channel Message or Channel
	    Message Local dictionary.
	@type target: basestring|sequence
	@param target: A single-character string identifying the rank to compare
	    against, or a sequence of single-character strings indentifying all
	    acceptable ranks.
	@type channel: basestring
	@param channel: The name of the channel from which the user's rank should be
	    derived.
	    
	    This parameter is optional, needed only if looking up the rank of a user
	    based on a string received in another channel or query, or if only the
	    user's name is known.
	    
	    If this parameter is specified, context_id and ial need to be specified,
	    as well.
	@type context_id: int
	@param context_id: The session-unique identifier used to indicate the network
	    where the user lookup should occur. This value is included in every
	    Outbound Event Dictionary.
	    
	    This parameter only needs to be specified if channel is specified.
	
	@rtype: int|bool|None
	@return: If target is specified as a character, an int is returned. Its
	    possible values are specified below::
	     -1:
	      The user's rank is less than the specified value or the user has no
	      rank
	     0:
	      The user's rank is equal to the specified value
	     1:
	      The user's rank is greater than the specified value
	    
	    If target is specified as a sequence, a bool is returned with a value of
	    True if the user's rank is one of the specified values, or False if it
	    is not.
	    
	    In either case, if a lookup channel is specified and the user cannot be
	    found, None is returned.
	    
	    Note: False and 0 are both NoneTypes, so they must be explicitly
	    matched.
	
	@raise ArgumentTypeError: If one of the given multi-type arguments is
	    incorrectly specified.
	"""
	if not type(data) in (dict, str, unicode):
		raise ArgumentTypeError(u"'data' must be a Channel Message( Local) Event Dictionary or a string, not '%s'." % type(user))
		
	if not type(target) in (tuple, list, str, unicode):
		raise ArgumentTypeError(u"'target' must be a sequence or a character, not '%s'." % type(target))
		
	symbol = None
	
	if type(data) == dict and data['eventname'] == "Channel Message Local":
		context_id = data['irccontext'],
		channel = data['channel'],
		data = data['username']
		
	if channel:
		user_name = data
		if type(data) == dict:
			user_name = data['userdata']['username']
			
		user = _ial({
		 'eventname': "Get User",
		 'irccontext': context_id,
		 'channel': channel,
		 'username': user_name
		})
		
		if user:
			symbol = user['user']['symbol']
		else:
			return
	else:
		if type(data) == dict:
			if data['eventname'] == "Channel Message":
				symbol = data['userdata']['symbol']
			else:
				raise ArgumentTypeError(u"'data' must be a Channel Message( Local) Event Dictionary.")
		else:
			raise ArgumentTypeError(u"'data' must be a Channel Message( Local) Event Dictionary when not specifying a channel.")
			
	if type(target) in (tuple, list):
		for i in target:
			if symbol == (GLOBAL.IRC_RANK_MAP[i] or i):
				return True
		return False
	else:
		if not symbol:
			return -1
			
		target = (GLOBAL.IRC_RANK_MAP.get(target) or target)
		match_point_reached = False
		for i in GLOBAL.IRC_RANK_PREFIX:
			if not match_point_reached and i == target:
				match_point_reached = True
				if i == symbol:
					return 0
					
			if i == symbol:
				if match_point_reached:
					return -1
				return 1
				
				
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
		
		
class DictionaryTypeError(Error):
	"""
	This class represents problems that might occur if an incorrect Event
	Dictionary is processed.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new DictionaryTypeError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		self.description = unicode(description)
		
		
class ArgumentTypeError(Error):
	"""
	This class represents problems that might occur if an incorrect argument is
	passed.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new ArgumentTypeError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		self.description = unicode(description)
		
