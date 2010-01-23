# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_control.raw_ui

Purpose
=======
 Provide a raw, primitive interface for debugging and development.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
__module_data__={
 'name': "Raw UI",
 'version': "0.8.1",
 #Optional
 'author': "Neil Tallim",
 'e-mail': "red.hamsterx@gmail.com",
 #Non-core
 'last_good_commit': 'r282'
} #: A collection of data used to identify this plugin to other plugins.

import threading
import time
import re

import pyrc_shared.interpreter as interpreter
import pyrc_common.GLOBAL as GLOBAL

_TOKENS = {
 'input': '>>',
 'output': '<<',
 'event': '::',
 'currentcontext': ']:[',
 'context': '[:]'
} #: A dictionary of tokens used to mark events.

_HELP_TEXT = (
 "RawUI Help Text",
 "",
 "When connecting to an IRC server, the connection will be given a cID value.",
 "",
 "When joining a channel or setting a query, the new context will be given a tID",
 "value.",
 "",
 "To change the active connection, type '#\\', where '#' is the cID.",
 "To change the active context, type '#:', where # is the tID.",
 "To change both at once, type '#\\#:'.",
 "",
 "Context information will be printed in the format",
 "'%s 1\\1: = synIRC:#animesuki.os (2\\ = ETG)' every time it changes." % _TOKENS['currentcontext'],
 "The value in parentheses represents the active connection, and it will only",
 "appear if the active connection differs from the active context.",
 "",
 "Once a context has been set, using ':' as a prefix will address it, regardless",
 "of the active connection.",
 "",
 "Using no prefix will cause your string to be sent directly along the active",
 "connection.",
 "Using '/' as a prefix will initiate string processing, using either",
 "built-in routines or the interpreter; the active context will be the focus",
 "for events.",
 "",
 "Type ':' by itself to view the current context and a list of all available",
 "contexts. Specify a context and provide a string to send it there without",
 "changing the current context.",
 "",
 "In addition to the standard interpreter commands, the following are built into",
 "this interface:"
 " /query <target> : defines a context for the target",
)#: The text to display if '/help' is typed.

_PREFIX_PARSER = re.compile(r"(?:(\d+)\\)?(?:(\d+):)?(.*)") #: A regular expression used to parse raw user input.

_connections_lock = threading.Lock()
_connections = {}
"""
A dictionary of connections, keyed by connection ID.

Its elements have the following form::
 {<connection_id:int>: (
   <server_name:unicode>,
   {<target_id:int>: <target_channel_or_user:unicode>}
 )}
"""

_active_target = (0, 0) #: The interface's active target as a (connection, target) tuple.
_active_connection = 0 #: The interface's active connection.

_ial = None #: A reference to pyrc_irc_abstract.irc_interface.processDictionary(), the IRC Abstraction Layer's interface.

_user_watcher = None #: A thread used to watch for and react to user input, this interface's mainloop.

