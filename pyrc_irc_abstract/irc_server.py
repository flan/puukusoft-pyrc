# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.irc_server

Purpose
=======
 Establish and maintain a connection to an IRC server, generating events as
 they occur, and sending data as required.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import re
import threading
import time
import random
import Queue
import socket

import irc_user
import irc_channel

import resources.connection
import resources.irc_events
import resources.numeric_events

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.G_OBJECTS as G_OBJECTS
import pyrc_common.C_FUNCS as C_FUNCS

import pyrc_common.dictionaries.information as informationDictionaries
#The following dictionaries are used by this module:
##Server Data

import pyrc_common.dictionaries.outbound as outboundDictionaries
#The following dictionaries are used by this module:
##IRC Ping Timeout
##IRC Ping Timeout Check
##IRC Raw Command
##IRC Raw Event
##Server Channel Close
##Server Connection Error
##Server Connection Success
##Server Disconnection
##Server Protocol Error
##Server Reconnection Success

class Server(object):
	"""
	This class serves as an interface to PyRC's communication with, and
	representation of, an IRC server in an IRC network.
	
	This class provides a means of sendign and receiving information from the
	IRC server, and it quietly gathers data to effectively model the status of
	relevant parts of the network at all times.
	"""
	_context_id = None #: The unique ID number assigned to this Server upon its creation.
	
	_channel_manager = None #: The pyrc_irc_abstract.irc_channel.ChannelManager object used to manage all channels PyRC is in.
	_user_manager = None #: The pyrc_irc_abstract.irc_user.UserManagerServer object used to manage all users PyRC knows about.
	
	_connection = None #: The _Connection object used to actually communicate with the IRC server.
	
	_last_action = None #: A UNIX timestamp representing the last time at which the user acted.
	
	_current_nickname = None #: The nickname PyRC is currently using on the IRC network.
	_nickname_lock = None #: A lock used to prevent multiple simultaneous accesses to PyRC's current nickname.
	
	_user_modes = None #: A list containing all modes currently assigned to PyRC by the IRC server.
	_mode_lock = None #: A lock used to prevent multiple simultaneous accesses to the mode list.
	
	_network_name = None #: The name of the IRC network to which this Server is attached.
	_network_group_name = None #: The user-specified name of this network's group; this will be used for consistency if available.
	_connection_data = None #: The _ConnectionData object used to retain the information used to connect to the IRC network for future reconnect() calls.
	_event_queue = None #: A queue of events that will be passed to PyRC's plugins via the worker threads.
	
	_stash = None #: The _Stash object used to collect pieces of data used to build a complete dictionary.
	
	_worker_threads = None #: A tuple of worker threads used to send events from the IRC network to PyRC's plugins.
	
	_local_ip = None #The IP address of the system running PyRC, as seen by the IRC server.
	
	def __init__(self, id_number, network_group_name, thread_count):
		"""
		This function is invoked when a new Server object is created.
		
		@type id_number: int
		@param id_number: The unique ID number assigned to this Server object.
		@type network_group_name: basestring|None
		@param network_group_name: The user-specified name of the network group,
		    used to provide consistency to plugins if network name resolution
		    fails. Do not set when the user specifies an unknown address.
		@type thread_count: int
		@param thread_count: The number of worker threads to spawn for use by
		    this Server object.
		
		@return: Nothing.
		"""
		self._context_id = id_number
		if network_group_name:
			self._network_group_name = unicode(network_group_name)
		self._channel_manager = irc_channel.ChannelManager(self)
		self._user_manager = irc_user.UserManagerServer()
		self._stash = _Stash(self)
		self._nickname_lock = threading.Lock()
		self._user_modes = []
		self._mode_lock = threading.Lock()
		self._event_queue = Queue.Queue(0)
		
		self.resetIdleTime()
		
		worker_threads = []
		for i in range(thread_count):
			worker_thread = G_OBJECTS.WorkerThread(self._event_queue, "Context ID: %i" % id_number)
			worker_threads.append(worker_thread)
			worker_thread.start()
		self._worker_threads = tuple(worker_threads)
		
	def connect(self, nicknames, ident, real_name, addresses, password, channels):
		"""
		This function accepts and stores information required to establish a
		connection to an IRC network, then attempts to connect to an IRC
		server.
		
		@type nicknames: list
		@param nicknames: A list of nicknames to try, in order, in an attempt
		    to establish a connection to the IRC network.
		@type ident: basestring
		@param ident: The ident string to present to the IRC network.
		@type real_name: basestring
		@param real_name: The real name string to present to the IRC network.
		@type addresses: tuple
		@param addresses: A list of address data to cycle through in an attempt
		    to connect to the IRC network.
		@type password: basestring|None
		@param password: The password required to connect to the IRC server, if
		    any.
		@type channels: list
		@param channels: A list of channel "name[:password]" strings that may
		    be used to automatically join channels upon a successful
		    connection.
		
		@return: Nothing.
		
		@raise InstantiationError: If ident, real_name, nicknames, or addresses
		    are incomplete.
		"""
		self._connection_data = _ConnectionData(nicknames, (ident, real_name), addresses, password)
		for i in channels:
			channel_data = i.split(":", 1)
			if len(channel_data) > 1:
				self._channel_manager.addChannel(channel_data[0], channel_data[1])
			else:
				self._channel_manager.addChannel(channel_data[0])
		self._connect(False)
		
	def _connect(self, reconnection):
		"""
		This function handles the actual process of connecting to a server; it
		should only be called internally, first through connect(), and then by
		reconnect() all subsequent times.
		
		On an error, this function's thread will be used to broadcast details to the rest
		of PyRC before dying.
		
		@type reconnection: bool
		@param reconnection: True if this is an attempt at reconnecting to an
		    IRC server; False if this is the first connection attempt.
		
		@return: Nothing.
		"""
		class ConnectionHandler(threading.Thread):
			_server = None
			
			def __init__(self, server):
				threading.Thread.__init__(self)
				self.setDaemon(False)
				self.setName("ConnectionHandler, context ID: %i" % server._context_id)
				self._server = server
				
			def run(self):
				connection_data = self._server.getConnectionData()
				(ident, real_name) = connection_data.getProfile()
				nickname = self._server.getNickname()
				if not nickname: #If the Server has not previously connected.
					nickname = connection_data.getNickname()
					
				if nickname:
					reason = None
					while True:
						address = connection_data.getAddress()
						if not address:
							break
							
						try:
							self._server.getStash().flush()
							self._server._connection = _Connection(self._server, address[0], address[1], nickname, real_name, ident, connection_data.getPassword(), address[2])
							self._server.setName(address[0])
							if reconnection:
								self._server.addEvent(outboundDictionaries.Server_Reconnection_Success(self._server.getContextID(), self._server.getName(), address[0], address[1], nickname, ident, real_name, connection_data.getPassword(), address[2]))
							else:
								self._server.addEvent(outboundDictionaries.Server_Connection_Success(self._server.getContextID(), self._server.getName(), address[0], address[1], nickname, ident, real_name, connection_data.getPassword(), address[2]))
							reason = None
							break
						except resources.connection.ConnectionError, e:
							reason = e.description
					if reason:
						self._server.addEvent(outboundDictionaries.Server_Connection_Error(self._server.getContextID(), self._server.getName(), u"Unable to connect to any given server address. Most recent error: %s" % reason))
				else:
					self._server.addEvent(outboundDictionaries.Server_Connection_Error(self._server.getContextID(), self._server.getName(), u"Unable to select a nickname to use for authentication."))
		ConnectionHandler(self).start()
		
	def reconnect(self):
		"""
		This function attempts to reconnect to an IRC network, using the data
		stored when connect() was previously called.
		
		@return: Nothing.
		
		@raise ReconnectionError: If the Server is still connected or if
		    connect() was not previously called.
		"""
		if self.isConnected():
			raise ReconnectionError(u"There is already an active connection.")
		if not self._connection_data:
			raise ReconnectionError(u"No prior connection has been attempted.")
		self._connect(True)
		
	def disconnect(self):
		"""
		This function closes this Server's link to the IRC server, taking care
		of any necessary cleanup tasks.
		
		@return: Nothing.
		"""
		self._closeConnection()
		
	def close(self):
		"""
		This function cleans up the Server in preparation for its removal.
		
		Any links to other parts of PyRC will be severed.
		
		@return: Nothing.
		"""	
		for i in self._channel_manager.emptyPool():
			self.addEvent(outboundDictionaries.IRC_Channel_Close(self.getContextID(), self.getName(), i, "Closing connection", False, None))
		self.disconnect()
		
		for i in self._worker_threads:
			i.kill()
			
	def _closeConnection(self):
		"""
		This function handles the internal calls used to actually disconnect
		from the IRC server.
		
		This function should not be called from outside of the object.
		
		@return: Nothing.
		"""
		if self._connection:
			self._connection.close()
			
	def processInput(self, raw_string):
		"""
		This function processes the raw input provided by the IRC server.
		
		It works by splitting the input into lines based on linebreak
		characters. If the last line is missing such a character, it is
		considered a fragment and stored in the Server's _Stash to be used when
		processing the next packet.
		
		Each line is individually fed to _processInput, which handles
		evaluation.
		
		@type raw_string: basestring
		@param raw_string: Raw input from the IRC server.
		
		@rtype: variable|None
		@return: None if processing went smoothly; something if there was a
		    problem. (The returned value is meaningless; an event dictionary
		    will be generated to describe the problem)
		"""
		fragment = self._stash.getFragment()
		if fragment:
			raw_string = fragment + raw_string
			
		lines = re.split(r"\r|\n", raw_string)
		if not re.match(r"\r|\n", raw_string[-1]):
			self._stash.setFragment(lines.pop())
			
		for i in lines:
			if i:
				result = self._processInput(i)
				if result:
					return result
					
	def _processInput(self, raw_string):
		"""
		This function accepts raw lines from the IRC server and delegates its
		processing to one of the support libraries.
		
		A "Raw IRC Event" is generated if any plugins are waiting for them. If
		not, the event is suppressed.
		
		@type raw_string: basestring
		@param raw_string: The line to be processed.
		
		@rtype: variable|None
		@return: None if processing went smoothly; something if there was a
		    problem. (The returned value is meaningless; an event dictionary
		    will be generated to describe the problem)
		"""
		if self._connection: #Internal events might not need a connection.
			self._connection.resetTimeout()
			
		if GLOBAL.plugin.handlesRawEvent():
			self.addEvent(outboundDictionaries.IRC_Raw_Event(self.getContextID(), self.getName(), raw_string))
			
		if not raw_string.startswith(':'):
			try:
				return resources.irc_events.handleNonColon(self, raw_string) 
			except resources.irc_events.ProtocolError, e:
				self.addEvent(outboundDictionaries.Server_Protocol_Error(self.getContextID(), self.getName(), e.description))
		else: #Determine what sort of event this is.
			data = raw_string[1:].split(None, 2)
			if data[1].isdigit(): #Server code.
				try:
					return resources.numeric_events.handleIRCEvent(self, data[0], data[1:], raw_string)
				except resources.numeric_events.ProtocolError, e:
					self.addEvent(outboundDictionaries.Server_Protocol_Error(self.getContextID(), self.getName(), e.description))
			else:
				try:
					if data[0].find("!") == -1:
						return resources.irc_events.handleServerCode(self, data[0], data[1:], raw_string)
					else:
						return resources.irc_events.handleResponseCode(self, data[0], data[1:], raw_string)
				except resources.irc_events.ProtocolError, e:
					self.addEvent(outboundDictionaries.Server_Protocol_Error(self.getContextID(), self.getName(), e.description))
					
	def send(self, message, priority=GLOBAL.ENUM_SERVER_SEND_PRIORITY.AVERAGE):
		"""
		This function queues a string for transmission to the IRC server.
		
		@type message: basestring
		@param message: The string to be sent to the IRC server.
		@type priority: GLOBAL.ENUM_SERVER_SEND_PRIORITY.EnumValue
		@param priority: The priority the message will be assigned in the
		    queue.
		
		@return: Nothing.
		"""
		if self._connection: #Make sure a connection has indeed been established.
			self._connection.addMessage(message, priority)
			
	def ping(self, target=None):
		"""
		This function sends a PING to a user on the IRC server, or to the server
		itself.
		
		This function's logic resides within the Server's _Connection object.
		
		@type target: basestring|None
		@param target: The name of the user to be pinged, or None if the server
		    is the intended target.
		
		@return: Nothing.
		"""
		if self._connection: #Make sure a connection has indeed been established.
			self._connection.ping(target)
			
	def processPong(self, source=None):
		"""
		This function records the receipt of a PONG from either the IRC server
		or a user and returns the time that elapsed since the PING was sent.
		
		@type source: basestring|None
		@param source: The name of the user who sent the PONG reply, or None if
		    the reply came from the IRC server.
		
		@rtype: float|None
		@return: The number of seconds that elapsed between the PING and this
		    PONG, or None if the source isn't being tracked.
		"""
		if self._connection: #Make sure a connection has indeed been established.
			return self._connection.pong(source)
			
	def addChannel(self, channel_name):
		"""
		This function adds a new Channel to the server.
		
		The logic of this function has been exported to
		irc_channel.ChannelManager.addChannel().
		
		@type channel_name: basestring
		@param channel_name: A string containing the name of the channel to be
		    added.
		
		@return: Nothing.
		"""
		self._channel_manager.addChannel(channel_name)
		
	def addEvent(self, event):
		"""
		This function adds an event to the server's broadcast queue.
		
		@type event: dict
		@param event: The event to broadcast to PyRC's plugins.
		
		@return: Nothing.
		"""
		self._event_queue.put(event)
		
	def addUser(self, user):
		"""
		This function adds a new user to the pool of managed users.
		
		The logic of this function has been exported to
		irc_user.UserManagerServer.addUser().
		
		@type user: irc_user.User
		@param user: The User object to be added to the pool.
				
		@return: Nothing.
		"""
		self._user_manager.addUser(user)
		
	def getChannel(self, channel_name):
		"""
		This function will retrieve the specified Channel from the server.
		
		The logic of this function has been exported to
		irc_channel.ChannelManager.getChannel().
		
		@type channel_name: basestring
		@param channel_name: A string containing the name of the channel to be
		    retrieved.
		
		@rtype: Channel|None
		@return: The requested Channel object, or None if the channel could not
		    be found.
		"""
		return self._channel_manager.getChannel(channel_name)
		
	def getChannelManager(self):
		"""
		This function returns the pyrc_irc_abstract.irc_channel.ChannelManager
		object owned by this Server.
		
		@rtype: pyrc_irc_abstract.irc_channel.ChannelManager
		@return: The pyrc_irc_abstract.irc_channel.ChannelManager object owned by this
		    Server.
		"""
		return self._channel_manager
		
	def getConnectionData(self):
		"""
		This function returns the _ConnectionData object associated with this
		Server.
		
		@rtype: _ConnectionData
		@return: The _ConnectionData object associated with this Server.
		"""
		return self._connection_data
		
	def getContextID(self):
		"""
		This function returns the context ID assigned to this Server.
		
		@rtype: int
		@return: This Server's context ID.
		"""
		return self._context_id
		
	def getData(self):
		"""
		This function returns a dictionary containing all information known about
		the server.
		
		@rtype: dict
		@return: A dictionary of the format returned by
		    common.dictionaries.information.Server_Data().
		"""
		(address, port) = _connection.getAddress()
		
		ident = None
		realname = None
		if self._connection_data:
			profile = self._connection_data.getProfile()
			ident = profile[0]
			realname = profile[1]
			
		return informationDictionaries.ServerData(self._context_id, self._network_group_name, self._network_name, address, port, self.getNickname(), ident, realname, self.getUserModes(), self.getUserModeString(), self._channel_manager.getChannelsData(), self.getIdleTime(), self._local_ip)
		
	def getIdent(self):
		"""
		This function returns the ident this Server object is set to
		provide to IRC servers.
		
		@rtype: unicode|None
		@return: The ident this Server object provides to IRC servers.
		    
		    This value will not change while a connection is active, and it
		    will still be available through this function after a connection
		    ends.
		    
		    It changes only when a connection is attempted; it will be None if
		    this Server object is new.
		"""
		if self._connection_data:
			return self._connection_data.getProfile()[0]
		return None
		
	def getIdleTime(self):
		"""
		This function returns the number of seconds that have elapsed since the
		user last acted.
		
		@rtype: float
		@return: The number of seconds that have elapsed since the user last
		    acted.
		"""
		return time.time() - self._last_action
		
	def getLocalIP(self):
		"""
		This function returns the local IP of PyRC, as set by the user, seen by
		the server, or identified by a local check, which will generally return
		localhost.
		
		@rtype: unicode
		@return: The IP of the system running PyRC.
		"""
		if GLOBAL.DCC_LOCAL_IP:
			return GLOBAL.DCC_LOCAL_IP
			
		if self._local_ip:
			return self._local_ip
			
		try:
			local_ip = socket.gethostbyname(socket.gethostname())
			if local_ip:
				return local_ip
			return "127.0.0.1"
		except:
			return "127.0.0.1"
			
	def getName(self):
		"""
		This function returns the name of the IRC network to which this Server
		is connected.
		
		@rtype: unicode
		@return: The name of the IRC network to which this Server is connected.
		"""
		if self._network_group_name:
			return self._network_group_name
		return self._network_name
		
	def getNickname(self):
		"""
		This function returns the nickname currently associated with PyRC on
		the IRC server to which this Server is connected.
		
		@rtype: unicode
		@return: The nickname used by this Server on the IRC server.
		"""
		try:
			self._nickname_lock.acquire()
			return self._current_nickname
		finally:
			self._nickname_lock.release()
			
	def getRealName(self):
		"""
		This function returns the real name this Server object is set to
		provide to IRC servers.
		
		@rtype: unicode|None
		@return: The real name this Server object provides to IRC servers.
		    
		    This value will not change while a connection is active, and it
		    will still be available through this function after a connection
		    ends.
		    
		    It changes only when a connection is attempted; it will be None if
		    this Server object is new.
		"""
		if self._connection_data:
			return self._connection_data.getProfile()[1]
		return None
		
	def getStash(self):
		"""
		This function returns the _Stash object associated with this Server.
		
		@rtype: _Stash
		@return: The _Stash object associated with this Server.
		"""
		return self._stash
		
	def getUser(self, nickname):
		"""
		This function retrieves the pyrc_irc_abstract.irc_user.User object used to
		represent the named user on the IRC network.
		
		The logic of this function has been exported to
		irc_user.UserManagerServer.getUser().
		
		@type nickname: basestring
		@param nickname: The nickname of the user whose representation is to be
		    retrieved.
		
		@rtype: pyrc_irc_abstract.irc_user.User|None
		@return: The cached object used to represent the requested user, or
		    None if the user is not known.
		"""
		return self._user_manager.getUser(nickname)
		
	def getUserData(self, nickname):
		"""
		This function retrieves a standard user information dictionary that
		represents the current status of the named user on the IRC network.
		
		The logic of this function has been exported to
		irc_user.UserManagerServer.getUserData().
		
		@type nickname: basestring
		@param nickname: The nickname of the user whose representation is to be
		    retrieved.
		
		@rtype: dict|None
		@return: The user information dictionary that currently represents the
		    requested user, or None if the user is not known.
		"""
		return self._user_manager.getUserData(nickname)
		
	def getUserManager(self):
		"""
		This function retrieves this Server's UserManager object.
		
		@rtype: irc_user.UserManager
		@return: This Server's UserManager object.
		"""
		return self._user_manager
		
	def getUserModes(self):
		"""
		This function returns a tuple of all modes the IRC server has assigned
		to PyRC.
		
		@rtype: tuple
		@return: A tuple of modes set on PyRC by the server. Its members may be
		   single-character mode strings, or tuples formed of single-character
		   mode strings and a variable-length single-token paramater.
		"""
		try:
			self._mode_lock.acquire()
			return tuple(self._user_modes)
		finally:
			self._mode_lock.release()
			
	def getUserModeString(self):
		"""
		This function returns a string representing all modes the IRC server
		has assigned to PyRC.
		
		@rtype: unicode
		@return: A string representing all modes the IRC server has assigned to
		    PyRC, followed by their parameters.
		"""
		self._mode_lock.acquire()
		
		modestring = ''
		post_modestring = ''
		for i in self._user_modes:
			if isinstance(i, basestring):
				modestring += i
			else:
				modestring += i[0]
				post_modestring += ' %s' % i[1]
				
		self._mode_lock.release()
		return unicode(modestring + post_modestring)
		
	def isConnected(self):
		"""
		This function returns whether this Server object is currently connected
		to an IRC server.
		
		It works by determining whether a nickname is currently assigned to
		PyRC. When PyRC connects, it sets the _current_nickname variable; when
		the connection is lost, this variable is cleared.
		
		@rtype: bool
		@return: True if this Server object is connected to an IRC server;
		    False otherwise.
		"""
		try:
			self._nickname_lock.acquire()
			return not self._current_nickname == None
		finally:
			self._nickname_lock.release()
			
	def removeChannel(self, channel_name):
		"""
		This function will remove the specified Channel from the server.
		
		The logic of this function has been exported to
		irc_channel.ChannelManager.removeChannel().
		
		@type channel_name: basestring
		@param channel_name: A string containing the name of the channel to be
		    removed.
		
		@return: Nothing.
		"""
		self._channel_manager.removeChannel(channel_name)
		
	def removeUser(self, nickname):
		"""
		This function removes a user from the pool.
		
		The logic of this function has been exported to
		irc_user.UserManagerServer.removeUser().
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be removed.
		
		@return: Nothing.
		"""
		self._user_manager.removeUser(nickname)
		
	def resetIdleTime(self):
		"""
		This function resets the counter used to determine how long the user has
		been inactive.
		
		@return: Nothing.
		"""
		self._last_action = time.time()
		
	def setLocalIP(self, ip):
		"""
		This function is used to set the local IP of PyRC for this IRC server.
		
		@type ip: basestring
		@param ip: PyRC's IP address.
		
		@return: Nothing.
		"""
		self._local_ip = unicode(ip)
		
	def setName(self, network_name):
		"""
		This function sets the name of the IRC network to which this Server is
		connected.
		
		This function should only be called once per connection, based on the
		value in the "Welcome" event.
		
		@type network_name: unicode
		@param network_name: The name of the IRC network to which this Server
		    is connected.
		
		@return: Nothing.
		"""
		self._network_name = network_name
		
	def setNickname(self, nickname):
		"""
		This function updates the nickname currently associated with PyRC on
		the IRC server to which this Server is connected. It also updates the
		value to try first when reconnecting.
		
		@type nickname: unicode
		@param nickname: The nickname to set in place of the old one.
		
		@return: Nothing.
		"""
		self._nickname_lock.acquire()
		
		self._current_nickname = nickname
		
		self._nickname_lock.release()
		
	def updateUserModes(self, modes):
		"""
		This function updates the modes the IRC server has assigned to PyRC.
		
		@type modes: list
		@param modes: A list of changed modes with which to update PyRC's
		    internal mode list.
		    
		    These modes may be single-character mode strings or tuples
		    comprised of a single-character mode string and a variable-length
		    single-token parameter.
		
		@return: Nothing.
		"""
		self._mode_lock.acquire()
		
		for i in modes:
			if i[2]:
				if not i[1]:
					self._user_modes.append(i[0])
				else:
					self._user_modes.append(i[:2])
			else:
				for j in self._user_modes:
					if j[0] == i[0]:
						self._user_modes.remove(j)
						break
						
		self._user_modes.sort()
		
		self._mode_lock.release()	
		
	def updateUserNickname(self, nickname, new_nickname):
		"""
		This function ensures that a name change by another user on the IRC
		network is properly reflected in all areas of PyRC's local cache.
		
		The logic of this function has been exported to
		irc_user.UserManagerServer.updateUserNickname().
		
		@type nickname: basestring
		@param nickname: The old nickname of the user.
		@type new_nickname: basestring
		@param new_nickname: The new nickname of the user.
		
		@return: Nothing.
		"""
		self._user_manager.updateUserNickname(nickname, new_nickname)
		
