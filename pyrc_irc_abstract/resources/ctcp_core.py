# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.ctcp_core

Purpose
=======
 Handle all inbound CTCP events.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import time

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.C_FUNCS as C_FUNCS

import pyrc_common.dictionaries.outbound as outboundDictionaries
#The following dictionaries are used by this module:
##IRC CTCP Request
##IRC CTCP Response
##IRC Ping
##IRC Pong

def _quickCTCPReply(server, username, data, priority=GLOBAL.ENUM_SERVER_SEND_PRIORITY.AVERAGE):
	"""
	This function is used to emit a generic CTCP reply event.
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object to which this event will be
	    sent.
	@type username: basestring
	@param username: The username to which this event will be sent.
	@type data: basestring
	@param data: The data that will be sent to the user.
	@type priority: GLOBAL.ENUM_SERVER_SEND_PRIORITY.EnumValue
	@param priority: The priority at which this event will be sent.
	
	@return: Nothing.
	"""
	server.send("NOTICE %s :\001%s\001" % (username, data), priority)
	
#Define built-in responses.
#######################################
def _responseVersion(user_data, server):
	"""
	This function is used to respond to a CTCP VERSION.
	
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object from which this request
	    originated.
	
	@return: Nothing.
	"""
	psyco_status = ""
	if GLOBAL.ENV_PSYCO:
		psyco_status = " (Psyco-enhanced)"
	_quickCTCPReply(server, user_data['username'], "VERSION %s %s running on %s%s" % (GLOBAL.RLS_PyRC_NAME, GLOBAL.RLS_PyRC_VERSION, GLOBAL.ENV_PLATFORM, psyco_status))
	
def _responseFinger(user_data, server):
	"""
	This function is used to respond to a CTCP FINGER.
	
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object from which this request
	    originated.
	
	@return: Nothing.
	"""
	_quickCTCPReply(server, user_data['username'], "FINGER %s has been idle for %s" % (server.getRealName(), _getIdleTime(server)))
	
def _responseTime(user_data, server):
	"""
	This function is used to respond to a CTCP TIME.
	
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object from which this request
	    originated.
	
	@return: Nothing.
	"""
	_quickCTCPReply(server, user_data['username'], "TIME %s" % time.asctime())
	
def _responseUserInfo(user_data, server):
	"""
	This function is used to respond to a CTCP USERINFO.
	
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object from which this request
	    originated.
	
	@return: Nothing.
	"""
	_quickCTCPReply(server, user_data['username'], "USERINFO %s" % GLOBAL.USR_VARIABLES['userinfo'])
	
def _responseSource(user_data, server):
	"""
	This function is used to respond to a CTCP SOURCE.
	
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object from which this request
	    originated.
	
	@return: Nothing.
	"""
	_quickCTCPReply(server, user_data['username'], "SOURCE %s" % GLOBAL.RLS_PyRC_URL)
	
def _responseClientInfo(user_data, server):
	"""
	This function is used to respond to a CTCP CLIENTINFO.
	
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object from which this request
	    originated.
	
	@return: Nothing.
	"""
	handlers = _built_in_responses.keys()
	for i in _ctcp_responses:
		handler = i['request']
		if not handler in handlers:
			handlers.append(handler)
	handlers.append("PING")
	handlers.sort()
	_quickCTCPReply(server, user_data['username'], "CLIENTINFO %s" % ' '.join(handlers))
	
_built_in_responses = {
 "VERSION": _responseVersion,
 "SOURCE": _responseSource,
 "FINGER": _responseFinger,
 "TIME": _responseTime,
 "USERINFO": _responseUserInfo,
 "CLIENTINFO": _responseClientInfo
}#: A dictionary containing built-in response-handling functions, keyed by CTCP event.
del _responseVersion
del _responseSource
del _responseFinger
del _responseTime
del _responseUserInfo
del _responseClientInfo

