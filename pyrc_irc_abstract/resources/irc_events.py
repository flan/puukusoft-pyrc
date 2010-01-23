# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.resources.irc_events

Purpose
=======
 Handle colon-prefixed, non-colon prefixed, and every other kind of IRC event,
 except those with numbered codes.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2005-2007
"""
import time

import user_functions
import ctcp_core
import common

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.dictionaries.outbound as outboundDictionaries
#The following dictionaries are used by this module:
##IRC Channel Close
##IRC Channel Invite
##IRC Channel Message
##IRC Channel Modes Update
##IRC Channel New Topic
##IRC Channel User Join
##IRC Channel User Part
##IRC Ping
##IRC Pong
##IRC Private Message
##IRC Raw Event
##IRC User Modes
##IRC User Nickname Change
##IRC User Notice
##IRC User Quit
##PyRC Implement Me
##Server Kill
##Server Message

def _serverMessage(server, data):
	"""
	This function emits a 'Server Message' dictionary for the given text.
	
	This is used primarily when there is no reason to process the IRC server's
	event, since it is purely informational.
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object that received this event.
	@type data: unicode
	@param data: The payload of the event.
	
	@return: Nothing
	"""
	server.addEvent(outboundDictionaries.Server_Message(server.getContextID(), server.getName(), data))
	
def _generateNonColon():
	"""
	This function returns a dictionary of functions mapped to identifying
	event tokens.
	
	All stored functions have the same input and output signatures::
	 server:
	  pyrc_irc_abstract.irc_server.Server : A reference to the Server object
	                                        received the event.
	 data:
	  unicode : The payload of the event.
	  
	 Return:
	 	None : Nothing is returned, unless PyRC needs to disconnect.
	 Raise:
	   Varies : An exception is raised if the spec parsing routine fails.
	
	@rtype: dict
	@return: A dictionary of functions keyed by identifying event tokens.
	"""
	nc = {}
	
	def _ERROR(server, data):
		return (data, True) #Just disconnect with the server's reason.
	nc['ERROR'] = _ERROR
	
	def _PING(server, data):
		#Pings are handled automatically; an event is raised strictly for
		#informational purposes.
		server.send("PONG :%s" % data, GLOBAL.ENUM_SERVER_SEND_PRIORITY.CRITICAL)
		server.addEvent(outboundDictionaries.IRC_Ping(server.getContextID(), server.getName(), data, None))
	nc['PING'] = _PING
	
	return nc
_non_colon_events = _generateNonColon() #: A dictionary of functions, keyed by event name.
del _generateNonColon

def _generateServerCodes():
	"""
	This function returns a dictionary of functions mapped to identifying
	event tokens.
	
	All stored functions have the same input and output signatures::
	 server:
	  pyrc_irc_abstract.irc_server.Server : A reference to the Server object
	                                        that received the event.
	 data:
	  unicode : The payload of the event.
	 target:
	  basestring : The name of the event's target, typically a user or a
	               channel.
	 nickname:
	  basestring : The nickname of the user described by this event.
	
	 Return:
	 	None : Nothing is returned, unless PyRC needs to disconnect.
	 Raise:
	   Varies : An exception is raised if the spec parsing routine fails.
	
	@rtype: dict
	@return: A dictionary of functions keyed by identifying event tokens.
	"""
	sc = {}
	
	def _MODE(server, data, target, nickname):
		modes = common.splitModes(data)
		if target[0] in GLOBAL.IRC_CHANNEL_PREFIX:
			channel = server.getChannel(target)
			if not channel:
				return
				
			channel.updateModes(modes)
			user_data = channel.getUserData(nickname)
			if not user_data:
				user_data = user_functions.generateUserData(user_functions.splitUserData(nickname))
			server.addEvent(outboundDictionaries.IRC_Channel_Modes_Update(server.getContextID(), server.getName(), target, modes, data, {}, channel.getModes(), channel.getModeStringFull(), channel.getModeStringSafe(), user_data))
		else:
			server.updateUserModes(modes)
			server.addEvent(outboundDictionaries.IRC_User_Modes(server.getContextID(), server.getName(), nickname, modes, data, server.getUserModes(), server.getUserModeString()))
	sc['MODE'] = _MODE
	
	def _NOTICE(server, data, target, nickname):
		_serverMessage(server, data)
	sc['NOTICE'] = _NOTICE
	
	def _PONG(server, data, target, nickname):
		server.addEvent(outboundDictionaries.IRC_Pong(server.getContextID(), server.getName(), server.processPong(), None))
	sc['PONG'] = _PONG
	
	return sc
_server_code_events = _generateServerCodes() #: A dictionary of functions, keyed by event name.
del _generateServerCodes

def _generateResponseCodes():
	"""
	This function returns a dictionary of functions mapped to identifying
	event tokens.
	
	All stored functions have the same input and output signatures::
	 server:
	  pyrc_irc_abstract.irc_server.Server : A reference to the Server object
	                                        that received the event.
	 data:
	  unicode : The payload of the event.
	 target:
	  basestring : The name of the event's target, typically a user or a
	               channel.
	 user_data:
	  basestring : A User Data Information Dictionary, channel-specific if
	  possible.
	  
	 Return:
	 	None : Nothing is returned, unless PyRC needs to disconnect.
	 Raise:
	   Varies : An exception is raised if the spec parsing routine fails.
	
	@rtype: dict
	@return: A dictionary of functions keyed by identifying event tokens.
	"""
	rc = {}
	
	def _INVITE(server, data, target, user_data): #:flonne!~flonne@Free.Phone.Chatline INVITE YUO :#pyrc
		server.addEvent(outboundDictionaries.IRC_Channel_Invite(server.getContextID(), server.getName(), data.lower(), user_data))
	rc['INVITE'] = _INVITE
	
	def _JOIN(server, data, target, user_data): #:PyRCX!~PyRC@ZiRC-CAB5A9EC.cg.shawcable.net JOIN :#animesuki.os
		channel_name = unicode(target.replace(':', '').lower())
		channel = server.getChannel(channel_name)
		if not channel: #We're joining the channel, since it isn't in our list.
			server.getStash().createChannel(channel_name)
			server.addChannel(channel_name)
		else: #Someone else is joining the channel
			channel.addUser(user_data['username'], user_data['ident'], user_data['hostmask'])
			server.addEvent(outboundDictionaries.IRC_Channel_User_Join(server.getContextID(), server.getName(), channel_name, channel.getUserData(user_data['username'])))
	rc['JOIN'] = _JOIN
	
	def _KICK(server, data, target, user_data): #:basket!~basket@prepare.for.descent.into.usercom.zirc.org KICK #animesuki.os PyRC :rejoin
		channel_name = unicode(target.lower())
		data = data.split(None, 1)
		
		channel = server.getChannel(channel_name)
		if not channel:
			return
			
		if data[0].lower() == server.getNickname().lower():
			server.addEvent(outboundDictionaries.IRC_Channel_Close(server.getContextID(), server.getName(), channel.getName(), data[1][1:], True, user_data))
			server.removeChannel(channel.getName())
		else:
			target_data = channel.getUserData(data[0])
			server.addEvent(outboundDictionaries.IRC_Channel_User_Part(server.getContextID(), server.getName(), channel.getName(), data[1][1:], target_data, True, user_data))
			channel.removeUser(user_data['username'])
	rc['KICK'] = _KICK
	
	def _KILL(server, data, target, user_data): #:OperServ!services@zirc.org KILL Dead_HamsterX :equilibrium!eclipse!services!OperServ (Session limit exceeded)
		server.addEvent(Server_Kill(server.getContextID(), server.getName(), unicode(target), data, user_data))
		if target.lower() == server.getNickname().lower():
			return (None, False)
	rc['KILL'] = _KILL
	
	def _MODE(server, data, target, user_data):
		channel = server.getChannel(target)
		if not channel:
			return
			
		modes = common.splitModes(data)
		(added_channel_modes, removed_channel_modes, added_user_modes, removed_user_modes) = channel.updateModes(modes)
		
		changestring = ''
		addedstring_post = ''
		removedstring_post = ''
		if added_channel_modes or added_user_modes:
			changestring += '+'
			for i in added_channel_modes + added_user_modes:
				changestring += i[0]
				if i[1]:
					addedstring_post += ' %s' % i[1]
					
		if removed_channel_modes or removed_user_modes:
			changestring += '-'
			for i in removed_channel_modes + removed_user_modes:
				changestring += i[0]
				if i[1]:
					removedstring_post += ' %s' % i[1]
					
		user_mode_changes = {}
		for i in added_user_modes + removed_user_modes:
			user_list = user_mode_changes.get((i[2], i[0]))
			if not user_list:
				user_list = []
				user_mode_changes[(i[2], i[0])] = user_list
			user_list.append(i[1])
			
		for i in user_mode_changes:
			user_mode_changes[i].sort()
			
		if addedstring_post:
			changestring += addedstring_post
			if removedstring_post:
				changestring += ' |%s' % removedstring_post
		elif removedstring_post:
			changestring += removedstring_post
			
		channel_user_data = channel.getUserData(user_data['username'])
		if channel_user_data:
			user_data = channel_user_data
			
		server.addEvent(outboundDictionaries.IRC_Channel_Modes_Update(server.getContextID(), server.getName(), channel.getName(), modes, changestring, user_mode_changes, channel.getModes(), channel.getModeStringFull(), channel.getModeStringSafe(), user_data))
	rc['MODE'] = _MODE
	
	def _NICK(server, data, target, user_data):
		if not user_data:
			return
			
		new_nickname = unicode(target.replace(':', ''))
		server.updateUserNickname(user_data['username'], new_nickname)
		user = server.getUser(new_nickname)
		
		local_change = False
		if server.getNickname().lower() == user_data['username'].lower():
			server.setNickname(new_nickname)
			local_change = True
			
		server.addEvent(outboundDictionaries.IRC_User_Nickname_Change(server.getContextID(), server.getName(), new_nickname, user.getChannels(), user_data, local_change))
	rc['NICK'] = _NICK
	
	def _NOTICE(server, data, target, user_data):
		if data[0] == "\001": #CTCP response.
			data = data.replace("\001", '').split(None, 1)
			ctcp_core.ctcpResponseHandler(data[0], data[1], user_data, server)
		else:
			server.addEvent(outboundDictionaries.IRC_User_Notice(server.getContextID(), server.getName(), data, unicode(target), user_data))
	rc['NOTICE'] = _NOTICE
	
	def _PART(server, data, target, user_data):
		channel = server.getChannel(target)
		if not channel:
			return
			
		if not user_data:
			return
			
		if user_data['username'].lower() == server.getNickname().lower():
			server.addEvent(outboundDictionaries.IRC_Channel_Close(server.getContextID(), server.getName(), channel.getName(), data, False, None))
			server.removeChannel(channel.getName())
		else:
			server.addEvent(outboundDictionaries.IRC_Channel_User_Part(server.getContextID(), server.getName(), channel.getName(), data, user_data, False, None))
			channel.removeUser(user_data['username'])
	rc['PART'] = _PART
	
	def _PRIVMSG(server, data, target, user_data):
		is_action = False
		if data[0] == "\001": #Either an action or a CTCP.
			data = data.replace("\001", '').split(None, 1)
			data[0] = data[0].upper()
			if data[0] == "ACTION":
				is_action = True
				data = data[1]
			else:
				payload = None
				if len(data) > 1:
					payload = data[1]
				ctcp_core.ctcpHandler(data[0], payload, user_data, unicode(target), server)
				return
				
		if target[0] in GLOBAL.IRC_CHANNEL_PREFIX:
			channel = server.getChannel(target)
			if not channel:
				return
				
			channel.passChannelMessage((user_data['username'], user_data['ident'], user_data['hostmask']))
			server.addEvent(outboundDictionaries.IRC_Channel_Message(server.getContextID(), server.getName(), channel.getName(), data, is_action, user_data))
		else:
			server.addEvent(outboundDictionaries.IRC_User_Private_Message(server.getContextID(), server.getName(), data, is_action, user_data))
	rc['PRIVMSG'] = _PRIVMSG
	
	def _QUIT(server, data, target, user_data):
		user = server.getUser(user_data['username'])
		if not user:
			return
			
		message = target
		if data:
			message = "%s %s" % (message, data)
		server.addEvent(outboundDictionaries.IRC_User_Quit(server.getContextID(), server.getName(), unicode(message), user.getChannels(), user_data))
		user.removeUser()
	rc['QUIT'] = _QUIT
	
	def _TOPIC(server, data, target, user_data):
		channel = server.getChannel(target)
		if not channel:
			return
			
		channel.setTopic(data)
		server.addEvent(outboundDictionaries.IRC_Channel_Topic_New(server.getContextID(), server.getName(), channel.getName(), channel.getTopic(), user_data))
	rc['TOPIC'] = _TOPIC
	
	return rc
_response_code_events = _generateResponseCodes() #: A dictionary of functions, keyed by event name.
del _generateResponseCodes

def handleNonColon(server, raw_string):
	"""
	This function parses and processes a non-colon-prefixed event sent by the
	server.
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object that received this event.
	@type raw_string: basestring
	@param raw_string: The raw event string.
	
	@rtype: None|Tuple
	@return: Nothing if everything went well; a tuple containing an optional
	    reason and a bool indicating whether PyRC should suppress reconnection
	    if PyRC needs to disconnect. Leaving the reason empty will result in no
	    disconnection event being generated, so the handler will need to take
	    care of informing the IAL.
	
	@raise ProtocolError: If the string received from the IRC server did not
	    match the spec expected by PyRC.
	"""
	(identifier, data) = raw_string.split(" :", 1)
	
	handler = _non_colon_events.get(identifier)
	if handler:
		try:
			if data:
				data = unicode(data, 'utf-8', 'replace')
			return handler(server, data)
		except Exception, e:
			raise ProtocolError("Error while processing '%s': %s" % (raw_string, e))
	else:
		raw = outboundDictionaries.IRC_Raw_Event(server.getContextID(), server.getName(), raw_string)
		server.addEvent(outboundDictionaries.PyRC_Implement_Me(identifier, raw))
		
def handleServerCode(server, nickname, text, raw_string):
	"""
	This function parses and processes a colon-prefixed event sent by the
	server.
	
	It handles strings that look like::
		:YUO MODE YUO :+ixz
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object that received this event.
	@type nickname: basestring
	@param nickname: The name of the user described by this event.
	@type text: basestring
	@param text: The token used to identify the type of event.
	@type raw_string: basestring
	@param raw_string: The raw event string.
	
	@rtype: None|Tuple
	@return: Nothing if everything went well; a tuple containing an optional
	    reason and a bool indicating whether PyRC should suppress reconnection
	    if PyRC needs to disconnect. Leaving the reason empty will result in no
	    disconnection event being generated, so the handler will need to take
	    care of informing the IAL.
	
	@raise ProtocolError: If the string received from the IRC server did not
	    match the spec expected by PyRC.
	"""
	identifier = text[0]
	text = text[1].split(None, 1)
	
	target = text[0]
	data = None
	if len(text) > 1:
		data = text[1]
		if data:
			if data.startswith(':'):
				data = data[1:]
				
	handler = _server_code_events.get(identifier)
	if handler:
		try:
			if data:
				data = unicode(data, 'utf-8', 'replace')
			return handler(server, data, target, nickname)
		except Exception, e:
			raise ProtocolError("Error while processing '%s': %s" % (raw_string, e))
	else:
		raw = outboundDictionaries.IRC_Raw_Event(server.getContextID(), server.getName(), raw_string)
		server.addEvent(outboundDictionaries.PyRC_Implement_Me(identifier, raw))
		
def handleResponseCode(server, userstring, text, raw_string):
	"""
	This function parses and processes a colon-prefixed event sent by a user.
	
	It handles strings that look like::
		:Etna!~rhx@ZiRC-CAB5A9EC.cg.shawcable.net NOTICE rhx :PING rice
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object that received this event.
	@type userstring: basestring
	@param userstring: The URI of the user that sent this event (a raw user
	    string).
	@type text: list
	@param text: The token used to identify the type of event and the event's
	    data.
	@type raw_string: basestring
	@param raw_string: The raw event string.
	
	@rtype: None|Tuple
	@return: Nothing if everything went well; a tuple containing an optional
	    reason and a bool indicating whether PyRC should suppress reconnection
	    if PyRC needs to disconnect. Leaving the reason empty will result in no
	    disconnection event being generated, so the handler will need to take
	    care of informing the IAL.
	
	@raise ProtocolError: If the string received from the IRC server did not
	    match the spec expected by PyRC.
	"""
	identifier = text[0]
	
	text = text[1].split(None, 1)
	target = text[0]
	
	data = None
	if len(text) > 1:
		data = text[1]
		if data:
			if data.startswith(':'):
				data = data[1:]
				
	user_data = None
	user_data = user_functions.splitUserData(userstring)
	user = server.getUser(user_data[0])
	if not user:
		user_data = user_functions.generateUserData(user_data)
	else:
		user.setIdentity(user_data[1], user_data[2])
		if target[0] in GLOBAL.IRC_CHANNEL_PREFIX:
			user_data = user.getData(target)
		else:
			user_data = user.getData()
			
	handler = _response_code_events.get(identifier)
	if handler:
		try:
			if data:
				data = unicode(data, 'utf-8', 'replace')
			return handler(server, data, target, user_data)
		except Exception, e:
			import pyrc_common.errlog
			print pyrc_common.errlog.grabTrace()
			raise ProtocolError("Error while processing '%s': %s" % (raw_string, e))
	else:
		raw = outboundDictionaries.IRC_Raw_Event(server.getContextID(), server.getName(), raw_string)
		server.addEvent(outboundDictionaries.PyRC_Implement_Me(identifier, raw))
		
		
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
		self.description = unicode(description, 'utf-8', 'replace')
		
class ProcessingError(Error):
	"""
	This class represents the possibility of problems related to mode
	processing.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new ProcessingError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		Error.__init__(self, description)
		
class ProtocolError(Error):
	"""
	This class represents problems that might occur when processing strings
	received from the IRC server.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new ProtocolError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		Error.__init__(self, description)
		