class _ConnectionData(object):
	"""
	This class serves as a container for data needed to establish a connection
	to an IRC server. One should be attached to each Server object.
	"""
	_profiles = None #: The profile data to use on this connection.
	_nicknames = None #: A list of nicknames that can be used on this connection.
	_nickname_counter = -1 #: A pointer to the last attempted nickname.
	_addresses = None #: A list of addresses that can be connected to.
	_address_counter = -1 #: A pointer to the last attemped connection.
	_password = None #: The network's password, if any.
	
	def __init__(self, nicknames, profile, addresses, password):
		"""
		This function is invoked when a new _ConnectionData object is created.
		
		@type nicknames: list
		@param nicknames: A list of nicknames to cycle through in order to
		    establish a connection to an IRC server.
		@type profile: tuple
		@param profile: A tuple containing the ident and real name to provide
		    to the IRC server once a connection has been established.
		@type addresses: list
		@param addresses: A list of IRC server addresses to try.
		@type password: unicode|None
		@param password: The password required by the IRC network, if any.
		
		@return: Nothing.
		
		@raise InstantiationError: If any of profile, nicknames, or addresses
		    are incomplete.
		"""
		if not profile[0] or not profile[1]:
			raise InstantiationError(u"No profiles have been specified for use on this connection.")
		if not nicknames:
			raise InstantiationError(u"No nicknames have been specified for use on this connection.")
		if not addresses:
			raise InstantiationError(u"No addresses have been specified for use on this connection.")
		self._nicknames = nicknames
		self._profile = profile
		self._addresses = addresses
		self._password = password
		
	def getAddress(self):
		"""
		This function will provide the next address in the list of addresses to
		try in an attempt to establish a connection.
		
		If there are no remaining addresses, it will return None, and it should
		be assumed that the connection attempt failed.
		
		@rtype: tuple|None
		@return: The next URL/port/SSL triple to try in an attempt to establish
		    a connection, or None if all addresses have been exhausted.
		"""
		if self._address_counter + 1 < len(self._addresses):
			self._address_counter += 1
			return self._addresses[self._address_counter]
		return None
		
	def getNickname(self):
		"""
		This function will provide the next nickname in the list of nicknames
		to try in an attempt to establish a connection.
		
		If there are no remaining nicknames, it will return None, and it should
		be assumed that the connection attempt failed.
		
		@rtype: unicode|None
		@return: The next nickname to try in an attempt to establish a
		    connection, or None if all nicknames have been exhausted.
		"""
		if self._nickname_counter + 1 < len(self._nicknames):
			self._nickname_counter += 1
			return self._nicknames[self._nickname_counter]
		return None
		
	def getPassword(self):
		"""
		This function returns the password used by the IRC network, if any.
		
		@rtype: unicode|None
		@return: The password provided to the IRC network, if any.
		"""
		return self._password
		
	def getProfile(self):
		"""
		This function returns the ident and real name PyRC presented to the IRC
		server.
		
		@rtype: tuple
		@return: The ident and real name in a tuple.
		"""
		return self._profile
		
	def setConnected(self):
		"""
		This function resets the address cycle and returns the address that was
		ultimately used to establish a connection to the server.
		
		It should be called only once a connection has been confirmed.
		
		@rtype: unicode
		@return: The address of the IRC server to which a connection was
		    established.
		"""
		address = self._addresses[self._address_counter]
		self._address_counter = -1
		return address
		
	def setAuthenticated(self):
		"""
		This function resets the nickname cycle and returns the profile that
		was ultimately used to establish a connection to the server.
		
		It should be called only once a connection has been confirmed and a
		'Welcome' event has been received.
		
		@rtype: unicode
		@return: The nickname that was ultimately used to connect to the server.
		"""
		nickname = self._nicknames[self._nickname_counter]
		self._nickname_counter = -1
		return nickname
		
		