#Define custom responses.
#######################################
_ctcp_responses = []
"""
This is a list of user-defined CTCP request/response pairs.

It has the following form::
 [
  {
   'request': <:unicode>,
   'response': <:unicode>,
   'final': <:bool> #If True, this will be the last evaluation that sees the request. 
  }
 ]
"""

def getResponses():
	"""
	This function returns a list of all user-defined CTCP responses.
	
	Its primary use will likely be in saving modifications made at runtime.
	
	@rtype: list
	@return: A list of all user-defined CTCP responses.
	    This list contains elements of the following form::
	     {
	      'request': <:unicode>,
	      'response': <:unicode>,
	      'final': <:bool>
	     }
	"""
	return _ctcp_responses
	
def addResponse(request, response, final):
	"""
	This function adds a new response to the list of user-defined CTCP
	responses.
	
	@type request: basestring
	@param request: The CTCP event on which the response should be returned.
	@type response: basestring
	@param response: The response that will be returned if the request is
	    matched.
	@type final: bool
	@param final: If True, this will be the last evaluation through which the
	    request will pass. That is, no plugins will be able to see the event.
	
	@return: Nothing.
	"""
	global _ctcp_responses
	_ctcp_responses.append({
	 'request': unicode(request.upper()),
	 'response': unicode(response),
	 'final': final
	})
	
def delResponse(request, response, final):
	"""
	This function deletes a response from the list of user-defined CTCP
	responses after matching all three parameters that define the event.
	
	@type request: basestring
	@param request: The CTCP event on which the response should be returned.
	@type response: basestring
	@param response: The response that will be returned if the request is
	    matched.
	@type final: bool
	@param final: If True, this will be the last evaluation through which the
	    request will pass. That is, no plugins will be able to see the event.
	
	@return: Nothing.
	"""
	global _ctcp_responses
	for i in _ctcp_responses:
		if i['request'] == request and i['response'] == response and i['final'] == final:
			_ctcp_responses.remove(i)
			return
			
