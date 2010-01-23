# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.dictionaries.outbound

Purpose
=======
 Maintain a centralized collection of outbound dictionaries that are used
 with the IAL.
 
 By centralizing this resource, global changes should be easier to enact.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2007
"""
def IRC_Channel_Banlist(context_id, network_name, channel, banlist):
	return {
	 'eventname': "Channel Banlist",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'banlist': banlist
	}
	
def IRC_Channel_Close(context_id, network_name, channel, reason, kick, kicker_data):
	return {
	 'eventname': "Channel Close",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'message': reason,
	 'kick': kick,
	 'kicker': kicker_data
	}
	
def IRC_Channel_Created(context_id, network_name, channel_name, time_created):
	return {
	 'eventname': "Channel Created",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel_name,
	 'timestamp': time_created
	}
	
def IRC_Channel_Information(context_id, network_name, channel, message):
	return {
	 'eventname': "Channel Information",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'message': message
	}
	
def IRC_Channel_Invite(context_id, network_name, channel, user_data):
	return {
	 'eventname': "Channel Invite",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'userdata': user_data
	}
	
def IRC_Channel_Join(context_id, network_name, time_created, topic_setter, topic_time, channel_data):
	return {
	 'eventname': "Channel Join",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'timestamp': time_created,
	 'topictime': topic_time,
	 'topicwho': topic_setter,
	 'channeldata': channel_data
	}
	
def IRC_Channel_Message(context_id, network_name, channel, message, action, user_data):
	return {
	 'eventname': "Channel Message",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'message': message,
	 'action': action,
	 'userdata': user_data
	}
	
def IRC_Channel_Message_Local(context_id, network_name, channel, message, action, local_nickname):
	return {
	 'eventname': "Channel Message Local",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'message': message,
	 'action': action,
	 'username': local_nickname
	}
	
def IRC_Channel_Modes(context_id, network_name, channel_name, modestring, modestring_safe, modes):
	return {
	 'eventname': "Channel Modes",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel_name,
	 'modestring': modestring,
	 'modestringsafe': modestring_safe,
	 'modes': modes
	}
	
def IRC_Channel_Modes_Update(context_id, network_name, channel, changes, changestring, usermodes, modes, modestring, modestring_safe, user_data):
	return {
	 'eventname': "Channel Modes Update",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'changes': changes,
	 'changestring': changestring,
	 'usermodes': usermodes,
	 'modestring': modestring,
	 'modestringsafe': modestring_safe,
	 'modes': modes,
	 'userdata': user_data
	}
	
def IRC_Channel_Names(context_id, network_name, channel_name, users):
	return {
	 'eventname': "Channel Names",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel_name,
	 'users': users
	}
	
def IRC_Channel_Topic(context_id, network_name, channel_name, topic):
	return {
	 'eventname': "Channel Topic",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel_name,
	 'topic': topic
	}
	
def IRC_Channel_Topic_Information(context_id, network_name, channel_name, topic_setter, topic_time):
	return {
	 'eventname': "Channel Topic Information",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel_name,
	 'topictime': topic_time,
	 'topicwho': topic_setter
	}
	
def IRC_Channel_Topic_New(context_id, network_name, channel, topic, user_data):
	return {
	 'eventname': "Channel Topic New",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'topic': topic,
	 'userdata': user_data
	}
	
def IRC_Channel_User_Join(context_id, network_name, channel_name, user_data):
	return {
	 'eventname': "Channel User Join",
	 'networkname': network_name,
	 'irccontext': context_id,
	 'channel': channel_name,
	 'userdata': user_data
	}
	
def IRC_Channel_User_Part(context_id, network_name, channel, reason, user_data, kick, kicker_data):
	return {
	 'eventname': "Channel User Part",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channel': channel,
	 'message': reason,
	 'userdata': user_data,
	 'kick': kick,
	 'kicker': kicker_data
	}
	
def IRC_CTCP_Request(context_id, network_name, user_data, target, event_type, data, handled):
	return {
	 'eventname': "CTCP Request",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'target': target,
	 'event': event_type,
	 'data': data,
	 'handled': handled,
	 'userdata': user_data
	}
	
def IRC_CTCP_Response(context_id, network_name, user_data, event_type, data):
	return {
	 'eventname': "CTCP Response",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'event': event_type,
	 'data': data,
	 'userdata': user_data
	}
	
def IRC_IsOn_Response(context_id, network_name, is_on, nickname):
	return {
	 'eventname': "IsOn Response",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'ison': is_on,
	 'username': nickname
	}
	
def IRC_Object_Information(context_id, network_name, object, text):
	return{
	 'eventname': "Object Information",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'object': object,
	 'message': text
	}
	
def IRC_Ping(context_id, network_name, timestring, user_data):
	return {
	 'eventname': "Ping",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'data': timestring,
	 'userdata': user_data
	}
	
def IRC_Ping_Timeout(context_id, network_name, username):
	return {
	 'eventname': "Ping Timeout",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'username': username
	}
	
def IRC_Ping_Timeout_Check(context_id, network_name):
	return {
	 'eventname': "Ping Timeout Check",
	 'irccontext': context_id,
	 'networkname': network_name
	}
	
def IRC_Pong(context_id, network_name, time_elapsed, user_data):
	return {
	 'eventname': "Pong",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'pingtime': time_elapsed,
	 'userdata': user_data
	}
	
def IRC_Raw_Command(context_id, network_name, data):
	return {
	 'eventname': "Raw Command",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'data': data
	}
	
def IRC_Raw_Event(context_id, network_name, data):
	return {
	 'eventname': "Raw Event",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'data': data
	}
	
def IRC_User_Logon(context_id, network_name, type, timestamp, message, user_data):
	return {
	 'eventname': "User Logon",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'type': type,
	 'timestamp': timestamp,
	 'data': text,
	 'userdata': user_data
	}
	
def IRC_User_Modes(context_id, network_name, target, changes, changestring, modes, modestring):
	return {
	 'eventname': "User Modes",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'changes': changes,
	 'changestring': changestring,
	 'modes': modes,
	 'modestring': modestring,
	 'username': target
	}
	
def IRC_User_Notice(context_id, network_name, text, target, user_data):
	return {
	 'eventname': "User Notice",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'text': text,
	 'target': target,
	 'userdata': user_data
	}
	
def IRC_User_Nickname_Change(context_id, network_name, new_nickname, affected_channels, user_data, local_change):
	return {
	 'eventname': "User Nickname Change",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'nickname': new_nickname,
	 'channels': affected_channels,
	 'userdata': user_data,
	 'islocal': local_change
	}
	
def IRC_User_Private_Message(context_id, network_name, message, action, user_data):
	return {
	 'eventname': "Private Message",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'message': message,
	 'action': action,
	 'userdata': user_data
	}
	
def IRC_User_Private_Message_Local(context_id, network_name, username, message, action, local_nickname):
	return {
	 'eventname': "Private Message Local",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'target': username,
	 'message': message,
	 'action': action,
	 'username': local_nickname
	}
	
def IRC_User_Quit(context_id, network_name, reason, channels, user_data):
	return {
	 'eventname': "User Quit",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'message': reason,
	 'channels': channels,
	 'userdata': user_data
	}
	
def IRC_User_Who_Fail(context_id, network_name, username):
	return {
	 'eventname': "Who Fail",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'username': username
	}
	
def IRC_User_Who_Response(context_id, network_name, channels, user_data):
	return {
	 'eventname': "Who Response",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'channels': channels,
	 'userdata': user_data
	}
	
def IRC_User_WhoIs_Response(context_id, network_name, irc_server, server_name, idle_time, channels, modes, bot, chanop, help, operator, registered, secure, data, user_data, address):
	return {
	 'eventname': "WhoIs Response",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'ircserver': irc_server,
	 'servername': server_name,
	 'address': address,
	 'channels': channels,
	 'timeinfo': idle_time,
	 'modes': modes,
	 'bot': bot,
	 'chanop': chanop,
	 'help': help,
	 'operator': operator,
	 'registered': registered,
	 'secure': secure,
	 'data': data,
	 'userdata': user_data
	}
	
def IRC_User_WhoWas_Fail(context_id, network_name, nickname):
	return {
	 'eventname': "WhoWas Fail",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'username': nickname
	}
	
def IRC_User_WhoWas_Response(context_id, network_name, last_server, last_seen, user_data):
	return {
	 'eventname': "WhoWas Response",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'ircserver': last_server,
	 'timestring': last_seen,
	 'userdata': user_data
	}
	
def PyRC_Implement_Me(details, raw):
	return {
	 'eventname': "Implement Me",
	 'details': details,
	 'raw': raw
	}
	
def PyRC_Initialised():
	return {
	 'eventname': "Initialised"
	}
	
def PyRC_Plugin_Crash(details, module_name, plugin_name, plugin_version, dictionary, log_file):
	return {
	 'eventname': "Plugin Crash",
	 'module': module_name,
	 'trace': details,
	 'pluginname': plugin_name,
	 'pluginversion': plugin_version,
	 'event': dictionary,
	 'logfile': log_file
	}
	
def PyRC_Plugin_Disable(module_name, plugin_name, plugin_version):
	return {
	 'eventname': "Plugin Disable",
	 'module': module_name,
	 'pluginname': plugin_name,
	 'pluginversion': plugin_version
	}
	
def PyRC_Plugin_Enable(module_name, plugin_name, plugin_version):
	return {
	 'eventname': "Plugin Enable",
	 'module': module_name,
	 'pluginname': plugin_name,
	 'pluginversion': plugin_version
	}
	
def PyRC_Plugin_Load(module_name, plugin_name, plugin_version):
	return {
	 'eventname': "Plugin Load",
	 'module': module_name,
	 'pluginname': plugin_name,
	 'pluginversion': plugin_version
	}
	
def PyRC_Plugin_Load_Error(module_name, details, log_file):
	return {
	 'eventname': "Plugin Load Error",
	 'module': module_name,
	 'trace': details,
	 'logfile': log_file
	}
	
def PyRC_Plugin_Reload(module_name, plugin_name, plugin_version):
	return {
	 'eventname': "Plugin Reload",
	 'module': module_name,
	 'pluginname': plugin_name,
	 'pluginversion': plugin_version
	}
	
def PyRC_Plugin_Status(plugin_name, plugin_version, text):
	return {
	 'eventname': "Plugin Status",
	 'pluginname': plugin_name,
	 'pluginversion': plugin_version,
	 'message': text
	}
	
def PyRC_Processing_Error(details):
	return {
	 'eventname': "Processing Error",
	 'trace': details
	}
	
def PyRC_Status(text):
	return {
	 'eventname': "PyRC Status",
	 'message': text
	}
	
def PyRC_Time_Signal(timestamp, scale):
	return{
	 'eventname': "Time Signal",
	 'timestamp': timestamp,
	 'scale': scale
	}
	
def Server_Connection_Error(context_id, network_name, description):
	return {
	 'eventname': "Server Connection Error",
	 'irccontext': context_id,
	 'message': description
	}
	
def Server_Connection_Success(context_id, network_name, address, port, nickname, ident, real_name, password, ssl):
	return {
	 'eventname': "Server Connection Success",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'address': address,
	 'port': port,
	 'username': nickname,
	 'ident': ident,
	 'realname': real_name,
	 'password': password,
	 'ssl': ssl
	}
	
def Server_Disconnection(context_id, network_name, reason, local_cause):
	return {
	 'eventname': "Server Disconnection",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'message': reason,
	 'localcause': local_cause
	}
	
def Server_Information(context_id, network_name, server_address, server_version, user_modes, channel_modes):
	return {
	 'eventname': "Server Information",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'serveraddress': server_address,
	 'serverversion': server_version,
	 'usermodes': user_modes,
	 'channelmodes': channel_modes,
	}
	
def Server_Kill(context_id, network_name, user_name, reason, user_data):
	return {
	 'eventname': "Server Kill",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'username': target,
	 'message': reason,
	 'userdata': user_data
	}
	
def Server_Message(context_id, network_name, message):
	return {
	 'eventname': "Server Message",
	 'networkname': network_name,
	 'irccontext': context_id,
	 'message': message
	}
	
def Server_MOTD(context_id, network_name, motd):
	return {
	 'eventname': "Server MOTD",
	 'networkname': network_name,
	 'irccontext': context_id,
	 'motd': motd
	}
	
def Server_Protocol_Error(context_id, network_name, description):
	return {
	 'eventname': "Server Protocol Error",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'message': description
	}
	
def Server_Reconnection_Error(context_id, network_name, description):
	return {
	 'eventname': "Server Reconnection Error",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'message': description
	}
	
def Server_Reconnection_Success(context_id, network_name, address, port, nickname, ident, realname, password, ssl):
	return {
	 'eventname': "Server Reconnection Success",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'address': address,
	 'port': port,
	 'nickname': nickname,
	 'realname': realname,
	 'ident': ident,
	 'password': password,
	 'ssl': ssl
	}
	
def Server_Welcome(context_id, network_name, message):
	return {
	 'eventname': "Server Welcome",
	 'irccontext': context_id,
	 'networkname': network_name,
	 'message': message
	}
	