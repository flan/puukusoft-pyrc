# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.dictionaries.information

Purpose
=======
 Maintain a centralized collection of information dictionaries that are used
 with the IAL.
 
 By centralizing this resource, global changes should be easier to enact.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
def Channel_Data(name, topic, modes, modestring, modestring_safe, user_data):
	"""
	This function builds and returns a "Channel Data" information dictionary.
	
	@type name: unicode
	@param name: The channel's name.
	@type topic: unicode
	@param topic: The channel's topic.
	@type modes: tuple
	@param modes: The modes currently set on the channel. These may be unicodes
	    or (<mode:unicode>, <param:unicode>) tuples.
	@type modestring: unicode
	@param modestring: The channel's modestring.
	@type modestring_safe: unicode
	@param modestring_safe: A safe version of the channel's modestring.
	@type user_data: dict
	@param user_data: A dictionary of channel-specific "User Data" dictionaries,
	    keyed by lower-case user nicknames.
	
	@rtype: dict
	@return: A dictionary of the following form::
	     {
	      'channel': <channel_name:unicode>,
	      'topic': <channel_topic:unicode>,
	      'modes': <channel_modes:tuple>,
	      'modestring': <channel_modestring:unicode>,
	      'modestringsafe': <channel_modestring_safe:unicode>,
	      'users': <user_data:dict>
	     }
	"""
	return {
	 'channel': name,
	 'topic': topic,
	 'modes': modes,
	 'modestring': modestring,
	 'modestringsafe': modestring_safe,
	 'users': user_data
	}
	
def Server_Data(context_id, group_name, network_name, address, port, nickname, ident, realname, modes, modestring, channels, last_action, local_ip):
	"""
	This function builds and returns a "Server Data" information dictionary.
	
	@type context_id: int
	@param context_id: The session-unique identifier of the Server.
	@type group_name: unicode|None
	@param group_name: The user-specified name of the network group, used for
	    plugin processing consistency.
	@type network_name: unicode|None
	@param network_name: The name of the IRC network to which the Server is
	    connected.
	@type address: unicode|None
	@param address: The address of the IRC server to which the Server is
	    connected.
	@type port: int|None
	@param port: The post on the IRC server to which the Server is connected.
	@type nickname: unicode
	@param nickname: The nickname currently used by PyRC.
	@type ident: unicode|None
	@param ident: The ident currently used by PyRC.
	@type realname: unicode|None
	@param realname: The real name currently used by PyRC.
	@type modes: tuple
	@param modes: A tuple of modes applied to PyRC by the IRC network.
	    Its elements may be single-character mode tokens or tuples containing
	    a single-character mode token and a single-token parameter.
	@type modestring: unicode
	@param unicode: A string that represents every mode currently set on PyRC.
	@type channels: dict
	@param channels: A dictionary of Channel Data dictionaries, keyed by channel
	    name.
	@type last_action: float
	@param last_action: The number of seconds that have elapsed since the user
	    last acted on the IRC server.
	@type local_ip: unicode
	@param local_ip: The IP address of PyRC, as identified by the user, IRC
	    server, or local TCP/IP, in that order.
	
	@rtype: dict
	@return: A dictionary of the following form::
	 {
	  'irccontext': <:int>,
	  'networkname': <:unicode|None>,
	  'groupname': <:unicode|None>,
	  'username': <:unicode>,
	  'ident': <:unicode>,
	  'realname': <:unicode>,
	  'address': <:unicode>,
	  'port': <:int>,
	  'localip': <:unicode>,
	  'lastaction': <:float>,
	  'modes': <:tuple>,
	  'modestring': <:unicode>,
	  'channels': <:dict>
	 }
	"""
	return {
	 'irccontext': context_id,
	 'networkname': network_name,
	 'groupname': group_name,
	 'username': nickname,
	 'ident': ident,
	 'realname': realname,
	 'address': address,
	 'port': port,
	 'localip': local_ip,
	 'lastaction': last_action,
	 'modes': modes,
	 'modestring': modestring,
	 'channels': channels
	}
	
def User_Data(nickname, ident, hostmask, country, real_name, irc_server, last_action_global, last_action_channel, symbol):
	"""
	This function builds and returns a "User Data" information dictionary.
	
	@type nickname: unicode
	@param nickname: The user's nickname.
	@type ident: unicode|None
	@param ident: The user's ident, if known.
	@type hostmask: unicode|None
	@param hostmask: The user's hostmask, if known.
	@type country: unicode|None
	@param country: The user's country, as identified by a TLD lookup on the
	    hostmask, if known.
	@type real_name: unicode|None
	@param real_name: The user's real name, if known.
	@type irc_server: unicode|None
	@param irc_server: The URL of the IRC server to which the user is connected,
	    if known.
	@type last_action_global: float|None
	@param last_action_global: The time at which the user last performed an
	    action anywhere, if known. Expressed as a UNIX timestamp.
	@type last_action_channel: float|None
	@param last_action_channel: The time at which the user last performed an
	    action in a channel, if known. Expressed as a UNIX timestamp.
	    
	    This parameter may be set only in channel-specific contexts.
	@type symbol: unicode|None
	@param symbol: The dominant rank symbol attached to the user, if any.
	    If not None, its length is always one character.
	    
	    This parameter may be set only in channel-specific contexts.
	
	@rtype: dict
	@return: A dictionary of the following form::
	 {
	  'username': <nickname:unicode>,
	  'ident': <ident:unicode|None>,
	  'hostmask': <hostmask:unicode|None>,
	  'country': <country:unicode|None>,
	  'realname': <real_name:unicode|None>,
	  'ircserver': <irc_server:unicode|None>,
	  'lastactionglobal': <last_action_global:float|None>,
	  'lastactionchannel': <last_action_channel:float|None>,
	  'symbol': <symbol:unicode|None>
	 }
	"""
	return {
	 'username': nickname,
	 'ident': ident,
	 'hostmask': hostmask,
	 'country': country,
	 'realname': real_name,
	 'ircserver': irc_server,
	 'lastactionglobal': last_action_global,
	 'lastactionchannel': last_action_channel,
	 'symbol': symbol
	}
	