"""
PyRC module: pyrc_irc_abstract.resources.autocompletion

Purpose
=======
 Provide support for PyRC's dynamic tab-completion functionality.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
import os
import os.path

import pyrc_common.GLOBAL as GLOBAL

class Tree(object):
	"""
	This class represents an autocompletion tree, an object that contains a tree
	of autocompletion _Nodes.
	"""
	_nodes = None #: A dictonary that contains all of this node's children, keyed by value.
	_is_terminus = False #: True if this node represents a viable endpoint, used to allow nodes to both be leaves and have children.
	
	def __init__(self):
		"""
		This function is invoked when a new Tree object is created.
		
		@return: Nothing.
		"""
		self._nodes = {}
		
	def addTokens(self, tokens):
		"""
		This function is used to fill the node tree with valid grammars.
		
		At each stage, the head token will be checked against the current node's
		children to see if there is a match.
		
		If there is, the matching child	will be given all remaining tokens, and
		this process will repeat. If there isn't, a new child will be created,
		and it will be given all remaining tokens, continuing this process.
		
		At the end of the token list, the active node will be declared a
		terminal node, meaning that it is a valid ending point for completion
		requests.
		
		@type tokens: tuple
		@param tokens: A list of tokens that represent the structure of strings
		    that may be completed.
		
		@return: Nothing.
		"""
		if tokens:
			head = tokens[0].upper()
			node = self._nodes.get(head)
			if node:
				node.addTokens(tokens[1:])
			else:
				if head == "%C":
					self._nodes[head] = _ChannelNode(tokens)
				elif head == "%F":
					self._nodes[head] = _FileNode(tokens)
				elif head == "%P":
					self._nodes[head] = _PluginNode(tokens)
				elif head == "%U":
					self._nodes[head] = _UserNode(tokens)
				else:
					self._nodes[head] = _Node(tokens)
		else:
			self._is_terminus = True
			
	def getTokens(self, tokens, irc_context, focus, irc_servers):
		"""
		This function is used to get a list of all tokens that fit at the end of
		the given token list.
		
		If the final token provided is the empty string, all matches that can
		follow the second-last token will be returned. Else, all valid
		completions of the last token will be returned.
		
		If the token list is empty, all values from all children will be
		returned. This is equivalent to passing in a list containing only the
		empty string.
		
		@type tokens: tuple
		@param tokens: A list of tokens that represent the string to be
		    completed.
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type focus: basestring|None
		@param focus: The name of the channel or user (in the case of a query)
		    that the user is currently interacting with.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: tuple
		@return: A list of all valid token matches. () means that no matches
		    could be found.
		"""
		if len(tokens) > 1: #Still resolving the token's nodes.
			node = self._nodes.get(tokens[0].upper())
			if node:
				return node.getTokens(tokens[1:])
			else:
				node = self._nodes.get("%U") #Test for users.
				if node and node.validateUser(tokens[0].lower(), irc_context, focus, irc_servers):
					return node.getTokens(tokens[1:])
					
				node = self._nodes.get("%C") #Test for channels.
				if node and node.validateChannel(tokens[0].lower(), irc_context, focus, irc_servers):
					return node.getTokens(tokens[1:])
					
				node = self._nodes.get("%F") #Test for files.
				if node and node.validateFile(tokens[0]):
					return node.getTokens(tokens[1:])
					
				node = self._nodes.get("%P") #Test for plugins.
				if node and node.validatePlugin(tokens[0]):
					return node.getTokens(tokens[1:])
					
				return () #No matches possible; search failed.
		else:
			if not tokens: #The plugin sent an empty string. Assume it's a request for a new token.
				tokens = ('')
				
			matches = []
			if self._is_terminus and not tokens[0]: #Only trigger if the user did not provide input.
				matches.append('')
				
			for i in sorted(self._nodes.keys()):
				matches += self._nodes[i].getMatches(tokens[0], irc_context, focus, irc_servers)
				
			return tuple(matches)
			
			
class _Node(Tree):
	"""
	This class defines a node, an object that may contain many nodes and
	represent a leaf.
	"""
	_value = None #: The value of this node for generation purposes.
	
	def __init__(self, tokens):
		"""
		This function is invoked when a new Node object is created.
		
		During this function, the head token will be stored as the node's value,
		and all remaining tokens will be recursively added as children. (This
		function uses addTokens() to handle this generation to avoid duplicating
		logic)
		
		@type tokens: tuple
		@param tokens: A list of tokens that represent the structure of strings
		    that may be completed.
		
		@return: Nothing.
		"""
		self._nodes = {}
		self._value = tokens[0].upper()
		
		self.addTokens(tokens[1:])
		
	def getMatches(self, fragment, irc_context, focus, irc_servers):
		"""
		This function is used to get all matches associated with the node's
		value, given a token fragment.
		
		If any possible values match the fragment, they will be returned as part
		of a list.
		
		@type fragment: basestring
		@param fragment: The token fragment with which to search for matches.
		@type irc_context: int
		@param irc_context: This parameter is not used.
		@type focus: basestring|None
		@param focus: This parameter is not used.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: This parameter is not used.
		
		@rtype: list
		@return: A list of all valid token matches.
		"""
		if self._value.startswith(fragment):
			return [self._value]
		return []
		
		
class _ChannelNode(_Node):
	def getMatches(self, fragment, irc_context, focus, irc_servers):
		"""
		This function is used to get all matches associated with the node's
		value, given a token fragment.
		
		If any possible values match the fragment, they will be returned as part
		of a list.
		
		@type fragment: basestring
		@param fragment: The token fragment with which to search for matches.
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type focus: basestring|None
		@param focus: The name of the channel or user (in the case of a query)
		    that the user is currently interacting with.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: list
		@return: A list of all valid token matches.
		"""
		values = []
		fragment = fragment.lower()
		
		if focus and focus[0] in GLOBAL.IRC_CHANNEL_PREFIX: #The current context should take precedence.
			focus = focus.lower()
			if focus.startswith(fragment):
				values.append(focus)
				
		for i in sorted(self._getChannelNames(irc_context, irc_servers)):
			if i.startswith(fragment) and not i == focus:
				values.append(i)
				
		return values
		
	def validateChannel(self, token, irc_context, focus, irc_servers):
		"""
		This function is used to determine whether a given token represents a
		channel in the current context.
				
		@type token: basestring
		@param token: The token to evaluate against possible channel names.
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type focus: basestring|None
		@param focus: The name of the channel or user (in the case of a query)
		    that the user is currently interacting with.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: bool
		@return: True if the given token is a channel in the current context.
		"""
		if focus and focus[0] in GLOBAL.IRC_CHANNEL_PREFIX and token == focus.lower():
			return True
		return token in self._getChannelNames(irc_context, irc_servers)
		
	def _getChannelNames(irc_context, irc_servers):
		"""
		This function is used to get a list of all known channel names on the
		specified IRC network.
		
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: tuple
		@return: A list of all channel names.
		"""
		return irc_servers.getServer(irc_context).getChannelManager.getChannelNames()
		
		
class _FileNode(_Node):
	def getMatches(self, fragment, irc_context, focus, irc_servers):
		"""
		This function is used to get all matches associated with the node's
		value, given a token fragment.
		
		If any possible values match the fragment, they will be returned as part
		of a list.
		
		@type fragment: basestring
		@param fragment: The token fragment with which to search for matches.
		@type irc_context: int
		@param irc_context: This parameter is not used.
		@type focus: basestring|None
		@param focus: This parameter is not used.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: This parameter is not used.
		
		@rtype: list
		@return: A list of all valid token matches.
		"""
		values = []
		
		(path, file) = os.path.split(os.path.expanduser(fragment))
		if os.path.isdir(path):
			for i in os.listdir(dir):
				if i.startswith(file):
					path = os.path.join(path, i)
					if os.path.isdir(path):
						path += os.sep
					values.append(path)
					
		return values
		
	def validateFile(self, token):
		"""
		This function is used to determine whether a given token represents a
		file.
		
		@type token: basestring
		@param token: The token to evaluate against the filesystem.
		
		@rtype: bool
		@return: True if the given token is a filepath.
		"""
		return os.path.exists(token)
		
		
class _PluginNode(_Node):
	def getMatches(self, fragment, irc_context, focus, irc_servers):
		"""
		This function is used to get all matches associated with the node's
		value, given a token fragment.
		
		If any possible values match the fragment, they will be returned as part
		of a list.
		
		@type fragment: basestring
		@param fragment: The token fragment with which to search for matches.
		@type irc_context: int
		@param irc_context: This parameter is not used.
		@type focus: basestring|None
		@param focus: This parameter is not used.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: This parameter is not used.
		
		@rtype: list
		@return: A list of all valid token matches.
		"""
		return [i for i in GLOBAL.plugin.listAllPlugins() if i.startswith(fragment)]
		
	def validatePlugin(self, token):
		"""
		This function is used to determine whether a given token represents a
		plugin.
		
		@type token: basestring
		@param token: The token to evaluate against the plugin list.
		
		@rtype: bool
		@return: True if the given token is a plugin.
		"""
		return token in GLOBAL.plugin.listAllPlugins()
		
		
class _UserNode(_Node):
	def getMatches(self, fragment, irc_context, focus, irc_servers):
		"""
		This function is used to get all matches associated with the node's
		value, given a token fragment.
		
		If any possible values match the fragment, they will be returned as part
		of a list.
		
		@type fragment: basestring
		@param fragment: The token fragment with which to search for matches.
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type focus: basestring|None
		@param focus: The name of the channel or user (in the case of a query)
		    that the user is currently interacting with.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: list
		@return: A list of all valid token matches.
		"""
		values = []
		
		if focus: #Without focus, every user known to exist on the server would be returned.
			if focus[0] in GLOBAL.IRC_CHANNEL_PREFIX:
				fragment = fragment.lower()
				
				users = self._getUsers(irc_context, focus, irc_servers)
				for i in sorted(users.keys()):
					if i.startswith(fragment):
						values.append(users[i]['username'])
			else: #The focus is a query; logically, the target is the other user.
				if focus.startswith(fragment):
					values.append(focus)
					
		return values
		
	def validateUser(self, token, irc_contect, channel, irc_servers):
		"""
		This function is used to determine whether a given token represents a
		user in the current context.
				
		@type token: basestring
		@param token: The token to evaluate against possible usernames.
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type focus: basestring|None
		@param focus: The name of the channel or user (in the case of a query)
		    that the user is currently interacting with.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: bool
		@return: True if the given token is a user in the current context.
		"""
		if focus and focus[0] not in GLOBAL.IRC_CHANNEL_PREFIX and token == focus.lower():
			return True
		return token in self._getUsers(irc_context, channel, irc_servers)
		
	def _getUsers(irc_context, channel, irc_servers):
		"""
		This function is used to get all known user names in the specified
		channel.
		
		@type irc_context: int
		@param irc_context: The session-unique ID of the IRC server to use for
		    dynamic content.
		@type channel: basestring
		@param channel: The name of the channel that the user is currently
		    interacting with.
		@type irc_servers: pyrc_irc_abstract.irc_server.ServerManager
		@param irc_servers: A reference to the ServerManager that maintains all
		    active Server objects.
		
		@rtype: dict
		@return: A dictionary of user data dictionaries, keyed by lowercase
		    username.
		"""
		return irc_servers.getServer(irc_context).getChannel(channel).getUsersData()
		