class _Stash(object):
	"""
	This class provides a resource for aggregating data received from the IRC
	server in order to emit complete dictionaries.
	"""
	_server = None #: A reference to the Server that owns this object.
	_motd = None #: A list of lines that comprise the IRC server's Message of the Day.
	_banlists = None #: A dictionary of channels that are currently receiving their banlist information.
	_channels = None #: A dictionary of channels that are incomplete, waiting for additional information before being presented to PyRC.
	_userlists = None #: A dictionary of pyrc_irc_abstract.irc_channel.Channel or pyrc_irc_abstract.irc_channel.SimpleUserContainer objects, keyed by channel name, that are used to direct the results of an IRC server's NAME events.
	_whois_replies = None #: A dictionary used to track WHOIS requests sent by PyRC. Data is received in bits and pieces, so it needs to be aggregated before a dictionary can be emitted.
	_whowas_replies = None #: A dictionary used to track WHOWAS requests sent by PyRC. Data is received in bits and pieces, so it needs to be aggregated before a dictionary can be emitted.
	_who_replies = None #: A dictionary used to track WHO requests sent by PyRC. Data is received in bits and pieces, so it needs to be aggregated before a dictionary can be emitted.
	_fragment = None #: A string fragment of a line received from the IRC server. This is used if the data the server tried to send exceeds the allowed packet size.
	
	def __init__(self, server):
		"""
		This function is invoked when a new _Stash object is created.
		
		@type server: Server
		@param server: A reference to the Server that owns this object.
		
		@return: Nothing.
		"""
		self._server = server
		
		self.flush()
		
	def flush(self):
		"""
		This function is invoked when the contents of this _Stash object are no
		longer needed.
		
		@return: Nothing.
		"""
		self._motd = None
		self._banlists = {}
		self._channels = {}
		self._userlists = {}
		self._whois_replies = {}
		self._whowas_replies = {}
		self._who_replies = {}
		self._fragment = None
		
	def completeMOTD(self):
		"""
		This function returns the complete MOTD and frees the memory used to
		build it.
		
		This function should be called only when the server indicates that the
		MOTD has been fully transmitted.
		
		@rtype: list
		@return: The list of lines comprising the server's MOTD.
		"""
		motd = self._motd
		self._motd = None
		return motd
		
	def getMOTD(self):
		"""
		This function retrieves the _Stash's working MOTD list.
		
		The object returned by this function should be modified directly using
		append().
		
		@rtype: list
		@return: The working collection of MOTD lines received from the server.
		"""
		if not self._motd:
			self._motd = []
		return self._motd 
		
	def completeBanlist(self, channel_name):
		"""
		This function retrieves a completed banlist for a channel.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which the banlist is to
		    be retrieved.
		
		@rtype: tuple
		@return: This channel's banlist. Its elements are tuples with the
		    following format::
			 (<banmask:unicode>, <server_maintaining_ban:unicode>,
			  <unix_ban_timestamp:int>)
		"""
		#Sanitize input.
		channel_name = unicode(channel_name).lower()
		banlist = self._banlists.get(channel_name)
		if banlist:
			del self._banlists[channel_name]
			banlist = tuple(banlist)
		else:
			banlist = ()
		return banlist
		
	def getBanlist(self, channel_name):
		"""
		This function retrieves an active banlist that is waiting to be
		populated by information as it arrives from the server.
		
		The object returned by this function should be appended to directly.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which the banlist is to
		    be retrieved.
		
		@rtype: list
		@return: The list used to store this channel's banlist. Its elements
		    are tuples with the following format::
			 (<banmask:unicode>, <server_maintaining_ban:unicode>,
			  <unix_ban_timestamp:int>)
		"""
		#Sanitize input.
		channel_name = unicode(channel_name).lower()
		banlist = self._banlists.get(channel_name)
		if not banlist:
			banlist = []
			self._banlists[channel_name] = banlist
		return banlist
		
	def completeChannel(self, channel_name):
		"""
		This function returns a dictionary with all information required to
		properly represent a channel on the IRC server, while freeing the
		memory used to build it.
		
		This function should be called only when the server indicates that the
		channel data has been fully transmitted (when the last nickname is
		received).
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which data is to be
		    retrieved.
		
		@rtype: dict
		@return: A dictionary containing all information required to properly
		    represent a channel on the IRC server.
		"""
		#Sanitize input.
		channel_name = unicode(channel_name).lower()
		channel = self._channels.get(channel_name)
		if channel:
			del self._channels[channel_name]
		return channel
		
	def createChannel(self, channel_name):
		"""
		This function creates a new, blank channel dictionary that will wait to
		be populated by information as it arrives from the server.
		
		The object returned by this function should be modified directly using
		Python's dictionary operators.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which data is to be
		    retrieved.
		
		@rtype: dict
		@return: The new dictionary created to collect information related to
		    the status of a channel on the IRC server.
		"""
		#Sanitize input.
		channel_name = unicode(channel_name).lower()
		channel = {
		 'channel': channel_name,
		 'topicwho': None,
		 'topictime': None
		}
		self._channels[channel_name] = channel
		return channel
		
	def getChannel(self, channel_name):
		"""
		This function retrieves an active channel dictionary that is waiting to
		be populated by information as it arrives from the server.
		
		The object returned by this function should be modified directly using
		Python's dictionary operators.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which data is to be
		    retrieved.
		
		@rtype: dict|None
		@return: The dictionary used to collect information related to the
		    status of a channel on the IRC server, or None if the channel
		    dictionary was not previously created with createChannel().
		"""
		return self._channels.get(unicode(channel_name).lower())
		
	def completeUserList(self, channel_name):
		"""
		This function returns an object with all information required to
		properly represent a list of users in a channel on the IRC server,
		while freeing the memory used to build it.
		
		This function should be called only when the server indicates that the
		name list has been fully transmitted.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which data is to be
		    retrieved.
		
		@rtype: pyrc_irc_abstract.irc_channel._UserContainer
		@return: Either a pyrc_irc_abstract.irc_channel.Channel object
			containing a full list of users if PyRC is in the requested channel,
			or a pyrc_irc_abstract.irc_channel.SimpleUserContainer object
			containing a full list of users if PyRC is scanning another channel.
		"""
		#Sanitize input.
		channel_name = unicode(channel_name.lower())
		channel = self._userlists.get(channel_name)
		if channel:
			del self._userlists[channel_name]
		return channel
		
	def createUserList(self, channel_name):
		"""
		This function indicates that an object should be provided to collect
		the names of users in a channel. The nature of this object will vary
		depending on whether PyRC happens to be in the channel in question, but
		their relevant functions have identical signatures.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which data is to be
		    retrieved.
		
		@rtype: pyrc_irc_abstract.irc_channel._UserContainer
		@return: Either a pyrc_irc_abstract.irc_channel.Channel object
			containing an empty list of users if PyRC is in the requested
			channel, or a pyrc_irc_abstract.irc_channel.SimpleUserContainer
			object containing an empty list of users if PyRC is scanning another
			channel.
		"""
		#Sanitize input.
		channel_name = unicode(channel_name.lower())
		channel = self._server.getChannel(channel_name)
		if channel:
			self._userlists[channel_name] = channel
		else:
			channel = irc_channel.SimpleUserContainer(self._server)
			self._userlists[channel_name] = channel
		return channel
		
	def getUserList(self, channel_name):
		"""
		This function provides an object to use to collect the names of users
		in a channel. The nature of this object will vary depending on whether
		PyRC happens to be in the channel in question, but their relevant
		functions have identical signatures.
		
		@type channel_name: basestring
		@param channel_name: The name of the channel for which data is to be
		    retrieved.
		
		@rtype: pyrc_irc_abstract.irc_channel._UserContainer
		@return: Either a pyrc_irc_abstract.irc_channel.Channel object
		    containing a list of users if PyRC is in the requested channel, or a
		    pyrc_irc_abstract.irc_channel.SimpleUserContainer object containing
		    a list of users if PyRC is scanning another channel.
		"""
		return self._userlists.get((unicode(channel_name.lower())))
		
	def completeWho(self, username):
		"""
		This function returns a dictionary with all information required to
		properly represent a WHO response from an IRC server, while freeing
		the memory used to build it.
		
		This function should be called only when the server indicates that the
		WHO information has been fully transmitted.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary containing all elements necessary to build a
		    complete WHO event dictionary.
		"""
		#Sanitize input.
		username = unicode(username).lower()
		who = self._who_replies.get(username)
		if who:
			del self._who_replies[username]
		return who
		
	def createWho(self, username):
		"""
		This function creates a dictionary that will collect information
		required to	properly represent a WHO response from an IRC server.
		
		The dictionary returned by this function should be manipulated using
		the normal Python dictionary interfaces.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary used to store the elements necessary to build a
		    complete WHO event dictionary.
		"""
		who = {
		 'channels': None,
		 'userdata': None
		}
		self._who_replies[unicode(username).lower()] = who
		return who
		
	def completeWhoIs(self, username):
		"""
		This function returns a dictionary with all information required to
		properly represent a WHOIS response from an IRC server, while freeing
		the memory used to build it.
		
		This function should be called only when the server indicates that the
		WHOIS information has been fully transmitted.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary containing all elements necessary to build a
		    complete WHOIS event dictionary.
		"""
		#Sanitize input.
		username = unicode(username).lower()
		whois = self._whois_replies.get(username)
		if whois:
			del self._whois_replies[username]
		return whois
		
	def createWhoIs(self, username):
		"""
		This function creates a dictionary that will collect information
		required to	properly represent a WHOIS response from an IRC server.
		
		The dictionary returned by this function should be manipulated using
		the normal Python dictionary interfaces.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary used to store the elements necessary to build a
		    complete WHOIS event dictionary.
		"""
		whois = {
		 'ircserver': None,
		 'servername': None,
		 'address': None,
		 'idletime': None,
		 'channels': [],
		 'modes': None,
		 'bot': None,
		 'chanop': None,
		 'help': None,
		 'operator': None,
		 'registered': [],
		 'secure': None,
		 'data': [],
		 'userdata': None
		}
		self._whois_replies[unicode(username).lower()] = whois
		return whois
		
	def getWhoIs(self, username):
		"""
		This function returns a dictionary that will collect information
		required to	properly represent a WHOIS response from an IRC server.
		
		The dictionary returned by this function should be manipulated using
		the normal Python dictionary interfaces.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary used to store the elements necessary to build a
		    complete WHOIS event dictionary.
		"""
		return self._whois_replies.get(unicode(username).lower())
		
	def completeWhoWas(self, username):
		"""
		This function returns a dictionary with all information required to
		properly represent a WHOWAS response from an IRC server, while freeing
		the memory used to build it.
		
		This function should be called only when the server indicates that the
		WHOWAS information has been fully transmitted.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary containing all elements necessary to build a
		    complete WHOWAS event dictionary.
		"""
		#Sanitize input.
		username = unicode(username).lower()
		whowas = self._whowas_replies.get(username)
		if whowas:
			del self._whowas_replies[username]
		return whowas
		
	def createWhoWas(self, username):
		"""
		This function creates a dictionary that will collect information
		required to	properly represent a WHOWAS response from an IRC server.
		
		The dictionary returned by this function should be manipulated using
		the normal Python dictionary interfaces.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary used to store the elements necessary to build a
		    complete WHOWAS event dictionary.
		"""
		whowas = {
		 'lastserver': None,
		 'lastseen': None,
		 'userdata': None
		}
		self._whowas_replies[unicode(username).lower()] = whowas
		return whowas
		
	def getWhoWas(self, username):
		"""
		This function returns a dictionary that will collect information
		required to	properly represent a WHOWAS response from an IRC server.
		
		The dictionary returned by this function should be manipulated using
		the normal Python dictionary interfaces.
		
		@type username: basestring
		@param username: The name of the user for whom information was
		    requested.
		
		@rtype: dict
		@return: A dictionary used to store the elements necessary to build a
		    complete WHOWAS event dictionary.
		"""
		return self._whowas_replies.get(unicode(username).lower())
		
	def getFragment(self):
		"""
		This function retrieves any partial line that may have been cut if the
		IRC server tried to send more information than it could fit in a
		packet.
		
		@rtype: basestring|None
		@return: A line fragment or None if the last packet ended cleanly.
		"""
		fragment = self._fragment
		self._fragment = None
		return fragment
		
	def setFragment(self, fragment):
		"""
		This function is used to save a partial line that was cut because the
		IRC server tried to send more data than could be accepted in a packet.
		
		@type fragment: basestring
		@param fragment: The partial line to be stored.
		
		@return: Nothing.
		"""
		self._fragment = fragment
		