def ctcpHandler(ctcp_type, ctcp_string, user_data, target, server):
	"""
	This function is called when CTCP request data is received from another
	client.
	
	PING/PONG requests are internally handled; DCC events are forwarded to
	pyrc_irc_abstract.dcc.dcc_core.
	
	All other requests are matched against user-defined CTCP events or sent to
	the plugin chain as instances of "CTCP Event" dictionaries.
	
	@type ctcp_type: basestring
	@param ctcp_type: A string identifying the type of CTCP request received.
	@type ctcp_string: basestring|None
	@param ctcp_string: A string containing any additional data sent with the
	    CTCP request.
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who made the request.
	@type target: basestring
	@param target: The target of this CTCP event. (Either PyRC's current name
	    the name of a channel.)
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the server object that received this request.
	
	@return: Nothing.
	"""
	if ctcp_type == "PING":
		_quickCTCPReply(server, user_data['username'], "PING %s" % ctcp_string, GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
		server.addEvent(outboundDictionaries.IRC_Ping(server.getContextID(), server.getName(), unicode(ctcp_string), unicode(user_data['username'])))
	else:
		#Needs DCC.	#Check to see whether this is DCC-related.
		
		handled = False
		continue_processing = True
		
		for i in _ctcp_responses:
			if ctcp_type == i['request']:
				_quickCTCPReply(server, user_data['username'], "%s %s" % (ctcp_type, _processCTCPString(i['response'], user_data['username'], server)))
				handled = True
				if i['final']: #The user-defined response suppresses further processing.
					continue_processing = False
					break
					
		if continue_processing: #Apply standard processing.
			handler = _built_in_responses.get(ctcp_type)
			if handler:
				handler(user_data, server)
				handled = True
				
		server.addEvent(outboundDictionaries.IRC_CTCP_Request(server.getContextID(), server.getName(), user_data, unicode(target.lower()), ctcp_type, ctcp_string, handled))
		
def ctcpResponseHandler(ctcp_type, ctcp_string, user_data, server):
	"""
	This function is called when CTCP response data is received from another
	client.
	
	PING/PONG responses are internally handled; DCC events are forwarded to
	pyrc_irc_abstract.dcc.dcc_core.
	
	All other responses are sent to the plugin chain as instances of
	"CTCP Reply" dictionaries.
	
	@type ctcp_type: basestring
	@param ctcp_type: A string identifying the type of CTCP response received.
	@type ctcp_string: basestring
	@param ctcp_string: A string containing any additional data sent with the
	    CTCP response.
	@type user_data: dict
	@param user_data: A User Data Information Dictionary representing the user
	    who provided the response.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the server object that received this response.
	
	@return: Nothing.
	"""
	if ctcp_type == "PING": #A PING reply from another user.
		delay = server.processPong(user_data['username'])
		if delay: #None is returned if the user wasn't previously PINGed.
			server.addEvent(outboundDictionaries.IRC_Pong(server.getContextID(), server.getName(), delay, user_data))
	else:
		#Needs DCC.
		#Check to see whether this is DCC-related.
		server.addEvent(outboundDictionaries.IRC_CTCP_Response(server.getContextID(), server.getName(), user_data, unicode(ctcp_type), unicode(ctcp_string)))
		
def _processCTCPString(data, user, server):
	"""
	This function replaces %-prefixed substrings by the following table::
	 %% -> %
	 %n -> current nick
	 %c -> user sending the CTCP request
	 %p -> local IP
	 %i -> time spent idle
	 %r -> realname
	 %u -> username
	 %d -> current day
	 %t -> current month
	 %y -> current year
	 %h -> current hour
	 %m -> current minute
	 %s -> current second
	
	@type data: basestring
	@param data: The CTCP response string to be processed.
	@type user: basestring
	@param user: The nickname of the user who requested this response.
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: The pyrc_irc_abstract.irc_server.Server object that received the
	    request for which this response is being prepared.
	
	@rtype: basestring
	@return: The processed CTCP response.
	"""
	current_time = time.localtime()
	data = data.replace("%%", "\x00")
	data = data.replace("%c", user)
	data = data.replace("%d", str(current_time[2]))
	data = data.replace("%t", str(current_time[1]))
	data = data.replace("%y", str(current_time[0]))
	data = data.replace("%h", str(current_time[3]))
	data = data.replace("%d", C_FUNCS.padInteger(current_time[4], 2))
	data = data.replace("%s", C_FUNCS.padInteger(current_time[5], 2))
	data = data.replace("%i", _getIdleTime(server))
	data = data.replace("%r", server.getRealName())
	data = data.replace("%u", server.getIdent())
	data = data.replace("%p", server.getLocalIP())
	data = data.replace("%n", server.getNickname())
	return data.replace("\x00", "%")
	
def _getIdleTime(server):
	"""
	This function calculates the total time spent idle on a server.
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: The pyrc_irc_abstract.irc_server.Server object for which idle time
	    is being calculated.
	
	@rtype: unicode
	@return: A string in the form '[[x hour(s), ][x minute(s), ]and ]x second(s)'
	"""
	idle_time = server.getIdleTime()
	hours = int(idle_time / 3600)
	idle_time = idle_time % 3600
	minutes = int(idle_time / 60)
	idle_time = idle_time % 60
	seconds = int(round(idle_time, 1))
	
	timestamp = ""
	if hours:
		timestamp = "%i %s, " % (hours, C_FUNCS.pluralizeQuantity(hours, 'hour'))
		
	if minutes:
		timestamp = "%s %i %s, " % (timestamp, minutes, C_FUNCS.pluralizeQuantity(minutes, 'minute'))
		
	if timestamp:
		timestamp = "%s and " % timestamp
		
	return u"%s %i %s" % (timestamp, seconds, C_FUNCS.pluralizeQuantity(seconds, 'second'))
	