def _generateEvents():
	"""
	This function is used to generate a dictionary containing functions that
	handle incoming Event Dictionaries.
	
	Each function in this dictionary has the following inputs::
	 (<event_dictionary:dict>,
	  <pyrc_irc_abstract.irc_interface.processDictionary:function>)
	
	They return nothing.
	
	@rtype: dict
	@return: A dictionary of Event Dictionary-handling functions, keyed by
	    eventname.
	"""
	events = {}
	
	def _discard(dictionary, ial):
		pass
	events['Channel Banlist'] = _discard
	events['Channel Message'] = _discard
	events['Channel Message Local'] = _discard
	events['Channel Modes Update'] = _discard
	events['Channel User Join'] = _discard
	events['CTCP Request'] = _discard
	events['Initialised'] = _discard
	events['Ping'] = _discard
	events['Ping Timeout Check'] = _discard
	events['Ping Timeout'] = _discard
	events['Pong'] = _discard
	events['Private Message'] = _discard
	events['Private Message Local'] = _discard
	events['Server Message'] = _discard
	events['Server MOTD'] = _discard
	events['Time Signal'] = _discard
	events['User Modes'] = _discard
	events['User Notice'] = _discard
	events['User Quit'] = _discard
	events['WhoIs Response'] = _discard
	
	def _IRC_Channel_Close(dictionary, ial):
		print dictionary
		try:
			_connections_lock.acquire()
			for i, name in _connections[dictionary['irccontext']][1].iteritems():
				if name == dictionary['channel']:
					reason = dictionary['message']
					if not reason:
						reason = "<no reason provided>"
						
					if dictionary['kick']:
						reason = "kicked by %s: %s" % (dictionary['kicker']['username'], reason)
						
					print "%s %i\\%i: = %s:%s has been removed: %s" % (_TOKENS['event'], dictionary['irccontext'], i, _connections[dictionary['irccontext']][0], dictionary['channel'], reason)
					
					if  _deleteContext(dictionary['irccontext'], i): #This was the active target.
						_printContexts()
						_printContext()
						
					break
		finally:
			_connections_lock.release()
	events['Channel Close'] = _IRC_Channel_Close
	
	def _IRC_Channel_Join(dictionary, ial):
		try:
			_connections_lock.acquire()
			c_id = _findFreeContext(dictionary['irccontext'])
			
			_connections[dictionary['irccontext']][1][c_id] = dictionary['channeldata']['channel']
			print "%s %s has been assigned tID '%i' (%i\\%i:)" % (_TOKENS['event'], dictionary['channeldata']['channel'], c_id, dictionary['irccontext'], c_id)
			
			#If the user hasn't set an active target, set this channel.
			global _active_target
			if not _active_target[1]:
				_active_target = (dictionary['irccontext'], c_id)
				_printContext()
		finally:
			_connections_lock.release()
	events['Channel Join'] = _IRC_Channel_Join
	
	def _IRC_Raw_Command(dictionary, ial):
		print "%i%s %s" % (dictionary['irccontext'], _TOKENS['output'], dictionary['data'])
	events['Raw Command'] = _IRC_Raw_Command
	
	def _IRC_Raw_Event(dictionary, ial):
		print "%i%s %s" % (dictionary['irccontext'], _TOKENS['input'], dictionary['data'])
	events['Raw Event'] = _IRC_Raw_Event
	
	def _PyRC_Status(dictionary, ial):
		print dictionary['message']
	events['PyRC Status'] = _PyRC_Status
	
	def _Server_Connection_Success(dictionary, ial):
		try:
			_connections_lock.acquire()
			_connections[dictionary['irccontext']] = (dictionary['networkname'], {})
			
			print "%s %i\\ = %s has been added." % (_TOKENS['event'], dictionary['irccontext'], dictionary['networkname'])
			
			global _active_connection
			if not _active_connection:
				_active_connection = dictionary['irccontext']
				
			global _active_target
			if not _active_target[0]:
				_active_target = (dictionary['irccontext'], 0)
				_printContext()
		finally:
			_connections_lock.release()
	events['Server Connection Success'] = _Server_Connection_Success
	
	def _Server_Disconnection(dictionary, ial):
		try:
			_connections_lock.acquire()
			if dictionary['irccontext'] in _connections:
				print "%s %i\\ = %s has been removed: %s" % (_TOKENS['event'], dictionary['irccontext'], _connections[dictionary['irccontext']][0], dictionary['message'])
				
				if  _deleteConnection(dictionary['irccontext']): #This was the passive connection.
					_printContexts()
					_printContext()
		finally:
			_connections_lock.release()
	events['Server Disconnection'] = _Server_Disconnection
	events['Server Kill'] = _Server_Disconnection
	
	def _Server_Welcome(dictionary, ial):
		try:
			_connections_lock.acquire()
			#Update the connection's name if necessary.
			old_name = _connections[dictionary['irccontext']][0]
			if not old_name == dictionary['networkname']:
				print "%s %i:%s is now known as '%s'" % (_TOKENS['event'], dictionary['irccontext'], old_name, dictionary['networkname'])
				_connections[dictionary['irccontext']] = (dictionary['networkname'], _connections[dictionary['irccontext']][1])
		finally:
			_connections_lock.release()
	events['Server Welcome'] = _Server_Welcome
	
	return events
