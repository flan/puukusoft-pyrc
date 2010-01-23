# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.irc_user

Purpose
=======
 Maintain details related to users with which PyRC has come into contact.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import threading
import time

import resources.tld_table

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.dictionaries.information as informationDictionaries
#The following dictionaries are used by this module:
##User Data

class User(object):
	"""
	This class represents a user on an IRC server. It is primarily instantiated
	as a child of channel objects, but since a user can be in more than one
	channel, one object may be referenced several times. 
	"""
	_detail_lock = None #: A lock used to prevent multiple simultaneous accesses to the user's data.
	_hostmask = None #: A string containing the user's hostmask, if known.
	_ident = None #: A string containing the user's ident, if known.
	_irc_server = None #: A string containing the URL of the IRC server to which the user is connected, if known.
	_nickname = None #: A string containing the user's nickname.
	_real_name = None #: A string containing the user's real name, if known.
	_last_action = None #: A float containing the user's last global action as a UNIX timestamp, if known.
	_channels = None
	"""
	A dictionary containing a list of all channels to which this user belongs.
	
	Its elements take the following form::
	 {
	  <channel:pyrc_irc_abstract.irc_channel.Channel>: [
	   <status_modifiers:list>,
	   <dominant_symbol:unicode|None>,
	   <last_action:float|None>
	  ]
	 }
	"""
	
	def __init__(self, nickname, channel):
		"""
		This function is invoked when creating a new user object, which is
		associated with the channel in which the user was first found.
		
		@type nickname: basestring
		@param nickname: The user's nickname.
		@type channel: pyrc_irc_abstract.irc_channel.Channel
		@param channel: The channel in which the user is residing.
		
		@return: Nothing.
		"""
		self._detail_lock = threading.RLock()
		self._channels = {}
		
		self.addChannel(channel)
		self._nickname = unicode(nickname)
		
	def addChannel(self, channel):
		"""
		This function associates the user with a new channel.
		
		@type channel: pyrc_irc_abstract.irc_channel.Channel
		@param channel: The channel with which to associate the user.
		
		@return: Nothing.
		"""
		self._detail_lock.acquire()
		
		self._channels[channel] = [[], None, None]
		
		self._detail_lock.release()
		
	def getChannels(self):
		"""
		This function retrieves a list of all channels in which this user
		resides.
		
		@rtype: tuple
		@return: A tuple of the names of all channels in which this user resides.
		"""
		self._detail_lock.acquire()
		
		channels = []
		for i in self._channels:
			channels.append(i.getName())
			
		channels.sort()
		
		self._detail_lock.release()
		return tuple(channels)
		
	def getData(self, channel=None):
		"""
		This function returns a dictionary containing all information known about
		the user.
		
		@type channel: pyrc_irc_abstract.irc_channel.Channel|basestring|None
		@param channel: The channel for which symbol and last_action_channel data
		    should be retrieved; None if only generic information is required.
		
		@rtype: dict
		@return: A dictionary of the format returned by
		    common.dictionaries.information.User_Data().
		"""
		self._detail_lock.acquire()
		
		last_action = None
		symbol = None
		if channel:
			channel_data = None
			if type(channel) == dict:
				channel_data = self._channels.get(channel)
			else:
				for i, channel_data_temp in self._channels.iteritems():
					if i.getName() == channel:
						channel_data = channel_data_temp
						break
						
			if channel_data:
				last_action = channel_data[2]
				symbol = channel_data[1]
				
		user_data = informationDictionaries.User_Data(self._nickname, self._ident, self._hostmask, resources.tld_table.tldLookup(self._hostmask), self._real_name, self._irc_server, self._last_action, last_action, symbol)
		
		self._detail_lock.release()
		return user_data
		
	def getNickname(self):
		"""
		This function returns the user's nickname.
		
		@rtype: unicode
		@return: The user's nickname.
		"""
		try:
			self._detail_lock.acquire()
			return self._nickname
		finally:
			self._detail_lock.release()
			
	def removeChannel(self, channel):
		"""
		This function disassociates the user from a channel.
		
		@type channel: pyrc_irc_abstract.irc_channel.Channel
		@param channel: The channel to be disassociated.
		
		@rtype: bool
		@return: True if the user is still in at least one other channel, False
		    otherwise.
		"""
		try:
			self._detail_lock.acquire()
			del self._channels[channel]
			return not self._channels == {}
		finally:
			self._detail_lock.release()
			
	def removeUser(self):
		"""
		This function removes the user from all channels.
		
		@return: None
		"""
		self._detail_lock.acquire()
		
		for i in self._channels.keys(): #.keys() prevents iteration errors, since the channel will remove itself from the user.
			i.removeUser(self._nickname)
			
		self._detail_lock.release()
		
	def setIdentity(self, ident, hostmask):
		"""
		This function takes identity data gathered through the IAL and uses it to
		fill in information related to the user's connection
		
		@type ident: basestring|None
		@param ident: The ident of the user, if available.
		@type hostmask: basestring|None
		@param hostmask: The hostmask of the user, if available.
		
		@return: Nothing.
		"""
		self._detail_lock.acquire()
		
		if not self._ident:
			self._ident = unicode(ident)
			
		if not self._hostmask == hostmask:
			self._hostmask = unicode(hostmask)
			
		self._detail_lock.release()
		
	def setRealname(self, real_name):
		"""
		This function takes data gathered through the IAL and uses it to set the
		user's real name.
		
		@type real_name: basestring|None
		@param real_name: The real name of the user, if available.
		
		@return: Nothing.
		"""
		self._detail_lock.acquire()
		
		if not self._real_name:
			self._real_name = unicode(real_name)
			
		self._detail_lock.release()
		
	def setIRCServer(self, irc_server):
		"""
		This function takes data gathered through the IAL and uses it to set the
		IRC server to which the user is connected.
		
		@type irc_server: basestring|None
		@param irc_server: The IRC server to which the user is connected,
		    if available.
		
		@return: Nothing.
		"""
		self._detail_lock.acquire()
		
		if not self._irc_server:
			self._irc_server = unicode(irc_server)
			
		self._detail_lock.release()
		
	def updateChannelStatus(self, channel, status, grant):
		"""
		This function updates the user's rank information within a channel.
		
		@type channel: pyrc_irc_abstract.irc_channel.Channel
		@param channel: The channel in which the user's rank is being modified.
		@type status: basestring
		@param status: The rank being modified (o, h, v...).
		    
		    This parameter must always be exactly one character long.
		@type grant: bool
		@param grant: True if the user is geining the rank; False if the user is
		    being stripped.
		
		@return: Nothing.
		"""
		self._detail_lock.acquire()
		
		channel_data = self._channels[channel]
		status = unicode(status).lower()
		if grant:
			if not status in channel_data[0]:
				channel_data[0].append(status)
		else:
			try:
				channel_data[0].remove(status)
			except:
				pass
				
		#Set the symbol associated with this user in this channel, if the user
		#actually has mode flags.
		channel_data[1] = None
		if channel_data[0]:
			for i in GLOBAL.IRC_RANK_ORDER:
				if i in channel_data[0]:
					channel_data[1] = unicode(GLOBAL.IRC_RANK_MAP[i])
					break
					
		self._detail_lock.release()
		
	def updateLastEvent(self, channel=None):
		"""
		This function updates the user's last action timestamp.
		
		This feature is of use primarily for determining whether a user is around
		when PyRC's user wants to speak with them.
		
		@type channel: pyrc_irc_abstract.irc_channel.Channel|None
		@param channel: The channel in which the user made an action, if any.
		
		@return: Nothing.
		"""
		self._detail_lock.acquire()
		
		self._last_action = int(time.time())
		if channel:
			self._channels[channel][2] = self._last_action
			
		self._detail_lock.release()
		
	def updateNickname(self, new_nickname):
		"""
		This function sets the user's nickname.
		
		It then notifies all channels it resides in of the change.
		
		@type new_nickname: basestring
		@param new_nickname: The user's new nickname.
		
		@return: Nothing
		"""
		self._detail_lock.acquire()
		
		old_nickname = self._nickname
		self._nickname = unicode(new_nickname)
		
		for i in self._channels:
			i.userNicknameChange(old_nickname, new_nickname)
			
		self._detail_lock.release()
		