class _Connection(object):
	"""
	This class maintains a connection to an IRC server, and handles all data
	traffic over the connection's lifetime.
	"""
	_server = None #: The Server that owns this object.
	_socket = None #: A resources.connection._Socket used to communicate with the IRC server.
	_socket_reader = None #: A _SocketReader used to generate events from messages sent by the IRC server.
	_socket_sender = None #: A _SocketSender used to feed new messages to the IRC server.
	_ping_core = None #: A _PingCore used to manage all PING-related services on this connection.
	_priority_queue = None #: A _PriorityQueue object used to manage outbound data.
	
	def __init__(self, server, host, port, nickname, realname, ident, password, ssl):
		"""
		This function is invoked when creating a new _Connection object.
		
		It connects to the specified IRC server and authenticates the connection.
		
		@type server: Server
		@param server: A reference to the Server that owns this object.
		@type host: basestring
		@param host: The DNS, IP, or host address of the IRC server to which a
		    connection will be made.
		@type port: int
		@param port: The port on the IRC server to which a connection will be
		    made.
		@type nickname: basestring
		@param nickname: The nickname to be used by this connection.
		@type realname: basestring
		@param realname: The real name to be used by this connection.
		@type ident: basestring
		@param ident: The ident string to the used by this connection.
		@type password: basestring|None
		@param password: The password used to log into the IRC server, if
		    required.
		@type ssl: bool
		@param ssl: True if an encrypted connection is to be used.
		
		@return: Nothing.
		
		@raise resources.connection.ConnectionError: If a connection could not be
		    established at the specified host/port.
		"""
		self._server = server
		
		if ssl:
			self._socket = resources.connection.SSLSocket()
		else:
			self._socket = resources.connection.BasicSocket()
		self._socket.connect(host, port)
		
		time.sleep(0.5) #Prevent "client too fast" errors.
		if password: #Authenticate.
			self.send("PASS %s" % password)
		self.send("NICK %s" % nickname)
		self.send("USER %s %s %s :%s" % (ident, socket.gethostname(), host, realname))
		
		self._socket_reader = _SocketReader(self)
		self._socket_sender = _SocketSender(self)
		self._ping_core = _PingCore(self)
		self._priority_queue = _PriorityQueue()
		
		self._socket_reader.start()
		self._socket_sender.start()
		self._ping_core.start()
		
	def addMessage(self, message, priority=GLOBAL.ENUM_SERVER_SEND_PRIORITY.AVERAGE):
		"""
		This function queues a message to be sent to the IRC server.
		
		@type message: basestring
		@param message: The message to be sent to the IRC server.
		@type priority: GLOBAL.ENUM_SERVER_SEND_PRIORITY.EnumValue
		@param priority: An enumeration value used to determine the priority at
		    which this message should be pulled out of the queue.
		
		@return: Nothing.
		"""
		if priority == GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW:
			try:
				self.send(message)
			except resources.connection.InvalidStateError: #The socket must have been closed prior to this instruction.
				pass
		else:
			self._priority_queue.addMessage(message, priority)
			
	def close(self):
		"""
		This function terminates all connections and threads in use by this
		_Connection object.
		
		@return: Nothing.
		"""
		self._ping_core.kill()
		self._socket_reader.kill()
		self._socket_sender.kill()
		
		self._socket.close()
		
	def getLatency(self):
		"""
		This function returns the number of seconds that have elapsed since the
		IRC server was last pinged by PyRC.
		
		@rtype: float
		@return: The number of seconds that have elapsed since PyRC last pinged
		    the server.
		"""
		return self._ping_core.getServerPingTime()
			
	def getMessage(self):
		"""
		This function returns the next message to be sent to the IRC server.
		
		@rtype: unicode|None
		@return: The next message to be sent, if any, or None if no message is
		    waiting.
		"""
		return self._priority_queue.getMessage()
		
	def getMessageCount(self):
		"""
		This function will return the number of unsent messages.
		
		It might be useful to provide throttle information.
		
		@rtype: int
		@return: The number of unsent messages in the queue.
		"""
		return self._priority_queue.getMessageCount()
		
	def getServer(self):
		"""
		This function returns a reference to the Server that owns this object.
		
		@rtype: Server
		@return: A reference to the Server that owns this object.
		"""
		return self._server
		
	def read(self):
		"""
		This function reads data from the IRC server.
		
		@rtype: basestring|None
		@return: The data received from the IRC server, or None if no data was
		    available.
		
		@raise InvalidStateError: If the socket is dead.
		@raise IncomingTransmissionError: If a problem occurred when reading data
		    from the connection.
		"""
		return self._socket.readData(GLOBAL.IRC_PACKET_SIZE)
		
	def send(self, message):
		"""
		This function sends data to the IRC server.
		
		@type message: basestring
		@param message: The string to be sent to the IRC server.
		
		@return: Nothing.
		
		@raise InvalidStateError: If the socket is dead.
		@raise OutgoingTransmissionError: If a problem occurred when writing data
		    to the connection.		
		"""
		if GLOBAL.plugin.handlesRawCommand():
			self._server.addEvent(outboundDictionaries.IRC_Raw_Command(self._server.getContextID(), self._server.getName(), message))
		self._socket.sendData(message.encode("utf-8") + GLOBAL.IRC_LINE_TERMINATOR)
		
	def ping(self, target=None):
		"""
		This function sends a PING to a user on the IRC server, or to the server
		itself.
		
		@type target: basestring|None
		@param target: The name of the user to be pinged, or None if the server
		    is the intended target.
		
		@return: Nothing.
		"""
		self._ping_core.sendPing(target)
		
	def pong(self, source=None):
		"""
		This function is called to indicate that a user has replied with a PONG.
		
		@type source: basestring|None
		@param source: The name of the user who responded with a PONG, or None if
		    it was the server.
		
		@rtype: float|None
		@return: The number of seconds that passed since the PING was sent or
		    None if the source isn't being tracked.
		"""
		if source:
			return self._ping_core.removeUser(source)
		else:
			return self._ping_core.getServerPingTime()
			
	def resetTimeout(self):
		"""
		This function prevents a fatal PING timeout event from being raised. It
		should be called every time data is received from the server.
		
		@return: Nothing.
		"""
		self._ping_core.resetCountdown()
		
		