_events = _generateEvents()
del _generateEvents
	
def hookEvent(dictionary, ial):
	"""
	This is a function defined in PyRC's UI specs. It is called by the IAL when
	an Event Dictionary is to be passed to the UI.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to be processed.
	@type ial: function
	@param ial: A reference to
		pyrc_irc_abstract.irc_interface.processDictionary(), the IAL's
		interface.
	
	@return: Nothing.
	"""
	handler = _events.get(dictionary['eventname'])
	if handler:
		handler(dictionary, ial)
	else:
		print dictionary
		
def loadMe(ial):
	"""
	This is a function defined in PyRC's plugin specs. It is called by the IAL
	when this plugin is loaded or enabled.
	
	@type ial: function
	@param ial: A reference to
		pyrc_irc_abstract.irc_interface.processDictionary(), the IAL's
		interface.
	
	@rtype: tuple
	@return: A triple of the following format::
	     (processes_raw_commands:bool, processes_raw_events:bool,
		  function_to_run_with_main_thread:function|None)
	"""
	global _ial
	_ial = ial
	interpreter.initialise(ial)
	
	#Start watching for user input.
	global _user_watcher
	_user_watcher = _UserWatcher()
	_user_watcher.setName("RawUI - UserWatcher")
	_user_watcher.start()
	
	return (True, True, None)
	
def unloadMe(ial):
	"""
	This is a function defined in PyRC's plugin specs. It is called by the IAL
	when this plugin is unloaded or disabled.
	
	@type ial: function
	@param ial: A reference to
		pyrc_irc_abstract.irc_interface.processDictionary(), the IAL's
		interface.
	
	@return: Nothing.
	"""
	pass
	
def _findFreeContext(connection_id):
	"""
	This function is used to find the next available context ID for use with a
	connection.
	
	This value will always be one higher than the highest defined context. While
	it would be possible to scan for the lowest free index, that would likely
	confuse users.
	
	@type connection_id: int
	@param connection_id: The ID of the connection to check.
	
	@rtype: int
	@return: The context ID that should be used.
	"""
	sequence = _connections[connection_id][1].keys()
	if sequence:
		return max(sequence) + 1
	return 1
	
def _changeContext(connection_id, context_id):
	"""
	This function is used to change the interface's active context.
	
	This function will change the active connection in addition to changing the
	active target. If no target is specified, only the active connection will be
	updated.
	
	@type connection_id: int
	@param connection_id: The ID of the connection to set as active.
	@type context_id: int
	@param context_id: The ID of the context to set as active.
	
	@rtype: bool
	@return: True if the operation succeeded; False if invalid parameters were
	    given.
	"""
	global _active_target
	global _active_connection
	
	connection = _connections.get(connection_id)
	if connection:
		if context_id:
			print context_id
			if context_id in connection[1]:
				_active_target = (connection_id, context_id)
			else:
				return False
		_active_connection = connection_id
		return True
	return False
	
def _parseContext(input_string):
	"""
	This function is used to parse the user's input to extract context-related
	information.
	
	@type input_string: basestring
	@param input_string: A string to be parsed.
	
	@rtype: tuple
	@return: A tuple of the following form::
	     (<connection:int>, <context:int>, <remaining_text:basestring>)
	"""
	match = _PREFIX_PARSER.match(input_string)
	connection = match.group(1)
	if connection:
		connection = int(connection)
	else:
		connection = 0
	context = match.group(2)
	if context:
		context = int(context)
	else:
		context = 0
		
	return (connection, context, match.group(3))
	