class UserManagerServer(object):
	"""
	This class maintains a list of all users known to exist on an IRC server.
	
	It provides a centralized means of accessing and updating user data.
	"""
	_user_lock = None #: A lock used to prevent multiple simultaneous accesses to the user pool.
	_users = None
	"""
	A dictionary containing a list of all users managed by this object.
	
	Its elements take the following form::
	 {
	  <nickname:unicode>: <:User>
	 }
	"""
	
	def __init__(self):
		"""
		This function is invoked when a new UserManagerServer object is created.
		
		@return: Nothing.
		"""
		self._user_lock = threading.Lock()
		self._users = {}
	
	def addUser(self, user):
		"""
		This function adds a new user to the pool of managed users.
		
		@type user: User
		@param user: The User object to be added to the pool.
				
		@return: Nothing.
		"""
		self._user_lock.acquire()
		
		self._users[user.getNickname().lower()] = user
		
		self._user_lock.release()
		
	def getUser(self, nickname):
		"""
		This function retrieves a user from the pool that this object manages.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be retrieved.
		
		@rtype: User|None
		@return: The User associated with the given nickname, or None if the user
		    could not be found.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		try:
			self._user_lock.acquire()
			return self._users.get(nickname)
		finally:
			self._user_lock.release()
			
	def getUserData(self, nickname):
		"""
		This function retrieves the channel-non-specific "User Data" dictionary
		associated with a user.
		
		@type nickname: basestring
		@param nickname: The nickname of the user for which data is to be
		    retrieved.
		
		@rtype: dict|None
		@return: A channel-non-specific dictionary of the form returned by
		    User.getData(), or None if the user could not be found.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		self._user_lock.acquire()
		
		user = self._users.get(nickname)
		
		self._user_lock.release()
		if user:
			return user.getData()
		return None
		
	def getUsersData(self):
		"""
		This function retrieves the channel-non-specific "User Data" dictionaries
		associated with all managed users.
		
		@rtype: dict
		@return: A dictionary of dictionaries of the form returned by
		    User.getData(). The containing dictionary takes the following form::
		     {
		      <nickname:unicode>: <User_Data:dictionary>
		     }
		    
		    The nicknames used as keys are all lower-case.
		"""
		self._user_lock.acquire()
		
		user_data = {}
		for i in self._users:
			user_data[i] = self._users[i].getData()
			
		self._user_lock.release()
		return user_data
		
	def removeUser(self, nickname):
		"""
		This function removes a user from the pool.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be removed.
		
		@return: Nothing.
		"""
		#Sanitize input
		nickname = unicode(nickname.lower())
		self._user_lock.acquire()
		
		user = self._users.get(nickname)
		if user:
			del self._users[nickname]
			
		self._user_lock.release()
		
	def updateUserNickname(self, nickname, new_nickname):
		"""
		This function updates the nickname of a user in the pool, and it updates
		the local reference.
		
		@type nickname: basestring
		@param nickname: The nickname by which the user was previously
		    referenced.
		@type new_nickname: basestring
		@param new_nickname: The nickname by which the user will now be
		    referenced.
		    
		@return: Nothing.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		new_nickname = unicode(new_nickname)
		self._user_lock.acquire()
		
		user = self._users.get(nickname)
		if user:
			user.updateNickname(new_nickname)
			del self._users[nickname]
			self._users[new_nickname.lower()] = user
			
		self._user_lock.release()
		
class UserManagerChannel(object):
	"""
	This class maintains a channel-specific list of users known to exist on an
	IRC server.
	
	It provides a convenient means of accessing and updating user data.
	"""
	_user_lock = None #: A lock used to prevent multiple simultaneous accesses to the user pool.
	_channel = None #: The pyrc_irc_abstract.irc_channel.Channel to which this object belongs. 
	_users = None
	"""
	A dictionary containing a list of all users managed by this object.
	
	Its elements take the following form::
	 {
	  <nickname:unicode>: <:User>
	 }
	"""
	
	def __init__(self, channel):
		"""
		This function is invoked when creating a new UserManagerChannel object.
		
		@type channel: pyrc_irc_abstract.irc_channel.Channel
		@param channel: The channel to which this object belongs.
		
		@return: Nothing.
		"""
		self._user_lock = threading.Lock()
		self._users = {}
		
		self._channel = channel
		
	def addUser(self, nickname, ident=None, hostmask=None):
		"""
		This function adds a new user to the pool of managed users.
		
		It uses an existing User object if possible, but it creates a new one if
		necessary.
		
		If a new object is created, it is added to the server's user pool.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be added.
		@type ident: basestring|None
		@param ident: The ident of the user, if available.
		@type hostmask: basestring|None
		@param hostmask: The hostmask of the user, if available.
		
		@return: Nothing.
		"""
		#Sanitize input
		nickname = unicode(nickname)
		self._user_lock.acquire()
		
		#Pop every relevant mode from the user's token.
		modes = []
		for i, token in enumerate(nickname):
			mode = GLOBAL.IRC_RANK_MAP_REVERSE.get(token)
			if mode:
				modes.append(mode)
			else:
				nickname = nickname[i:]
				break
				
		user = self._users.get(nickname.lower())
		if not user:
			server = self._channel.getServer()
			user = server.getUser(nickname)
			if user:
				user.addChannel(self._channel)
			else:
				user = User(nickname, self._channel)
				if ident and hostmask:
					user.setIdentity(ident, hostmask)
				server.addUser(user)
			self._users[nickname.lower()] = user
			
		for i in modes:
			user.updateChannelStatus(self._channel, i, True)
			
		self._user_lock.release()
		
	def emptyPool(self):
		"""
		This function disassociates every user managed by this object from the
		channel to which it is parented.
		
		@return: Nothing
		"""
		self._user_lock.acquire()
		
		for name, user in self._users.iteritems():
			if not user.removeChannel(self._channel):
				self._channel.getServer().removeUser(name)
		self._users = {}
		
		self._user_lock.release()
		
	def getUser(self, nickname):
		"""
		This function retrieves a user from the pool that this object manages.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be retrieved.
		
		@rtype: User|None
		@return: The User associated with the given nickname, or None if the user
		    could not be found.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		try:
			self._user_lock.acquire()
			return self._users.get(nickname)
		finally:
			self._user_lock.release()
			
	def getUserData(self, nickname):
		"""
		This function retrieves the channel-specific "User Data" dictionary
		associated with a user.
		
		@type nickname: basestring
		@param nickname: The nickname of the user for which data is to be
		    retrieved.
		
		@rtype: dict|None
		@return: A channel-specific dictionary of the form returned by
		    User.getData(), or None if the user could not be found.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		self._user_lock.acquire()
		
		user = self._users.get(nickname)
		
		self._user_lock.release()
		if user:
			return user.getData(self._channel)
		return None
		
	def getUsersData(self):
		"""
		This function retrieves the channel-specific "User Data" dictionaries
		associated with all managed users.
		
		@rtype: dict
		@return: A dictionary of dictionaries of the form returned by
		    User.getData(). The containing dictionary takes the following form::
		     {
		      <nickname:unicode>: <User_Data:dictionary>
		     }
		     
		    The nicknames used as keys are all lower-case.
		"""
		self._user_lock.acquire()
		
		user_data = {}
		for i in self._users:
			user_data[i] = self._users[i].getData(self._channel)
			
		self._user_lock.release()
		return user_data
		
	def removeUser(self, nickname):
		"""
		This function disassociates a user from this object's parent channel.
		
		If the user is no longer in any channels, it is also removed from the
		server's user pool.
		
		@type nickname: basestring
		@param nickname: The nickname of the user to be removed.
		
		@return: Nothing.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		self._user_lock.acquire()
		
		user = self._users.get(nickname)
		if user:
			if not user.removeChannel(self._channel):
				#It's possible that the user's nickname is changing, so go with the locked string.
				self._channel.getServer().removeUser(user.getNickname()) 
			del self._users[nickname]
			
		self._user_lock.release()
		
	def updateChannelStatus(self, nickname, status, grant):
		"""
		This function forwards a status update to a user in the pool.
		
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
		user = self.getUser(nickname) #Self-sanitizing/locking
		if user:
			user.updateChannelStatus(self._channel, status, grant)
			
	def updateUserNickname(self, nickname, new_nickname):
		"""
		This function updates the nickname reference of a user in the pool.
		
		It must be invoked after the User object has been updated; see
		User.updateNickname() for details.
		
		@type nickname: basestring
		@param nickname: The nickname by which the user was previously
		    referenced.
		@type new_nickname: basestring
		@param new_nickname: The nickname by which the user will now be
		    referenced.
		    
		@return: Nothing.
		"""
		#Sanitize input
		nickname = unicode(nickname).lower()
		new_nickname = unicode(new_nickname)
		self._user_lock.acquire()
		
		user = self._users.get(nickname)
		if user:
			del self._users[nickname]
			self._users[new_nickname.lower()] = user
			
		self._user_lock.release()
		
