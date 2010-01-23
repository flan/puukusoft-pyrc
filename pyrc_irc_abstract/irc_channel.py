# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.irc_channel

Purpose
=======
 Maintain data related to all channels PyRC is in on an IRC server.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""

import threading

import irc_user

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.dictionaries.information as informationDictionaries
#The following dictionaries are used by this module:
##Channel Data
##User Data

class _UserContainer(object):
	"""
	This class defines the basic functionality that a user container must
	satisfy for use by PyRC.
	
	This class is useless on its own, so it should not be instantiated.
	Instantiate Channel or SimpleUserContainer instead.
	"""
	_server = None #: A reference to the irc_server.Server that owns this object.
	
	def __init__(self, server):
		"""
		This function is invoked when a new _UserContainer object is created.
		
		@type server: irc_server.Server
		@param server: A reference to the irc_server.Server that owns this object.
		
		@return: Nothing.
		"""
		self._server = server
		
	def addUsers(self, nicknames):
		"""
		This function takes a list of raw nicknames, extracts symbol data, looks
		for matches in the server's pool, and stores all the information it can
		find.
		
		@type nicknames: list
		@param nicknames: A list of raw nickname strings. These may be
		    symbol-prefixed.
		
		@return: Nothing.	
		"""
		pass
		
	def getUsersData(self):
		"""
		This function returns a dictionary of dictionaries containing information
		about users.
		
		@rtype: dict
		@return: A dictionary of dictionaries of the form returned by
		    common.dictionaries.information.User_Data().
		    
		    The elements of this dictionary are keyed by lower-case username.
		"""
		pass
		
		