class _PingCore(threading.Thread):
	"""
	This class defines an object that manages all PING-related activity on a
	server, including user PING timeouts, and server PING-accessibility.
	"""
	_alive = True #: True until the thread is no longer useful.
	_connection = None #: A reference to the _Connection that owns this object.
	_server = None #: A reference to the _Server that owns this object.
	_user_lock = None #: A lock used to prevent multiple simultaneous accesses to the user list.
	_time_of_server_ping = None #: The time at which the last PING was sent to the server.
	_server_timeout = None #: The timestamp against which timeout events will be processed.
	_server_pinged = False #: Set to True when the server is PINGed to test for activity.
	_time_lock = None #: A lock used to prevent multiple simultaneous accesses to the timeout counters.
	_users = None
	"""
	A dictionary of users to whom PINGs have been sent, but who have yet to
	reply with a PONG.
	
	Elements in this dictionary take the following form::
	 {
	  <username:unicode>: <time_of_ping:float>
	 }
	"""
	
	def __init__(self, connection):
		"""
		This function is invoked when creating a new _PingCore object.
		
		@type connection: _Connection
		@param connection: A reference to the _Connection that owns this object.
		
		@return: Nothing.
		"""
		threading.Thread.__init__(self)
		self._connection = connection
		self._server = connection.getServer()
		self._user_lock = threading.Lock()
		self._time_lock = threading.RLock()
		self._users = {}
		self._time_of_server_ping = time.time()
		self._server_timeout = time.time()
		self.setDaemon(True)
		self.setName("Ping Core, server %i" % self._server.getContextID())
		
	def kill(self):
		"""
		This function terminates the _PingCore's execution after its current
		iteration.
		
		It should be called when its parent is destroyed.
		
		@return: Nothing.
		"""
		self._alive = False
		
	def run(self):
		"""
		This function is executed over the course of the _PingCore's lifetime.
		
		It decrements the time remaining before a PING timeout for each tracked
		user, and the time remaining before an automatic PING is sent to the
		server to ensure that the connection is still active.
		
		Alternatively, if such a PING has been sent to the server, it counts down
		the time before declaring the server unresponsive and raising a
		Ping Timeout event.
		
		@return: Nothing.
		"""
		while self._alive:
			start_time = time.time()
			self._user_lock.acquire()
			
			timeouts = []
			for i, user_time in self._users.iteritems():
				if start_time - user_time >= GLOBAL.IRC_IDLE_WAIT_TIME:
					timeouts.append(i)
					
			for i in timeouts:
				self._server.addEvent(outboundDictionaries.IRC_Ping_Timeout(self._server.getContextID(), i, self._server.getName()))
				del self._users[i]
				
			self._user_lock.release()
			self._time_lock.acquire()
			
			working_time = start_time - self._server_timeout
			if working_time >= GLOBAL.IRC_IDLE_WAIT_TIME:
				if not self._server_pinged:
					self._server.addEvent(outboundDictionaries.IRC_Ping_Timeout_Check(self._server.getContextID(), self._server.getName()))
					self.sendPing()
				elif working_time >= GLOBAL.IRC_IDLE_WAIT_TIME + GLOBAL.IRC_PING_TIMEOUT:
					self._server.addEvent(outboundDictionaries.IRC_Ping_Timeout(self._server.getContextID(), self._server.getName(), None))
					self._server.addEvent(outboundDictionaries.Server_Disconnection(self._server.getContextID(), self._server.getName(), "Ping timeout.", False))
					self._server.disconnect()
					
			self._time_lock.release()
			time.sleep(1)
			
	def getServerPingTime(self):
		"""
		This function returns the number of seconds that have elapsed since the
		IRC server was last pinged by PyRC.
		
		This function can be used to provide a reasonably relevant latency
		counter, as long as it is called only when a PONG is received, or
		after a "Ping Request Automated" event.
		
		@rtype: float
		@return: The number of seconds that have elapsed since PyRC last pinged
		    the server.
		"""
		try:
			self._time_lock.acquire()
			return time.time() - self._time_of_server_ping
		finally:
			self._time_lock.release()
			
	def removeUser(self, username):
		"""
		This function is called to indicate that a user has replied with a PONG.
		It aborts the user's timeout countdown.
		
		@type username: basestring
		@param username: The name of the user who responded with a PONG.
		
		@rtype: float|None
		@return: The time at which the user was PINGed, or None if the user
		    hasn't been PINGed.
		"""
		#Sanitize input.
		username = unicode(username).lower()
		self._user_lock.acquire()
		
		ping_time = self._users.get(username)
		if ping_time:
			ping_time = time.time() - ping_time
			del self._users[username]
			
		self._user_lock.release()
		return ping_time
		
	def resetCountdown(self):
		"""
		This function prevents a fatal PING timeout event from being raised. It
		should be called every time data is received from the server.
		
		@return: Nothing.
		"""
		self._time_lock.acquire()
		
		self._server_timeout = time.time()
		self._server_pinged = False
		
		self._time_lock.release()
		
	def sendPing(self, username=None):
		"""
		This function sends a PING to a user on the IRC server, or to the server
		itself.
		
		@type username: basestring|None
		@param username: The name of the user to be pinged, or None if the server
		    is the intended target.
		
		@return: Nothing.
		"""
		ping_time = time.time()
		current_time = str(ping_time)
		current_time = current_time[:current_time.find('.')]
		
		ping_string = None
		if username:
			#Sanitize input.
			username = unicode(username)
			self._user_lock.acquire()
			
			self._users[username.lower()] = ping_time
			
			self._user_lock.release()
			ping_string = "PRIVMSG %s :\001PING %s\001" % (username, current_time)
		else:
			self._time_lock.acquire()
			
			self._server_pinged = True
			self._time_of_server_ping = ping_time
			
			self._time_lock.release()
			ping_string = "PING :%s" % current_time
			
		try:
			self._connection.send(ping_string)
		except resources.connection.OutgoingTransmissionError:
			self._server.addEvent(outboundDictionaries.Server_Disconnection(self._server.getContextID(), self._server.getName(), u"Connection reset by peer.", False))
			self._server.disconnect()
		except resources.connection.InvalidStateError: #The socket must have been closed prior to this instruction.
			pass
			
			
