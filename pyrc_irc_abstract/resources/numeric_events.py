# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.resources.numeric_events

Purpose
=======
 Handle numbered IRC events.
 This module provides an implementation for a subset of the client-side
 protocol defined in RFC 1459 (http://www.faqs.org/rfcs/rfc1459.html).
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2005-2007
"""
import re

import tld_table
import user_functions
import common

import pyrc_common.GLOBAL as GLOBAL

import pyrc_common.dictionaries.information as informationDictionaries
#The following dictionaries are used by this module:
##User Data

import pyrc_common.dictionaries.outbound as outboundDictionaries
#The following dictionaries are used by this module:
##IRC Channel Banlist
##IRC Channel Created
##IRC Channel Information
##IRC Channel Join
##IRC Channel Modes
##IRC Channel Names
##IRC Channel Topic
##IRC Channel Topic Information
##IRC IsOn Response
##IRC Object Information
##IRC Raw Event
##IRC User Logon
##IRC Who Fail
##IRC Who Response
##IRC WhoIs Response
##IRC WhoWas Fail
##IRC WhoWas Response
##PyRC Implement Me
##Server Information
##Server Message
##Server MOTD
##Server Welcome

_COLON_PARSER = re.compile('(?:(^| ):.+?)') #: A regexp used to strip the token-endpoint-marking colon.

def _serverMessage(server, raw_string, code, server_url, target, data):
	"""
	This function emits a 'Server Message' dictionary for the given text.
	
	This is used primarily when there is no reason to process the IRC server's
	event, since it is purely informational.
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object that received this event.
	@type raw_string: basestring
	@param raw_string: The string that contains this event.
	@type code: int
	@param code: The numeric code used to identify this event within the IRC
	    protocol.
	@type server_url: basestring
	@param server_url: The URI from which this event originated.
	@type target: basestring
	@param target: The name of the event's target, typically a user or a
	    channel.
	@type data: basestring
	@param data: The payload of the event.
	
	@return: Nothing
	"""
	server.addEvent(outboundDictionaries.Server_Message(server.getContextID(), server.getName(), data))
	
def _generateEvents():
	"""
	This function returns a dictionary of functions mapped to numeric IRC event
	codes.
	
	All stored functions have the same input and output signatures::
	 server:
	  pyrc_irc_abstract.irc_server.Server : A reference to the Server object
	                                        that received the event.
	 raw_string:
	  basestring : The string that contains the event.
	 code:
	  int : The numeric code used to identify this event within the IRC
	        protocol.
	 server_url:
	  basestring : The URI from which this event originated.
	 target:
	  basestring : The name of the event's target, typically a user or a
	               channel.
	 data:
	  basestring : The payload of the event.
	
	 Return:
	 	None : Nothing is returned unless PyRC needs to disconnect.
	 Raise:
	   Varies : An exception is raised if the spec parsing routine fails.
	
	@rtype: dict
	@return: A dictionary of functions keyed by numeric IRC event codes.
	"""
	events = {}
	
	def _001(server, raw_string, code, server_url, target, data): #welcome
		server.setNickname(server.getConnectionData().setAuthenticated())
		name = data.split()[3]
		if name not in ["the", "Internet", "IRC"]:
			server.setName(name)
			
		server.addEvent(outboundDictionaries.Server_Welcome(server.getContextID(), server.getName(), data))
		
		#Request a "WHOIS" to get the local IP.
		server.send("WHOIS :%s" % server.getNickname())
		
		#Join all channels the Server knows about.
		channel_manager = server.getChannelManager()
		for i in channel_manager.getChannelNames():
			password = channel_manager.getChannel(i).getPassword()
			join_string = "JOIN %s" % i
			if password:
				join_string += " %s" % password
			server.send(join_string)
	events[1] = _001
	
	events[2] = _serverMessage #yourhost
	events[3] = _serverMessage #created
	
	def _004(server, raw_string, code, server_url, target, data): #myinfo
		data = data.split()
		server.addEvent(outboundDictionaries.Server_Information(server.getContextID(), server.getName(), data[0], data[1], data[2], data[3]))
	events[4] = _004
	
	events[10] = _serverMessage #statmem
	
	events[251] = _serverMessage #luserclient
	events[252] = _serverMessage #luserop
	events[253] = _serverMessage #luserunknown
	events[254] = _serverMessage #luserchannels
	events[255] = _serverMessage #luserme
	
	events[265] = _serverMessage #n_local
	events[266] = _serverMessage #n_global
	
	events[290] = _serverMessage #helphdr
	
	events[292] = _serverMessage #helptlr
	
	def _301(server, raw_string, code, server_url, target, data): #away
		data = data.split(None, 1)
		server.addEvent(outboundDictionaries.IRC_Object_Information(server.getContextID(), server.getName(), data[0], "%s is away: %s" % (data[0], data[1])))
	events[301] = _301
	
	def _303(server, raw_string, code, server_url, target, data): #ison
		nickname = None
		is_on = False
		if data:
			nickname = data.rstrip()
			is_on = True
			
		server.addEvent(outboundDictionaries.IRC_IsOn_Response(server.getContextID(), server.getName(), is_on, nickname))
	events[303] = _303
	
	def _307(server, raw_string, code, server_url, target, data): #userip
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['registered'].append(data[1])
	events[307] = _307
	
	def _310(server, raw_string, code, server_url, target, data): #whoishelp
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['help'] = data[1]
	events[310] = _310
	
	def _311(server, raw_string, code, server_url, target, data): #whoisuser
		data = data.split(None, 4)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			whois = server.getStash().createWhoIs(data[0])
			
		user = server.getUser(data[0])
		if user:
			user.setIdentity(data[1], data[2])
			user.setRealname(data[4])
			whois['userdata'] = user.getData()
		else:
			whois['userdata'] = informationDictionaries.User_Data(data[0], data[1], data[2], tld_table.tldLookup(data[2]), data[4], None, None, None, None)
	events[311] = _311
	
	def _312(server, raw_string, code, server_url, target, data): #whoisserver
		data = data.split(None, 2)
		if data[-1].isdigit():
			whowas = server.getStash().getWhoWas(data[0])
			if not whowas:
				return
				
			whowas['lastseen'] = data[2][1:]
			whowas['lastserver'] = data[1]
		else:
			whois = server.getStash().getWhoIs(data[0])
			if not whois:
				return
				
			whois['ircserver'] = data[1]
			whois['servername'] = data[2]
	events[312] = _312
	
	def _313(server, raw_string, code, server_url, target, data): #whoisoperator
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if whois:
			whois['operator'] = data[1]
	events[313] = _313
	
	def _314(server, raw_string, code, server_url, target, data): #whowasuser
		data = data.split(None, 4)
		whowas = server.getStash().createWhoWas(data[0])
		whowas['userdata'] = informationDictionaries.User_Data(data[0], data[1], data[2], tld_table.tldLookup(data[2]), data[4][1:], None, None, None, None)
	events[314] = _314
	
	def _315(server, raw_string, code, server_url, target, data): #endofwho
		data = data.split()
		who = server.getStash().completeWho(data[0])
		if who:
			server.addEvent(outboundDictionaries.IRC_User_Who_Response(server.getContextID(), server.getName(), tuple(who['channels']), who['userdata']))
		else:
			server.addEvent(outboundDictionaries.IRC_User_Who_Fail(server.getContextID(), server.getName(), data[0]))
	events[315] = _315
	
	def _316(server, raw_string, code, server_url, target, data): #whoischanop
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['chanop'] = data[1]
	events[316] = _316
	
	def _317(server, raw_string, code, server_url, target, data): #whoisidle
		data = data.split(None, 3)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['idletime'] = (int(data[1]), int(data[2]), data[3])
	events[317] = _317
	
	def _318(server, raw_string, code, server_url, target, data): #endofwhois
		data = data.split()
		whois = server.getStash().completeWhoIs(data[0])
		if whois:
			server.addEvent(outboundDictionaries.IRC_User_WhoIs_Response(server.getContextID(), server.getName(), whois['ircserver'], whois['servername'], whois['idletime'], tuple(whois['channels']), whois['modes'], whois['bot'], whois['chanop'], whois['help'], whois['operator'], tuple(whois['registered']), whois['secure'], tuple(whois['data']), whois['userdata'], whois['address']))
		else: #Note that this will be accompanied by 401.
			server.addEvent(outboundDictionaries.IRC_User_Who_Fail(server.getContextID(), server.getName(), data[0]))
	events[318] = _318
	
	def _319(server, raw_string, code, server_url, target, data): #whoischannels
		data = data.split()
		data[1] = data[1][1:]
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		for i in data[1:]:
			if i[0] in GLOBAL.IRC_CHANNEL_PREFIX + GLOBAL.IRC_RANK_PREFIX:
				whois['channels'].append(i)
	events[319] = _319
	
	def _320(server, raw_string, code, server_url, target, data): #whoisvworld
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['data'].append(data[1])
	events[320] = _320
	
	def _324(server, raw_string, code, server_url, target, data): #channelmodeis
		data = data.split(None, 1)
		channel = server.getChannel(data[0])
		if not channel:
			return
			
		channel.setModes(common.splitModes(data[1]))
		if not server.getStash().getChannel(channel.getName()): #Forward the channel's modes as a separate event.
			server.addEvent(outboundDictionaries.IRC_Channel_Modes(server.getContextID(), server.getName(), channel.getName(), channel.getModeStringFull(), channel.getModeStringSafe(), channel.getModes()))
	events[324] = _324
	
	def _329(server, raw_string, code, server_url, target, data): #channelcreate
		data = data.split(None, 1)
		if server.getStash().getChannel(data[0]):
			channel = server.getChannel(data[0])
			if not channel:
				return
				
			channel_data = server.getStash().completeChannel(channel.getName())
			server.addEvent(outboundDictionaries.IRC_Channel_Join(server.getContextID(), server.getName(), int(data[1]), channel_data['topicwho'], channel_data['topictime'], channel.getData()))
		else: #Forward the channel's create time as an independent event.
			server.addEvent(outboundDictionaries.IRC_Channel_Created(server.getContextID(), server.getName(), data[0].lower(), int(data[1])))
	events[329] = _329
	
	def _332(server, raw_string, code, server_url, target, data): #topic
		data = data.split(None, 1)
		channel = server.getChannel(data[0])
		if not channel:
			return
			
		data = data[1]
		channel.setTopic(data)
		if not server.getStash().getChannel(channel.getName()):
			server.addEvent(outboundDictionaries.IRC_Channel_Topic(server.getContextID(), server.getName(), channel.getName(), data))
	events[332] = _332
	
	def _333(server, raw_string, code, server_url, target, data): #topicinfo
		data = data.split()
		channel = server.getChannel(data[0])
		channel_name = None
		user_data = user_functions.splitUserData(data[1])
		if channel:
			channel_name = channel.getName()
			user_data_full = channel.getUser(user_data[0])
			if user_data_full:
				user_data = user_data_full
		else:
			channel_name = data[0].lower()
			user_data = user_functions.generateUserData(user_data)
			
		channel_data = server.getStash().getChannel(channel_name)
		if channel_data:
			channel_data['topicwho'] = user_data
			channel_data['topictime'] = int(data[2])
		else:
			server.addEvent(outboundDictionaries.IRC_Channel_Topic_Information(server.getContextID(), server.getName(), channel_name, user_data, int(data[2])))
	events[333] = _333
	
	def _335(server, raw_string, code, server_url, target, data): #whoisbot
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['bot'] = data[1]
	events[335] = _335
	
	def _352(server, raw_string, code, server_url, target, data): #whoreply
		#:mistral.il.us.zirc.org 352 PyRC #irpg ~ur_faec ZiRC-4E6BE5E5.cg.shawcable.net snowball.mo.us.zirc.org flan H :0 Red HamsterX
		real_name = data[data.find(':') + 3:]
		data = data.split()
		
		who = server.getStash().createWho(data[4])
		user = server.getUser(data[4])
		last_action = None
		if user:
			user.setIdentity(data[1], data[2])
			user.setRealname(real_name)
			user.setIRCServer(data[3])
			who['userdata'] = user.getData()
		else:
			who['userdata'] = informationDictionaries.User_Data(data[4], data[1], data[2], tldFunctions.tldLookup(data[2]), real_name, data[3], None, None, None)
			
		if not data[0] == "*":
			who['channels'] = [data[0]]
	events[352] = _352
	
	def _353(server, raw_string, code, server_url, target, data): #namreply
		data = data.replace(":", "")
		if len(data) > 1:
			if data[1].startswith('#'): #Some servers might not use the 'target @ channel' format, opting to omit the '@'. In this case, the channel is first.
				data = data.split()
			else: #Discard the '@'.
				data = data.split()[1:]
				
		if data:
			channel_name = data[0].lower()
			data = data[1:]
			if server.getStash().getChannel(channel_name):
				channel = server.getChannel(channel_name)
				if not channel:
					return
					
				channel.addUsers(data)
			else:
				channel = server.getStash().getUserList(channel_name)
				if not channel:
					channel = server.getStash().createUserList(channel_name)
				channel.addUsers(data)
	events[353] = _353
	
	def _366(server, raw_string, code, server_url, target, data): #endofnames
		channel_name = data.split()[0].lower()
		channel = server.getStash().completeUserList(channel_name)
		if server.getStash().getChannel(channel_name):
			server.send("MODE :%s" % channel_name, GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
		else:
			if channel:
				server.addEvent(outboundDictionaries.IRC_Channel_Names(server.getContextID(), server.getName(), channel_name, channel.getUsersData()))
	events[366] = _366
	
	def _367(server, raw_string, code, server_url, target, data): #banlist
		data = data.split()
		banlist = server.getStash().getBanlist(data[0])
		banlist.append(data[1], data[2], int(data[3]))
	events[367] = _367
	
	def _368(server, raw_string, code, server_url, target, data): #endofbanlist
		data = data.split(None, 1)
		channel_name = data[0].lower()
		server.addEvent(outboundDictionaries.IRC_Channel_Banlist(server.getContextID(), server.getName(), channel_name, server.getStash().completeBanlist(channel_name)))
	events[368] = _368
	
	def _369(server, raw_string, code, server_url, target, data): #endofwhowas
		data = data.split()
		whowas = server.getStash().completeWhoWas(data[0])
		if whowas:
			server.addEvent(outboundDictionaries.IRC_User_WhoWas_Response(server.getContextID(), server.getName(), whowas['lastserver'], whowas['lastseen'], whowas['userdata']))
	events[369] = _369
	
	def _372_375(server, raw_string, code, server_url, target, data): #motd, motdstart
		server.getStash().getMOTD().append(data)
	events[372] = _372_375
	events[375] = _372_375
	
	def _376(server, raw_string, code, server_url, target, data): #endofmotd
		motd = server.getStash().completeMOTD()
		if motd:
			server.addEvent(outboundDictionaries.Server_MOTD(server.getContextID(), server.getName(), tuple(motd)))
	events[376] = _376
	
	def _378(server, raw_string, code, server_url, target, data): #whoishost
		data = data.split(None, 1)
		
		if data[0].lower() == server.getNickname().lower():
			ip = re.search(r"(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})", data[1])
			if ip and int(ip.group(1)) <= 255 and int(ip.group(2)) <= 255 and int(ip.group(3)) <= 255 and int(ip.group(4)) <= 255:
				server.setLocalIP('.'.join(ip.groups()))
				
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['address'] = data[1]
	events[378] = _378
	
	def _379(server, raw_string, code, server_url, target, data): #whoishost
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['modes'] = data[1]
	events[379] = _379
	
	def _401(server, raw_string, code, server_url, target, data): #nosuchnick
		data = data.split(None, 1)
		server.addEvent(outboundDictionaries.IRC_Object_Information(server.getContextID(), server.getName(), data[0], data[1]))
	events[401] = _401
	
	def _404_442_473_474_475_477_499(server, raw_string, code, server_url, target, data): #cannotsendtochan,notonchannel,inviteonlychan,bannedfromchan,badchannelkey,needreggednick,notchannelowner
		data = data.split(None, 1)
		server.addEvent(outboundDictionaries.IRC_Object_Information(server.getContextID(), server.getName(), data[0], data[1]))
	events[404] = _404_442_473_474_475_477_499
	
	def _406(server, raw_string, code, server_url, target, data): #wasnosuchnick
		data = data.split()
		server.addEvent(outboundDictionaries.IRC_User_WhoWas_Fail(server.getContextID(), server.getName(), data[0]))
	events[406] = _406
	
	events[412] = _serverMessage #notexttosend
	
	def _421(server, raw_string, code, server_url, target, data): #unknowncommand
		_serverMessage(server, raw_string, code, server_url, target, "Unknown command: %s" % data.split(None, 1)[0])
	events[421] = _421
	
	events[422] = _serverMessage #nomotd
	
	events[431] = _serverMessage #nonicknamegiven
	
	def _433(server, raw_string, code, server_url, target, data): #nicknameinuse
		if server.isConnected():
			data = data.split(None, 1)
			data = "%s (%s)" % (data[1], data[0])
			_serverMessage(server, raw_string, code, server_url, target, data)
		else:
			nickname = server.getConnectionData().getNickname()
			if nickname:
				server.send("NICK :%s" % nickname, GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
			else:
				return ("All nicknames are in use.", False)
	events[433] = _433
	
	events[439] = _serverMessage #targettoofast
	
	def _440(server, raw_string, code, server_url, target, data): #servicesdown
		data = data.split(None, 1)
		_serverMessage(server, raw_string, code, server_url, target, '%s - % s' % (data[0], data[1]))
	events[440] = _440
	
	def _441(server, raw_string, code, server_url, target, data): #usernotinchannel
		data = data.split(None, 2)
		server.addEvent(outboundDictionaries.IRC_Object_Information(server.getContextID(), server.getName(), data[1], "%s is not in %s" % (data[0], data[1])))
	events[441] = _441
	
	events[442] = _404_442_473_474_475_477_499
	
	events[473] = _404_442_473_474_475_477_499
	events[474] = _404_442_473_474_475_477_499
	events[475] = _404_442_473_474_475_477_499
	
	events[477] = _404_442_473_474_475_477_499
	
	events[480] = _serverMessage #cannotknock
	
	def _482(server, raw_string, code, server_url, target, data): #chanoprivsneeded
		(channel, data) = data.split(None, 1)
		server.addEvent(outboundDictionaries.IRC_Channel_Information(server.getContextID(), server.getName(), channel, data))
	events[482] = _482
	
	events[499] = _404_442_473_474_475_477_499
	
	def _600_601_604_605(server, raw_string, code, server_url, target, data): #logon, logoff, nowon, nowoff
		data = data.split()
		type = None
		if code == 600:
			type = u'logon'
		elif code == 601:
			type = u'logoff'
		elif code == 604:
			type = u'nowon'
		elif code == 605:
			type = u'nowoff'
			
		user_data = None
		user = server.getUser(data[0])
		if user:
			user.setIdentity(data[1], data[2])
			user_data = user.getData()
		else:
			user_data = informationDictionaries.User_Data(data[0], data[1], data[2], tld_table.tldLookup(data[2]), None, None, None, None, None)
		server.addEvent(outboundDictionaries.IRC_User_Logon(server.getContextID(), server.getName(), type, int(data[3]), data[4][1:], user_data))
	events[600] = _600_601_604_605
	events[601] = _600_601_604_605
	events[604] = _600_601_604_605
	events[605] = _600_601_604_605
	
	def _671(server, raw_string, code, server_url, target, data): #whoissecure
		data = data.split(None, 1)
		whois = server.getStash().getWhoIs(data[0])
		if not whois:
			return
			
		whois['secure'] = data[1]
	events[671] = _671
	
	events[974] = _serverMessage #notallssl
	
	return events
_events = _generateEvents() #: A dictionary of functions, keyed by event code.
del _generateEvents

def handleIRCEvent(server, server_url, data, raw_string):
	"""
	This function parses and processes a numeric IRC event.
	
	@type server: pyrc_irc_abstract.irc_server.Server
	@param server: A reference to the Server object that received this event.
	@type server_url: basestring
	@param server_url: The URI of the IRC server that sent this event.
	@type data: tuple
	@param data: The raw event string, split into three pieces.
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
	code = int(data[0]) #Store the event code.
	handler = _events.get(code) #Get the function that will handle the event.
	if not handler: #Fail if the function could not be found, informing the user.
		details = _irc_codes.get(code)
		if not details:
			details = "Unknown"
		raw = outboundDictionaries.IRC_Raw_Event(server.getContextID(), server.getName(), raw_string)
		server.addEvent(outboundDictionaries.PyRC_Implement_Me(details, raw))
		return
		
	(target, data) = data[1].split(None, 1) #The event's target, the event's data.
	if data: #This will remove the first colon in the event data to avoid code duplication.
		m = _COLON_PARSER.search(data)
		if m:
			offset = len(m.group(1)) + m.start()
			data = data[:offset] + data[offset + 1:]
			
	try:
		if data:
			data = unicode(data, 'utf-8', 'replace')
		return handler(server, raw_string, code, server_url, target, data)
	except Exception, e:
		import pyrc_common.errlog
		print pyrc_common.errlog.grabTrace()
		print "number: %i" % code
		print "target: %s" % target
		print "data: %s" % data
		raise ProtocolError("Error while processing '%s': %s" % (raw_string, e))
		
_irc_codes = {
 #1: "welcome",
 #2: "yourhost",
 #3: "created",
 #4: "myinfo",
 5: "map",
 6: "mapmore",
 7: "mapend",
 8: "snomask",
 9: "statmemtot",
 #10: "statmem",
 200: "tracelink",
 201: "traceconnecting",
 202: "tracehandshake",
 203: "traceunknown",
 204: "traceoperator",
 205: "traceuser",
 206: "traceserver",
 207: "traceservice",
 208: "tracenewtype",
 209: "traceclass",
 210: "tracereconnect",
 211: "statslinkinfo",
 212: "statscommands",
 213: "statscline",
 214: "statsnline",
 215: "statsiline",
 216: "statskline",
 217: "statsqline",
 218: "statsyline",
 219: "endofstats",
 220: "statsbline",
 221: "umodeis",
 222: "sqline_nick",
 223: "statsgline",
 224: "statstline",
 225: "statseline",
 226: "statsnline",
 227: "statsvline",
 231: "serviceinfo",
 232: "endofservices",
 233: "service",
 234: "servlist",
 235: "servlistend",
 241: "statslline",
 242: "statsuptime",
 243: "statsoline",
 244: "statshline",
 245: "statssline",
 246: "statstline",
 247: "statsgline",
 248: "statsuline",
 249: "statsdebug",
 250: "luserconns",
 #251: "luserclient",
 #252: "luserop",
 #253: "luserunknown",
 #254: "luserchannels",
 #255: "luserme",
 256: "adminme",
 257: "adminloc1",
 258: "adminloc2",
 259: "adminemail",
 261: "tracelog",
 262: "endoftrace",
 263: "tryagain",
 #265: "n_local",
 #266: "n_global",
 271: "silelist",
 272: "endofsilelist",
 275: "statsdline",
 280: "glist",
 281: "endofglist",
 #290: "helphdr",
 291: "helpop",
 #292: "helptlr",
 293: "helphlp",
 294: "helpfwd",
 295: "helpign",
 300: "none",
 #301: "away",
 302: "userhost",
 #303: "ison",
 304: "rpl_text",
 305: "unaway",
 306: "nowaway",
 #307: "userip",
 308: "rulesstart",
 309: "endofrules",
 #310: "whoishelp",
 #311: "whoisuser",
 #312: "whoisserver",
 #313: "whoisoperator",
 #314: "whowasuser",
 #315: "endofwho",
 #316: "whoischanop",
 #317: "whoisidle",
 #318: "endofwhois",
 #319: "whoischannels",
 #320: "whoisvworld",
 321: "liststart",
 322: "list",
 323: "listend",
 #324: "channelmodeis",
 #329: "channelcreate",
 331: "notopic",
 #332: "topic",
 #333: "topicinfo",
 334: "listusage",
 #335: "whoisbot",
 341: "inviting",
 342: "summoning",
 346: "invitelist",
 347: "endofinvitelist",
 348: "exlist",
 349: "endofexlist",
 351: "version",
 #352: "whoreply",
 #353: "namreply",
 354: "whospcrpl",
 361: "killdone",
 362: "closing",
 363: "closeend",
 364: "links",
 365: "endoflinks",
 #366: "endofnames",
 #367: "banlist",
 #368: "endofbanlist",
 #369: "endofwhowas",
 371: "info",
 #372: "motd",
 373: "infostart",
 374: "endofinfo",
 #375: "motdstart",
 #376: "endofmotd",
 377: "motd2",
 #378: "austmotd",
 #379: "whoismodes",
 381: "youreoper",
 382: "rehashing",
 383: "youreservice",
 384: "myportis",
 385: "notoperanymore",
 386: "qlist",
 387: "endofqlist",
 388: "alist",
 389: "endofalist",
 391: "time",
 392: "usersstart",
 393: "users",
 394: "endofusers",
 395: "nousers",
 #401: "nosuchnick",
 402: "nosuchserver",
 403: "nosuchchannel",
 #404: "cannotsendtochan",
 405: "toomanychannels",
 #406: "wasnosuchnick",
 407: "toomanytargets",
 408: "nosuchservice",
 409: "noorigin",
 411: "norecipient",
 #412: "notexttosend",
 413: "notoplevel",
 414: "wildtoplevel",
 416: "querytoolong",
 #421: "unknowncommand",
 #422: "nomotd",
 423: "noadmininfo",
 424: "fileerror",
 425: "noopermotd",
 #431: "nonicknamegiven",
 432: "erroneusnickname",
 #433: "nicknameinuse",
 434: "norules",
 435: "serviceconfused",
 436: "nickcollision",
 437: "bannickchange",
 438: "nicktoofast",
 #439: "targettoofast",
 #440: "servicesdown",
 #441: "usernotinchannel",
 #442: "notonchannel",
 443: "useronchannel",
 444: "nologin",
 445: "summondisabled",
 446: "usersdisabled",
 447: "nonickchange",
 451: "notregistered",
 455: "hostilename",
 459: "nohiding",
 460: "notforhalfops",
 461: "needmoreparams",
 462: "alreadyregistered",
 463: "nopermforhost",
 464: "passwdmismatch",
 465: "yourebannedcreep",
 466: "youwillbebanned",
 467: "keyset",
 468: "invalidusername",
 469: "linkset",
 470: "linkchannel",
 471: "channelisfull",
 472: "unknownmode",
 #473: "inviteonlychan",
 #474: "bannedfromchan",
 #475: "badchannelkey",
 476: "badchanmask",
 #477: "needreggednick",
 478: "banlistfull",
 479: "secureonlychannel",
 #480: "cannotknock",
 481: "noprivileges",
 #482: "chanoprivsneeded",
 483: "cantkillserver",
 484: "ischanservice",
 485: "killdeny",
 486: "htmdisabled",
 489: "secureonlychan",
 491: "nooperhost",
 492: "noservicehost",
 501: "umodeunknownflag",
 502: "usersdontmatch",
 511: "silelistfull",
 513: "nosuchgline",
 513: "badping",
 518: "noinvite",
 519: "admonly",
 520: "operonly",
 521: "listsyntax",
 524: "operspverify",
 #600: "rpl_logon",
 #601: "rpl_logoff",
 602: "rpl_watchoff",
 603: "rpl_watchstat",
 #604: "rpl_nowon",
 #605: "rpl_nowoff",
 606: "rpl_watchlist",
 607: "rpl_endofwatchlist",
 610: "mapmore",
 640: "rpl_dumping",
 641: "rpl_dumprpl",
 642: "rpl_eodump",
 #671: "whoissecure",
 999: "numericerror"
}
"""
This list was originally derived from the Net::IRC Perl module, which is
available at http://sourceforge.net/projects/net-irc/ (GPL)

Its purpose here is to serve as a lookup table for codes that have yet to be
handled.
"""

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
		