class Channel(_UserContainer):
	"""
	This class represents a channel on an IRC server.
	
	It is only instantiated	as a child of server objects.
	"""
	_mode_lock = None #: A lock used to prevent multiple simultaneous accesses to the mode pool.
	_topic_lock = None #: A lock used to prevent multiple simultaneous accesses to the channel's topic.
	_name = None #: A string containing the name of this channel.
	_password = None #: A string containing the password of the channel, if any.
	_topic = None #: A string containing the topic of this channel.
	_modes = None #: A list of modes attached to this channel. Elements may be unicodes or tuples(2).
	_user_manager = None #: The pyrc_irc_abstract.irc_user.UserManagerChannel object this channel uses to manage its users.
	
	def __init__(self, server, channel_name, password=None):
		"""
		This function is invoked when creating a new Channel object.
		
		@type server: pyrc_irc_abstract.irc_server.Server
		@param server: A reference to the server object that owns this channel.
		@type channel_name: basestring
		@param channel_name: The name of the channel this object represents.
		@type password: basestring|None
		@param password: The password used to join the channel, if any.
		
		@return: Nothing.
		"""
		self._mode_lock = threading.Lock()
		self._topic_lock = threading.Lock()
		self._modes = []
		
		self._name = unicode(channel_name)
		if password:
			self._password = unicode(password)
			
		_UserContainer.__init__(self, server)
		self._user_manager = irc_user.UserManagerChannel(self)
		
	def close(self):
		"""
		This function will clean up any associations the channel has.
		
		It should be called prior to dereferencing.
		
		@return: Nothing.
		"""
		self._user_manager.emptyPool()
		
	def getData(self):
		"""
		This function returns a dictionary containing all information known about
		the channel and its users.
		
		@rtype: dict
		@return: A dictionary of the format returned by
		    common.dictionaries.information.Channel_Data().
		"""
		return informationDictionaries.Channel_Data(self._name, self.getTopic(), self.getModes(), self.getModeStringFull(), self.getModeStringSafe(), self._user_manager.getUsersData())
		
	#Channel management
	####################################
	def getModes(self):
		"""
		This function returns a copy of the channel's current modes, expressed as
		a tuple.
		
		Members of this tuple are either unicodes or (unicode, unicode) tuples;
		in the case of tuples, the first element is the mode, and the second
		element is its parameter.
		
		@rtype: tuple
		@return: A tuple of the channel's current modes.
		"""
		try:
			self._mode_lock.acquire()
			return tuple(self._modes)
		finally:
			self._mode_lock.release()
			
	def _getModeString(self, tuple_handler):
		"""
		This function will handle generation of a modestring, using a
		call-specific routine for handling tuples.
		
		@type tuple_handler: Function
		@param tuple_handler: A function to be invoked when handling a mode
		    stored as a tuple.
		    
		    It must accept a tuple(2), a modestring, and an paramstring.
		    
		    It must return a tuple(2) that contains the updated modestring and
		    paramstring.
		    
		@rtype: unicode
		@return: A finished modestring containing the channel's current modes.
		"""
		modestring = ""
		paramstring = ""
		self._mode_lock.acquire()
		
		for i in self._modes:
			if type(i) == unicode:
				modestring += i
			else:
				(modestring, paramstring) = tuple_handler(i, modestring, paramstring)
				
		self._mode_lock.release()
		return unicode(modestring + paramstring)
		
	def getModeStringFull(self):
		"""
		This function returns the channel's current modes, expressed as a string.
		
		@rtype: unicode
		@return: A string containing the channel's current modes.
		"""
		def tupleHandler(tuple_in, modestring, paramstring):
			modestring += tuple_in[0]
			if tuple_in[1]:
				paramstring += ' ' + tuple_in[1]
			return modestring, paramstring
			
		return self._getModeString(tupleHandler)
		
	def getModeStringSafe(self):
		"""
		This function returns the channel's current modes, expressed as a string.
		
		However, unline getModeStringFull(), sensitive information, such as the
		channel's key, if present, will be omitted.
		
		@rtype: unicode
		@return: A string containing the channel's current modes.
		"""
		def tupleHandler(tuple_in, modestring, paramstring):
			if not tuple_in[0] == 'k':
				modestring += tuple_in[0]
				if tuple_in[1]:
					paramstring += ' ' + tuple_in[1]
			else:
				modestring = tuple_in[0] + modestring
			return modestring, paramstring
			
		return self._getModeString(tupleHandler)
		
	def getName(self):
		"""
		This function returns the channel's name.
		
		@rtype: unicode
		@return: The channel's name.
		"""
		return self._name
		
	def getPassword(self):
		"""
		This function returns the channel's password, if any.
		
		@rtype: unicode|None
		@return: The channel's password if one was set, or None if no password
		    is set.
		"""
		return self._password
		
	def getServer(self):
		"""
		This function returns a reference to the Server that owns this channel
		object.
		
		@rtype: pyrc_irc_abstract.irc_server.Server
		@return: A reference to the server that owns this channel.
		"""
		return self._server
		
	def getTopic(self):
		"""
		This function returns the channel's current topic.
		
		@rtype: unicode
		@return: The channel's current topic.
		"""
		try:
			self._topic_lock.acquire()
			return self._topic
		finally:
			self._topic_lock.release()
			
	def setModes(self, modes):
		"""
		This function sets the channel's modes to an arbitrary list.
		
		@type modes: list
		@param modes: A list of tuples(2), each one representing a mode.
		    
		    The first element is always the mode represented.
		    The second element, however, is an optional parameter.
		    Both elements are basestrings.
		
		@return: Nothing.
		"""
		self._mode_lock.acquire()
		
		mode_list = []
		for i in modes:
			if i[1]:
				mode_list.append((unicode(i[0]), unicode(i[1])))
				if i[0] == 'k':
					self._password = unicode(i[1])
			else:
				mode_list.append(unicode(i[0]))
				
		mode_list.sort()
		self._modes = mode_list
		
		self._mode_lock.release()
		
	def setTopic(self, channel_topic):
		"""
		This function sets the channel's topic.
		
		@type channel_topic: basestring
		@param channel_topic: The new topic for the channel.
		
		@return: Nothing.
		"""
		self._topic_lock.acquire()
		
		self._topic = unicode(channel_topic)
		
		self._topic_lock.release()
		
	def updateModes(self, modes):
		"""
		This function is used to update the modes of the channel and its users.
		
		@type modes: list
		@param modes: A list of tuples(3) to be processed. These tuples take the
		    following form::
		     (<mode:basestring>, <parameter:basestring|None>, <add:bool>)
		
		@rtype: tuple
		@return: A tuple containing four lists of modes that were changed.
		    This tuple takes the following form::
		     (<added_channel_modes:list>, <removed_channel_modes:list>,
		      <added_user_modes:list>, <removed_user_modes:list>)
		    
		    Each of its channel lists contain tuples of the following form::
		     (<mode:basestring>, <parameter:basestring|None>)
		    
		    Each of its user lists contain tuples of the following form::
		     (<mode:basestring>, <parameter:basestring|None>, <add:bool>)
		"""
		added_channel_modes = []
		removed_channel_modes = []
		added_user_modes = []
		removed_user_modes = []
		for i in modes:
			if i[0] in GLOBAL.IRC_IGNORED_MODES:
				continue
			elif i[0] in GLOBAL.IRC_RANK_ORDER: #The mode is intended for a user.
				self.updateUserStatus(i[1], i[0], i[2])
				if i[2]:
					added_user_modes.append(i)
				else:
					removed_user_modes.append(i)
			elif i[2]: #The mode is being added.
				self._mode_lock.acquire()
				
				add = True
				remove = False
				element_to_remove = None
				added_channel_modes.append(i[:2])
				for j in self._modes:
					if j[0] == i[0]: #The mode was already set.
						if j[1] == i[1]: #And the parameter hasn't changed
							add = False
						else: #The paramater is changing, so remove the old mode.
							remove = True
							element_to_remove = j
						break
				if remove:
					self._modes.remove(element_to_remove)
				if add:
					if not i[1]:
						self._modes.append(unicode(i[0]))
					else:
						self._modes.append((unicode(i[0]), unicode(i[1])))
						if i[0] == 'k':
							self._password = unicode(i[1])
							
				self._mode_lock.release()
			else: #The mode is being removed.
				self._mode_lock.acquire()
				
				removed_channel_modes.append(i[:2])
				for j in self._modes:
					if j[0] == i[0]:
						self._modes.remove(j)
						break
						
				self._mode_lock.release()
		self._mode_lock.acquire()
		
		self._modes.sort()
		
		self._mode_lock.release()
		return (added_channel_modes, removed_channel_modes, added_user_modes, removed_user_modes)
		
	#User managerment
	####################################
	def addUser(self, nickname, ident=None, hostmask=None):
		"""
		This function adds a new user to the channel.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be added.
		@type ident: basestring|None
		@param ident: The ident of the user, if available.
		@type hostmask: basestring|None
		@param hostmask: The hostmask of the user, if available.
		
		@return: Nothing.
		"""
		self._user_manager.addUser(nickname, ident, hostmask)
		
	def addUsers(self, nicknames):
		"""
		This function adds a list of users to the channel; it is typically called
		when PyRC is joining.
		
		@type nicknames: list
		@param nicknames: A list of basestrings representing the users in the
		    channel.
		
		@return: Nothing.
		"""
		for i in nicknames:
			self.addUser(i)
			
	def getUser(self, nickname):
		"""
		This function retrieves a User object from the channel.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be retrieved.
		
		@rtype: User|None
		@return: The User associated with the given nickname, or None if the user
		    could not be found.
		"""
		return self._user_manager.getUser(nickname)
		
	def getUserData(self, nickname):
		"""
		This function retrieves the channel-specific "User Data" dictionary
		associated with a user.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@type nickname: basestring
		@param nickname: The nickname of the user for which data is to be
		    retrieved.
		
		@rtype: dict|None
		@return: A channel-specific dictionary of the form returned by
		    User.getData(), or None if the user could not be found.
		"""
		return self._user_manager.getUserData(nickname)
		
	def getUsersData(self):
		"""
		This function retrieves the channel-specific "User Data" dictionaries
		associated with all users in the channel.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@rtype: dict
		@return: A dictionary of dictionaries of the form returned by
		    User.getData(). The containing dictionary takes the following form::
		     {
		      <nickname:unicode>: <User_Data:dictionary>
		     }
		     
		    The nicknames used as keys are all lower-case.
		"""
		return self._user_manager.getUsersData()
		
	def removeUser(self, nickname):
		"""
		This function removes a user from this channel.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be removed.
		
		@return: Nothing.
		"""
		self._user_manager.removeUser(nickname)
		
	def updateUserStatus(self, nickname, status, grant):
		"""
		This function sets a status modifier on a user in the channel.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@type nickname: basestring
		@param nickname: The nickname of the user whose status is being modified.
		@type status: basestring
		@param status: The status being modified.
		    
		    This string must be exactly one character long.
		@type grant: bool
		@param grant: True if the user is gaining the specified status; False if
		    The user is being stripped.
		    
		@return: Nothing.
		"""
		self._user_manager.updateChannelStatus(nickname, status, grant)
		
	def userNicknameChange(self, old_nickname, new_nickname):
		"""
		This function updates the the nickname of a user in the channel.
		
		This function's logic and persistence have been exported to this
		channel's UserManagerChannel object.
		
		@type old_nickname: basestring
		@param old_nickname: The nickname the user was previously using.
		@type new_nickname: basestring
		@param new_nickname: The nickname the user is now using.
		
		@return: Nothing.
		"""
		self._user_manager.updateUserNickname(old_nickname, new_nickname)
		
	def passChannelMessage(self, user_data):
		"""
		This function updates information about a user who acted in a channel.
		
		@type user_data: tuple
		@param user_data: A tuple of the following form::
		     (<nickname:basestring>, <ident:basestring>, <hostmask:basestring>)
		
		@return: Nothing.
		"""
		user = self._user_manager.getUser(user_data[0])
		if user:
			user.updateLastEvent(self)
			user.setIdentity(user_data[1], user_data[2])
			
			