class _PriorityQueue(object):
	"""
	This class maintains a series of queues, which are used to prioritise
	messages sent to the IRC server, since they need to be throttled to avoid
	an "Excessive Flood" kick.
	
	Under a five-queue system, the following guidelines should be used when
	assigning priorities::
	 1: Absolute must-send (KICK)
	 2: Important (NICK)
	 3: Significant (NOTICE)
	 4: Normal (PRIVMSG)
	 5: Whenever (WHO)
	"""
	_length = None #: The number of messages sitting in the various queues.
	_queues = None #: A list of lists that will behave like queues to organize messages.
	_queue_lock = None #: A lock used to prevent multiple simultaneous access to the queue lists.
	
	def __init__(self):
		"""
		This function is invoked when creating a new _PriorityQueue object.
		
		@return: Nothing.
		"""
		self._queues = []
		self._queue_lock = threading.Lock()
		self._length = 0
		
		for i in range(len(GLOBAL.ENUM_SERVER_SEND_PRIORITY) - 1):
			self._queues.append([])
			
	def addMessage(self, message, priority):
		"""
		This function adds a new message to the queue structure.
		
		@type message: basestring
		@param message: The string to be sent to the IRC server.
		@type priority: GLOBAL.ENUM_SERVER_SEND_PRIORITY.EnumValue
		@param priority: The priority at which the message should be queued.
		    As may be expected, the higher the priority, the sooner the send.
		
		@return: Nothing.
		"""
		self._queue_lock.acquire()
		
		self._queues[priority.index - 1].insert(0, unicode(message))
		self._length += 1
		
		self._queue_lock.release()
		
	def getMessage(self):
		"""
		This function pops the next message to be sent to the IRC server.
		
		@rtype: unicode|None
		@return: The next message to be sent, if any, or None if the queue
		    structure is unpopulated.
		"""
		self._queue_lock.acquire()
		
		message = None
		for i in range(len(self._queues)):
			if self._queues[i]:
				message = self._queues[i].pop()
				self._length -= 1
				break
				
		self._queue_lock.release()
		return message
		
	def getMessageCount(self):
		"""
		This function will return the number of unsent messages.
		
		It might be useful to provide throttle information.
		
		@rtype: int
		@return: The number of unsent messages in the queue.
		"""
		try:
			self._queue_lock.acquire()
			return self._length
		finally:
			self.queue_lock.release()
			
			