def _deleteContext(connection_id, context_id):
	"""
	This function is used to remove a context from the list of available
	contexts.
	
	If the specified context is the active context, the active context will be
	flushed.
	
	@type connection_id: int
	@param connection_id: The ID of the connection from which the context is to
	    be removed.
	@type context_id: int
	@param context_id: The ID of the context that is to be removed.
	
	@rtype: bool
	@return: True if the context changed upon removal.
	"""
	del _connections[connection_id][1][context_id]
	
	global _active_target
	if _active_target == (connection_id, context_id):
		_active_target = (connection_id, 0)
		
		return True
	return False
	
def _deleteConnection(connection_id):
	"""
	This function is used to remove a connection from the list of available
	connections.
	
	If the specified connection is host to the active target or the active
	connection, those variables will be flushed.
	
	@type connection_id: int
	@param connection_id: The ID of the connection to be removed.
	
	@rtype: bool
	@return: True if the context changed upon removal.
	"""
	del _connections[connection_id]
	
	deleted_active = False
	
	global _active_target
	if _active_target[0] == connection_id:
		_active_target = (0, 0)
		deleted_active = True
		
	global _active_connection
	if _active_connection == connection_id:
		_active_connection = 0
		
	return deleted_active
	
def _printContexts():
	"""
	This function is used to display a list of all available contexts.
	
	@return: Nothing.
	"""
	print "Available contexts:"
	
	if not _connections:
		print "%s None" % _TOKENS['context']
		return
		
	for i in sorted(_connections.keys()):
		connection = _connections[i]
		print "\t%s %i\\ = %s" % (_TOKENS['context'], i, connection[0])
		
		for j in sorted(connection[1].keys()):
			print "\t\t%s %i\\%i: = %s:%s" % (_TOKENS['context'], i, j, connection[0], connection[1][j])
			
def _printContext():
	"""
	This function is used to display the current context.
	
	@return: Nothing.
	"""
	if not _active_target[0]:
		print "%s No active connection." % _TOKENS['context']
		return
		
	active_connection = ''
	if not _active_target[0] == _active_connection:
		active_connection = " (%i\\ = %s)" % (_active_connection, _connections[_active_connection][0])
		
	active_target = ''
	active_context = ''
	if _active_target[1]:
		active_target = "%i:" % _active_target[1]
		active_context = ":%s" % _connections[_active_target[0]][1][_active_target[1]]
		
	print "%s %i\\%s = %s%s%s is the current context" % (_TOKENS['currentcontext'], _active_target[0], active_target, _connections[_active_target[0]][0], active_context, active_connection)
	print "%s You are %s" % (_TOKENS['currentcontext'], _ial({'eventname': "Get Current Nickname", 'irccontext': _active_target[0]})['username'])
	
	