class SimpleUserContainer(_UserContainer):
	"""
	This class provides a skeleton for Channel-like user aggregation.
	
	It is required for gathering information about users in channels that PyRC
	has not joined.
	"""
	_users = None #: A dictionary of dictionaries of the form returned by common.dictionaries.information.User_Data(). These are keyed by lower-case username.
	
	def __init__(self, server):
		"""
		This function is invoked when a new SimpleUserContainer object is
		created.
		
		@type server: irc_server.Server
		@param server: A reference to the irc_server.Server that owns this object.
		
		@return: Nothing.
		"""
		self._users = {}
		
		_UserContainer.__init__(self, server)
		
	def addUsers(self, nicknames):
		"""
		This function takes a list of raw nicknames, extracts symbol data, looks
		for matches in the server's pool, and stores all the information it can
		find in a temporary container.
		
		@type nicknames: list
		@param nicknames: A list of raw nickname strings. These may be
		    symbol-prefixed.
		
		@return: Nothing.		
		"""
		for i in nicknames:
			nickname = unicode(i)
			
			#Pop every relevant mode from the user's token.
			modes = []
			for j in range(len(nickname)):
				if nickname[j] in GLOBAL.IRC_RANK_PREFIX:
					modes.append(nickname[j])
				else:
					nickname = nickname[j:]
					break
					
			symbol = None
			for j in GLOBAL.IRC_RANK_ORDER:
				if j in modes:
					symbol = j
					break
					
			user_data = None
			user = self._server.getUser(nickname)
			if user:
				user_data = user.getData()
				user_data['symbol'] = symbol
			else:
				user_data = informationDictionaries.User_Data(nickname, None, None, None, None, None, None, None, symbol)
				
			self._users[nickname.lower()] = user_data
			
	def getUsersData(self):
		"""
		This function returns a dictionary of dictionaries containing information
		about users.
		
		@rtype: dict
		@return: A dictionary of dictionaries of the form returned by
		    common.dictionaries.information.User_Data().
		    
		    The elements of this dictionary are keyed by lower-case username.
		"""
		return self._users
		
		