class _SocketReader(threading.Thread):
	"""
	This class regularly checks its parent's socket for new data, and sends
	what it finds to its parent Server for processing.
	"""
	_connection = None #: A reference to the _Connection that owns this object.
	_server = None #: A reference to the Server that owns this object.
	_alive = True #: True until the thread is no longer useful.
	
	def __init__(self, connection):
		"""
		This function is invoked when creating a new _SocketReader object.
		
		@type connection: _Connection
		@param connection: A reference to the _Connection that owns this object.
		
		@return: Nothing.
		"""
		threading.Thread.__init__(self)
		self._connection = connection
		self._server = self._connection.getServer()
		self.setDaemon(True)
		self.setName("Socket Reader, server %i" % self._server.getContextID())
		
	def kill(self):
		"""
		This function terminates the _SocketReader's execution after its current
		iteration.
		
		It should be called when its parent is destroyed.
		
		@return: Nothing.
		"""
		self._alive = False
		
	def run(self):
		"""
		This function is executed over the course of the _SocketReader's
		lifetime.
		
		It checks the socket for new data continuously, and sends anything it
		finds to the Server for processing.
		
		@return: Nothing.
		"""
		while self._alive:
			data = None
			try:
				data = self._connection.read()
			except resources.connection.InvalidStateError: #The socket must have been closed prior to this instruction.
				break
			except resources.connection.IncomingTransmissionError:
				self._server.addEvent(outboundDictionaries.Server_Disconnection(self._server.getContextID(), self._server.getName(), "Connection reset by peer.", False))
				self._server.disconnect()
			except resources.connection.SocketPollError:
				self._server.addEvent(outboundDictionaries.IRC_Ping_Timeout_Check(self._server.getContextID(), self._server.getName()))
				try:
					self._connection.ping()
				except resources.connection.OutgoingTransmissionError:
					self._server.addEvent(outboundDictionaries.Server_Disconnection(self._server.getContextID(), self._server.getName(), "Remote host closed socket.", False))
					self._server.disconnect()
					
			if data:
				data = self._server.processInput(data)
				if data: #The server told us to disconnect.
					if data[0]:
						self._server.addEvent(outboundDictionaries.Server_Disconnection(self._server.getContextID(), self._server.getName(), data[0], not data[1]))
					self._server.disconnect()
				else:
					self._connection.resetTimeout()
					