class _UserWatcher(threading.Thread):
	"""
	This class is used to watch for and process user input.
	"""
	def run(self):
		"""
		This function forms the mainloop of RawUI. It runs until the user tells
		it to stop, which in turn kills PyRC.
		
		During each cycle, it blocks until the user enters a command, then
		determines how the command should be processed -- whether it needs to be
		interpreted or parsed.
		
		It then executes the command within PyRC's IAL framework.
		
		@return: Nothing.
		"""
		global _active_connection
		
		time.sleep(0.5) #Don't interrupt the startup status prints.
		
		pyrc_data = _ial({'eventname': "Get Version"})
		print
		print "Now using %s v%s on %s v%s." % (__module_data__['name'], __module_data__['version'], pyrc_data['name'], pyrc_data['version'])
		print "To begin, type '/server irc.synirc.net'"
		print
		print "You can find out more about %s at the following locations:" % pyrc_data['name']
		print " HTTP: %s" % pyrc_data['url']
		print " IRC: %s" % pyrc_data['irc']
		print
		print "Type '/help' for information about how to use RawUI."
		print
		print "This is alpha software, so bugs are to be expected; consider reverting to"
		print "the %s SVN commit of rawUI.py if this interface is misbehaving." % __module_data__['last_good_commit']
		print
		del pyrc_data
		
		while True:
			try:
				user_input = raw_input()
			except (KeyboardInterrupt, EOFError):
				continue
				
			if not user_input:
				continue
				
			if user_input[0] == '/':
				if _active_target[0]:
					_ial({
					 'eventname': "Server Action",
					 'irccontext': _active_target[0]
					})
					
				#Check built-in patterns.
				split_input = user_input[1:].split(None, 1)
				if not split_input: #Empty string.
					continue
					
				split_input[0] = split_input[0].lower()
				if split_input[0] == "query":
					if not _active_connection:
						print "%s No server set." % _TOKENS['event']
						continue
						
					for i in split_input[1].split():
						_connections_lock.acquire()
						connection = _connections.get(_active_connection)
						if not connection:
							print "%s The active connection no longer exists." % _TOKENS['event']
							_connections_lock.release()
							continue
							
						c_id = _findFreeContext(_active_connection)
						connection[1][c_id] = i
						print "%s %s has been assigned tID %i." % (_TOKENS['event'], i, c_id)
						
						
						if not _active_target[1]:
							if _changeContext(_active_connection, c_id):
								_printContext()
						_connections_lock.release()
					continue
				elif split_input[0] == "help":
					for i in _HELP_TEXT:
						print i
					continue
					
				
				#Interpret.
				focus = None
				if _active_target[1]:
					##TODO: Find out why this keyerrors on 1.
					focus = _connections[_active_target[0]][1][_active_target[1]]
					
				irc_context = _active_target[0]
				if not _active_target[1]:
					irc_context = _active_connection
					
				(code, description, translation) = interpreter.interpret(user_input[1:], irc_context, focus)
				
				if code == interpreter.ENUM_EXECUTION_CODES.SUCCESS:
					if translation['eventname'] == "PyRC Quit":
						_ial(translation)
						break
					else:
						_ial(translation)
				elif code == interpreter.ENUM_EXECUTION_CODES.SUCCESS_REQRESP:
					print _ial(translation)
				elif code == interpreter.ENUM_EXECUTION_CODES.SYNTAX_ERROR:
					print description[0]
					for i in description[1:]:
						print "\t%s" % i
				elif code == interpreter.ENUM_EXECUTION_CODES.UNKNOWN and _active_target[0]:
					_ial({
					 'eventname': "Emit Generic",
					 'irccontext': _active_target[0],
					 'target': focus,
					 'message': user_input[1:]
					})
			else:
				_connections_lock.acquire()
				(connection, context, text) = _parseContext(user_input)
				if not text: #Change target.
					if context:
						if not connection:
							connection = _active_connection
							
						if _changeContext(connection, context):
							_printContext()
						else:
							print "%s Invalid context." % _TOKENS['event']
							_printContexts()
					elif connection:
						if connection in _connections:
							_active_connection = connection
							_printContext()
						else:
							print "%s Invalid context." % _TOKENS['event']
							_printContexts()
				elif text == ":": #Print contexts.
					_printContexts()
					_printContext()
				else:
					if text[0] == ":": #Send to current context.
						text = text[1:]
						connection = _active_target[0]
						context = _active_target[1]
					else:
						if not connection:
							connection = _active_connection
							
					connection_object = _connections.get(connection)
					if connection_object:
						_ial({
						 'eventname': "Server Action",
						 'irccontext': connection
						})
						
						if context:
							context = connection_object[1].get(context)
							if context:
								event_name = "Channel Message"
								target_key = 'channel'
								if not context[0] in GLOBAL.IRC_CHANNEL_PREFIX:
									event_name = "Private Message"
									target_key = 'username'
									
								_ial({
								 'eventname': "Emit Known",
								 'eventdict': {
								  'eventname': event_name,
								  'irccontext': connection,
								  target_key: context,
								  'message': text,
								  'action': False,
								  'send': True
								 }
								})
							else:
								print "%s Invalid context." % _TOKENS['event']
						else:
							_ial({
							 'eventname': "Emit Known",
							 'eventdict': {
							  'eventname': "Raw Command",
							  'irccontext': connection,
							  'data': text
							 }
							})
					else:
						print "%s Invalid connection." % _TOKENS['event']
				_connections_lock.release()
				