class ChannelManager(object):
	"""
	This class maintains a server-specific list of channels.
	"""
	_channel_lock = None #: A lock used to prevent multiple simultaneous accesses to the channel pool.
	_server = None #: The pyrc_irc_abstract.irc_server.Server to which this object belongs.
	_channels = None
	"""
	A dictionary containing a list of all channels managed by this object.
	
	Its elements take the following form::
	 {
	  <channel_name:unicode>: <:Channel>
	 }
	"""
	
	def __init__(self, server):
		"""
		This function is invoked when creating a new ChannelManager object.
		
		@type server: pyrc_irc_abstract.irc_server.Server
		@param server: A reference to the server that owns this object.
		
		@return: Nothing.
		"""
		self._channel_lock = threading.Lock()
		self._channels = {}
		
		self._server = server
		
	def addChannel(self, channel_name, password=None):
		"""
		This function creates a blank Channel object.
		
		@type channel_name: basestring
		@param channel_name: A string containing the name of the channel to be
		    added.
		@type password: basestring|None
		@param password: The password required to join the channel, if any.
		
		@return: Nothing.
		"""
		#Sanitize input
		channel_name = unicode(channel_name).lower()
		self._channel_lock.acquire()
		
		self._channels[channel_name] = Channel(self._server, channel_name, password)
		
		self._channel_lock.release()
		
	def emptyPool(self):
		"""
		This function disassociates every channel managed by this object from the
		server to which it is parented.
		
		@rtype: tuple
		@return: A list of channel names as unicodes.
		"""
		self._channel_lock.acquire()
		
		channel_names = self._channels.keys()
		for i in channel_names:
			self._channels[i].close()
		self._channels = {}
		
		self._channel_lock.release()
		channel_names.sort()
		return tuple(channel_names)
		
	def getChannel(self, channel_name):
		"""
		This function will retrieve the specified Channel from the pool.
		
		@type channel_name: basestring
		@param channel_name: A string containing the name of the channel to be
		    retrieved.
		
		@rtype: Channel|None
		@return: The requested Channel object, or None if the channel could not
		    be found.
		"""
		#Sanitize input
		channel_name = unicode(channel_name).lower()
		try:
			self._channel_lock.acquire()
			return self._channels.get(channel_name)
		finally:
			self._channel_lock.release()
			
	def getChannelNames(self):
		"""
		This function will return the names of all managed channels.
		
		@rtype: tuple
		@return: The names of all managed channels as unicodes.
		"""
		self._channel_lock.acquire()
		
		channel_names = self._channels.keys()
		
		self._channel_lock.release()
		channel_names.sort()
		return tuple(channel_names)
		
	def getChannelsData(self):
		"""
		This function will retrieve the data of each channel in the pool.
		
		@rtype: dict
		@return: A dictionary containing Channel Information dictionaries, keyed
		    by channel name.
		"""
		channels_data = {}
		
		self._channel_lock.acquire()
		
		for i in self._channels:
			channels_data[i.getName()] = i.getData()
			
		self._channel_lock.release()
		return channels_data
		
	def removeChannel(self, channel_name):
		"""
		This function will remove the specified Channel from the pool.
		
		@type channel_name: basestring
		@param channel_name: A string containing the name of the channel to be
		    removed.
		
		@return: Nothing.
		"""
		#Sanitize input
		channel_name = unicode(channel_name.lower())
		self._channel_lock.acquire()
		
		channel = self._channels.get(channel_name)
		if channel:
			channel.close()
			del self._channels[channel_name]
			
		self._channel_lock.release()
		