class _SocketSender(threading.Thread):
	"""
	This class regularly checks its parent _Connection for new messages, and
	sends them to the IRC server.
	"""
	_connection = None #: The _Connection that owns this object.
	_alive = True #: True until the thread is no longer useful.
	
	def __init__(self, connection):
		"""
		This function is invoked when creating a new _SocketSender object.
		
		@type connection: _Connection
		@param connection: A reference to the _Connection that owns this object.
		
		@return: Nothing.
		"""
		threading.Thread.__init__(self)
		self._connection = connection
		self.setDaemon(True)
		self.setName("Socket Sender, server %i" % self._connection.getServer().getContextID())
		
	def kill(self):
		"""
		This function terminates the _SocketSender's execution after its current
		iteration.
		
		It should be called when its parent is destroyed.
		
		@return: Nothing.
		"""
		self._alive = False
		
	def run(self):
		"""
		This function is executed over the course of the _SocketSender's
		lifetime.
		
		It checks its parent for new messages every 0.1 seconds, and sends
		anything it finds to the IRC server.
		
		@return: Nothing.
		"""
		while self._alive:
			message = self._connection.getMessage()
			if message:
				try:
					self._connection.send(message)
				except resources.connection.InvalidStateError: #The socket must have been closed prior to this instruction.
					break
				except resources.connection.OutgoingTransmissionError:
					server = self._connection.getServer()
					server.addEvent(outboundDictionaries.Server_Disconnection(server.getContextID(), server.getName(), "Remote host closed socket."))
					server.disconnect()
					
			time.sleep(0.1)
			
class ServerManager(object):
	"""
	This class maintains a server-specific list of servers.
	"""
	_server_lock = None #: A lock used to prevent multiple simultaneous accesses to the server pool.
	_connection_counter = 0 #: A counter used to ensure that every server object has a unique ID number.
	_servers = None
	"""
	A dictionary containing a list of all servers managed by this object.
	
	Its elements take the following form::
	 {
	  <id_number:int>: <:Server>
	 }
	"""
	
	def __init__(self):
		"""
		This function is invoked when a new ServerManager object is created.
		
		@return: Nothing.
		"""
		self._server_lock = threading.Lock()
		self._servers = {}
		
	def addServer(self, name, thread_count):
		"""
		This function creates a blank Server object.
		
		@type name: basestring|None
		@param name: The name to use to identify this Server object. None to
		    allow IRC-network-based resolution.
		@type thread_count: int
		@param thread_count: The number of worker threads to spawn for this
		    Server.
		
		@rtype: Server
		@return: The newly created Server.		
		"""
		self._server_lock.acquire()
		
		self._connection_counter += 1
		server = Server(self._connection_counter, name, thread_count)
		self._servers[self._connection_counter] = server
		
		self._server_lock.release()
		return server
		
	def getServer(self, id_number):
		"""
		This function will retrieve the specified Server from the pool.
		
		@type id_number: int
		@param id_number: An int containing the number of the server to be
		    retrieved.
		
		@rtype: Server|None
		@return: The requested Server object, or None if the server could not
		    be found.
		"""
		try:
			self._server_lock.acquire()
			return self._servers.get(id_number)
		finally:
			self._server_lock.release()
			
	def getServers(self):
		"""
		This function will return a list of all Servers in the pool.
		
		@rtype: list
		@return: A list containing all Servers in the pool, ordered by ID.
		"""
		self._server_lock.acquire()
		
		servers = []
		for i in sorted(self._servers.keys()):
			servers.append(self._servers[i])
			
		self._server_lock.release()
		return servers
		
	def removeServer(self, id_number):
		"""
		This function will remove the specified Server from the pool.
		
		@type id_number: int
		@param id_number: An int containing the number of the server to be
		    removed.
		
		@return: Nothing.
		"""
		self._server_lock.acquire()
		
		server = self._servers.get(id_number)
		if server:
			server.close()
			del self._servers[id_number]
			
		self._server_lock.release()
		
		
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
		
class ReconnectionError(Error):
	"""
	This class represents problems that might occur when attempting to reconnect
	to a server.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new ReconnectionError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		Error.__init__(self, description)
		