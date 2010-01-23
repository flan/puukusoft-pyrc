# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.irc_interface

Purpose
=======
 Provide a single point of access to the entire IRC layer.
 All servers, and all DCC connections, are to be handled through a Singleton
 instance of this interface.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import sys
import traceback
import time
import threading
import Queue
import random

import irc_server
import resources.autocompletion
import resources.connection

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.G_OBJECTS as G_OBJECTS
import pyrc_common.asynch

import pyrc_control.config.networks
import pyrc_control.config.profiles

import pyrc_common.dictionaries.outbound as outboundDictionaries
#The following dictionaries are used by this module:
##IRC Channel Message Local
##IRC Private Message Local
##PyRC Plugin Crash
##PyRC Processing Error
##PyRC Status
##Server Connection Error
##Server Reconnecttion Error

_event_queue = Queue.Queue(0) #: A queue used to feed the IAL's worker threads.

_irc_servers = irc_server.ServerManager() #: An irc_server.ServerManager object that manages all IRC servers to which PyRC is connected.

_autocompletion_tree = resources.autocompletion.Tree() #: A resources.autocompletion.Tree object used to manage autocompletion grammars.

_time_to_die = False #: True if the IAL should reject all input because PyRC is shutting down.

_registered_commands = [] #: A list of strings identified as commands for tab-completion in supporting UIs.
_registered_commands_lock = threading.Lock() #: A lock used to prevent multiple simultaneous accesses to the registered commands list.

_worker_threads = None #: A tuple of worker threads used to handle requests from the user and plugins.

def initialise(thread_count):
	"""
	This function must be called before the IAL is used; it creates the IAL's
	worker threads and pre-populates its runtime variables.
	
	@type thread_count: int
	@param thread_count: The number of worker threads to be created.
	
	@return: Nothing.
	"""
	worker_threads = []
	for i in range(thread_count):
		worker_thread = G_OBJECTS.WorkerThread(_event_queue, "IAL")
		worker_threads.append(worker_thread)
		worker_thread.start()
		
	global _worker_threads
	_worker_threads = tuple(worker_threads)
	
def _eventGenerator():
	"""
	This function generates all event functions currently supported by PyRC's
	dictionary API.
	
	It will be called once and then deleted.
	
	It returns a dictionary keyed by 'eventname'; this allows the function
	associated with an event dictionary to be retrieved quickly.
	
	@rtype: dict
	@return: A dictionary of event functions that are keyed by 'eventname'.
	"""
	events = {}
	
	def _IRC_Channel_Close(dictionary):
		server = _irc_servers.getServer(dictionary['irccontext'])
		server.send("PART %s :%s" % (dictionary['channel'], dictionary['message']), GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
		server.removeChannel(dictionary['channel'])
		server.addEvent(dictionary)
	events['Channel Close'] = _IRC_Channel_Close
	
	def _IRC_Channel_Join(dictionary):
		join_string = "JOIN %s" % dictionary['channel']
		if dictionary['password']:
			join_string += " %s" % dictionary['password']
			
		_irc_servers.getServer(dictionary['irccontext']).send(join_string)
	events['Channel Join'] = _IRC_Channel_Join
	
	def _IRC_Channel_Message(dictionary):
		message = "PRIVMSG %s :" % dictionary['channel']
		if dictionary['action']:
			message += "\001ACTION %s\001" % dictionary['message']
		else:
			message += dictionary['message']
			
		server = _irc_servers.getServer(dictionary['irccontext'])
		if dictionary['send']:
			server.send(message)
			
		server.addEvent(outboundDictionaries.IRC_Channel_Message_Local(server.getContextID(), server.getName(), unicode(dictionary['channel'].lower()), unicode(dictionary['message']), dictionary['action'], server.getNickname()))
	events['Channel Message'] = _IRC_Channel_Message
	
	def _IRC_CTCP_Request(dictionary):
		if dictionary['data']:
			dictionary['data'] = " %s" % dictionary['data']
		else:
			dictionary['data'] = ''
			
		_irc_servers.getServer(dictionary['irccontext']).send("PRIVMSG %s :\001%s%s\001" % (dictionary['target'], dictionary['event'], dictionary['data']), GLOBAL.ENUM_SERVER_SEND_PRIORITY.AVERAGE)
	events['CTCP Request'] = _IRC_CTCP_Request

	def _IRC_CTCP_Response(dictionary):
		if dictionary['data']:
			dictionary['data'] = " %s" % dictionary['data']
		else:
			dictionary['data'] = ''
			
		_irc_servers.getServer(dictionary['irccontext']).send("NOTICE %s :\001%s%s\001" % (dictionary['user'], dictionary['event'], dictionary['data']), GLOBAL.ENUM_SERVER_SEND_PRIORITY.AVERAGE)
	events['CTCP Response'] = _IRC_CTCP_Response
	
	def _IRC_Emit_Generic(dictionary):
		_event_queue.put(dictionary)
	events['Emit Generic'] = _IRC_Emit_Generic
	
	def _IRC_Emit_Known(dictionary):
		_event_queue.put(dictionary)
	events['Emit Known'] = _IRC_Emit_Known
	
	def _IRC_IsOn_Request(dictionary):
		_irc_servers.getServer(dictionary['irccontext']).send("ISON :%s" % dictionary['username'], GLOBAL.ENUM_SERVER_SEND_PRIORITY.LOW)
	events['IsOn Request'] = _IRC_IsOn_Request
	
	def _IRC_Nickname_Change(dictionary):
		_irc_servers.getServer(dictionary['irccontext']).send("NICK :%s" % dictionary['username'], GLOBAL.ENUM_SERVER_SEND_PRIORITY.LOW)
	events['Nickname Change'] = _IRC_Nickname_Change
	
	def _IRC_Ping(dictionary):
		_irc_servers.getServer(dictionary['irccontext']).ping(dictionary['target'])
	events['Ping'] = _IRC_Ping
	
	def _IRC_Private_Message(dictionary):
		message = "PRIVMSG %s :" % dictionary['username']
		if dictionary['action']:
			message += "\001ACTION %s\001" % dictionary['message']
		else:
			message += dictionary['message']
			
		server = _irc_servers.getServer(dictionary['irccontext'])
		if dictionary['send']:
			server.send(message)
			
		server.addEvent(outboundDictionaries.IRC_User_Private_Message_Local(server.getContextID(), server.getName(), unicode(dictionary['username']), unicode(dictionary['message']), dictionary['action'], server.getNickname()))
	events['Private Message'] = _IRC_Private_Message
	
	def _IRC_Raw_Command(dictionary):
		_irc_servers.getServer(dictionary['irccontext']).send(dictionary['data'], GLOBAL.ENUM_SERVER_SEND_PRIORITY.LOW)
	events['Raw Command'] = _IRC_Raw_Command
	
	def _PyRC_Plugin_Disable(dictionary):
		GLOBAL.plugin.disablePlugin(dictionary['module'])
	events['Plugin Disable'] = _PyRC_Plugin_Disable
	
	def _PyRC_Plugin_Enable(dictionary):
		GLOBAL.plugin.enablePlugin(dictionary['module'])
	events['Plugin Enable'] = _PyRC_Plugin_Enable
	
	def _PyRC_Plugin_Load(dictionary):
		try:
			GLOBAL.plugin.addPlugin(dictionary['module'])
		except:
			_event_queue.put(outboundDictionaries.PyRC_Plugin_Crash(GLOBAL.errlog.grabTrace(), unicode(dictionary['plugin']), -1.0, dictionary, GLOBAL.errlog.logError('plugins', dictionary['module'], u"Import error")))
	events['Plugin Load'] = _PyRC_Plugin_Load
	
	def _PyRC_Plugin_Reload(dictionary):
		try:
			GLOBAL.plugin.reloadPlugin(dictionary['module'])
		except:
			_event_queue.put(outboundDictionaries.PyRC_Plugin_Crash(GLOBAL.control.errlog.grabTrace(), unicode(dictionary['plugin']), -1.0, dictionary, GLOBAL.errlog.logError('plugins', dictionary['module'], u"Import error")))
	events['Plugin Reload'] = _PyRC_Plugin_Reload
	
	def _PyRC_Plugin_Status(dictionary):
		_event_queue.put(dictionary)
	events['Plugin Status'] = _PyRC_Plugin_Status
	
	def _PyRC_Quit(dictionary):
		class QuitHandler(threading.Thread):
			dictionary = None
			
			def __init__(self, dictionary):
				threading.Thread.__init__(self)
				self.setDaemon(False)
				self.setName("QuitHandler")
				self.dictionary = dictionary
				
			def run(self):
				#Prevent anything from happening while everything dies.
				global _time_to_die
				_time_to_die = True
				
				for i in _worker_threads:
					i.kill()
					
				GLOBAL.plugin.broadcastEvent(outboundDictionaries.PyRC_Status("Shutting down PyRC..."))
				
				GLOBAL.plugin.killAll()
				
				active_servers = []
				inactive_servers = [] #Don't keep counting the dead.
				for i in _irc_servers.getServers():
					try:
						i.send("QUIT :" + self.dictionary['message'], GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
					except resources.connection.OutgoingTransmissionError:
						pass
					quit_thread = pyrc_common.asynch.Asyncher(i.close)
					active_servers.append(quit_thread)
					quit_thread.start()
					
				spin = True
				while spin:
					for i in inactive_servers:
						active_servers.remove(i)
					inactive_servers = []
					
					time.sleep(0.05)
					
					spin = False
					for i in active_servers:
						if i.isAlive():
							spin = True
							break
						else:
							inactive_servers.append(i)
							
				sys.exit()
		QuitHandler(dictionary).start()
	events['PyRC Quit'] = _PyRC_Quit
	
	def _PyRC_Register_Autocompletion(dictionary):
		_registered_commands_lock.acquire()
		_autocompletion_tree.addTokens(dictionary['pattern'].split())
		_registered_commands_lock.release()
	events['Register Autocompletion'] = _PyRC_Register_Autocompletion
	
	def _PyRC_Set_Environment_Variable(dictionary):
		GLOBAL.ENV_VARIABLES_LOCK.acquire()
		GLOBAL.ENV_VARIABLES[dictionary['variable']] = dictionary['value']
		GLOBAL.ENV_VARIABLES_LOCK.release()
	events['Set Environment Variable'] = _PyRC_Set_Environment_Variable
	
	def _PyRC_Toggle_Raw_Command_Handling(dictionary):
		GLOBAL.plugin.toggleRawCommandHandling(dictionary['enable'])
	events['Toggle Raw Command Handling'] = _PyRC_Toggle_Raw_Command_Handling
	
	def _PyRC_Toggle_Raw_Event_Handling(dictionary):
		GLOBAL.plugin.toggleRawEventHandling(dictionary['enable'])
	events['Toggle Raw Event Handling'] = _PyRC_Toggle_Raw_Event_Handling
	
	def _Server_Action(dictionary):
		_irc_servers.getServer(dictionary['irccontext']).resetIdleTime()
	events['Server Action'] = _Server_Action
	
	def _Server_Connect(dictionary):
		dictionary['address'] = dictionary['address'].lower()
		
		#Process user-provided details.
		network_name = None
		port = dictionary['port']
		if not port:
			if dictionary['ssl']:
				port = GLOBAL.IRC_DEFAULT_PORT_SSL
			else:
				port = GLOBAL.IRC_DEFAULT_PORT
				
		worker_threads = dictionary['options'].get('workerthreads')
		if not worker_threads:
			worker_threads = GLOBAL.USR_SERVER_THREADS
			
		auto_connect = False
		#proxy = None
		addresses = [(dictionary['address'], port, dictionary['ssl'])]
		channels = dictionary['channels']
		commands = ()
		
		#Process network details.
		pyrc_control.config.networks.load()
		
		#Find out if the target is a named network.
		network_from_address = False
		network = pyrc_control.config.networks.getNetwork(dictionary['address'])
		if not network: #Find out if the target is part of a named network.
			network_from_address = True
			network = pyrc_control.config.networks.getNetworkByAddress(dictionary['address'])
			
		pyrc_control.config.networks.unload()
		if network:
			network_name = network.get('name')
			if not network_name:
				network_name = network['id']
				
			auto_connect = network['autoconnect']
			worker_threads = network['workerthreads']
			#proxy = network['proxy']
			
			if dictionary['tryall']: #Only add addresses if the user doesn't say no.
				leading_addresses = []
				addresses = []
				for i in network['addresses'][1]:
					address = (i[0], i[1], i[2]) #i[3] is proxy data, which is not handled yet.
					if network_from_address and i[0] == dictionary['address']:
						leading_addresses.append(address)
					else:
						addresses.append(address)
						
				if network['addresses'][0]:
					random.shuffle(addresses)
					
				addresses = tuple(leading_addresses + addresses)
				
		#Process profiles.
		nicknames = dictionary['nicknames']
		nicknames_filled = not nicknames == None
		ident = dictionary['ident']
		real_name = dictionary['realname']
		profiles = dictionary['profiles']
		
		if profiles:
			pyrc_control.config.profiles.load()
			
			if nicknames:
				nicknames = list(nicknames)
			else:
				nicknames = []
				
			for i in profiles:
				profile = pyrc_control.config.getProfile(i)
				if profile:
					for j in profile[0]:
						if not j in nicknames:
							nicknames.append(j)
					if not ident:
						ident = profile[1]
					if not real_name:
						real_name = profile[2]
						
			pyrc_control.config.profiles.unload()
			
		if not nicknames or not ident or not real_name:
			pyrc_control.config.profiles.load()
			
			load_all_profiles = True
			
			if network: #Load network-specific details.
				if not nicknames_filled:
					nicknames = []
				for i in network['profiles'][1]:
					profile = pyrc_control.config.getProfile(i)
					if not nicknames_filled:
						for j in profile[0]:
							if not j in nicknames:
								nicknames.append(j)
					if not ident:
						ident = profile[1]
					if not real_name:
						real_name = profile[2]
						
					if nicknames_filled and ident and real_name: #Everything's full.
						break
						
				if not network['profiles'][0]:
					load_all_profiles = False
					
			if not ident or not real_name or not network:
				profile = pyrc_control.config.profiles.getDefaultProfile()
				if not nicknames:
					nicknames = profile[0]
				if not ident:
					ident = profile[1]
				if not real_name:
					real_name = profile[2]
					
			if load_all_profiles and not nicknames_filled:
				profiles = pyrc_control.config.profiles.getAllProfiles()
				for i in profiles:
					for j in profiles[i][0]:
						if not j in nicknames:
							nicknames.append(j)
							
			pyrc_control.config.profiles.unload()
			
		#Try connecting.
		server = _irc_servers.addServer(network_name, worker_threads)
		try:
			server.connect(nicknames, ident, real_name, addresses, dictionary['password'], channels)
		except Exception, e:
			error_header = u"Error connecting to '%s': " % dictionary['address']
			if isinstance(e, irc_server.InstantiationError):
				_event_queue.put(outboundDictionaries.Server_Connection_Error(server.getContextID(), server.getName(), error_header + e.description))
			else:
				(ty, val) = sys.exc_info()[:2] 
				_event_queue.put(outboundDictionaries.Server_Connection_Error(server.getContextID(), server.getName(), error_header + unicode(traceback.format_exception_only(ty, val)[0][:-1])))
			_irc_servers.removeServer(server.getContextID())
	events['Server Connect'] = _Server_Connect
	
	def _Server_Disconnect(dictionary):
		server = _irc_servers.getServer(dictionary['irccontext'])
		server.send("QUIT :%s" % dictionary['message'], GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
		server.disconnect()
	events['Server Disconnect'] = _Server_Disconnect
	
	def _Server_Quit(dictionary):
		server = _irc_servers.getServer(dictionary['irccontext'])
		server.send("QUIT :%s" % dictionary['message'], GLOBAL.ENUM_SERVER_SEND_PRIORITY.NOW)
		server.close()
		_irc_servers.removeServer(server.getContextID())
	events['Server Quit'] = _Server_Quit
	
	def _Server_Reconnect(dictionary):
		server = _irc_servers.getServer(dictionary['irccontext'])
		if server:
			try:
				server.reconnect()
				_event_queue.put(outboundDictionaries.Server_Reconnection_Success(server.getContextID(), server.getName(), server.getNickname(), server.getIdent(), server.getRealName()))
			except irc_server.ReconnectionError, e:
				_event_queue.put(outboundDictionaries.Server_Reconnection_Error(server.getContextID(), server.getName(), e.description))
			except irc_server.ConnectionError, e:
				_event_queue.put(outboundDictionaries.Server_Connection_Error(server.getContextID(), server.getName(), e.description))
		else:
			_event_queue.put(outboundDictionaries.Server_Reconnection_Error(dictionary['irccontext'], "Unknown", "%i is an invalid IRC context." % dictionary['irccontext']))
	events['Server Reconnect'] = _Server_Reconnect
	
	return events
_events = _eventGenerator()
del _eventGenerator

def _reqrespGenerator():
	"""
	This function generates all reqresp functions currently supported by PyRC's
	dictionary API.
	
	It will be called once and then deleted.
	
	It returns a dictionary keyed by 'eventname'; this allows the function
	associated with a reqresp dictionary to be retrieved quickly.
	
	@rtype: dict
	@return: A dictionary of reqresp functions that are keyed by 'eventname'.
	"""
	reqresps = {}
	
	def _IRC_Get_Channel(dictionary):
		return {
		 'channel': _irc_servers.getServer(dictionary['irccontext']).getChannel(dictionary['channel']).getData()
		}
	reqresps['Get Channel'] = _IRC_Get_Channel
	
	def _IRC_Get_Channels(dictionary):
		channel_manager = _irc_servers.getServer(dictionary['irccontext']).getChannelManager()
		
		return {
			'channels': channel_manager.getChannelsData()
		}
	reqresps['Get Channels'] = _IRC_Get_Channels
	
	def _IRC_Get_Channel_Modes(dictionary):
		channel = _irc_servers.getServer(dictionary['irccontext']).getChannel(dictionary['channel'])
		
		return {
		 'modes': channel.getModes(),
		 'modestring': channel.getModeStringFull(),
		 'modestringsafe': channel.getModeStringSafe()
		}
	reqresps['Get Channel Modes'] = _IRC_Get_Channel_Modes
	
	def _IRC_Get_Channel_Users(dictionary):
		return {
		 'users': _irc_servers.getServer(dictionary['irccontext']).getChannel(dictionary['channel']).getUsersData()
		}
	reqresps['Get Channel Users'] = _IRC_Get_Channel_Users
	
	def _IRC_Get_Current_Nickname(dictionary):
		return {
		 'username': _irc_servers.getServer(dictionary['irccontext']).getNickname()
		}
	reqresps['Get Current Nickname'] = _IRC_Get_Current_Nickname
	
	def _IRC_Get_Network_Names(dictionary):
		networks = {0: 'Local'}
		for i in _irc_servers.getServers():
			networks[i.getContextID()] = i.getName()
			
		return {
		 'networks': networks
		}
	reqresps['Get Network Names'] = _IRC_Get_Network_Names
	
	def _IRC_Get_Server(dictionary):
		return{
		 'server': _irc_servers.getServer(dictionary['irccontext']).getData()
		}
	reqresps['Get Server'] = _IRC_Get_Server
	
	def _IRC_Get_Servers(dictionary):
		servers = {}
		for i in _irc_servers.getServers():
			servers[i.getContextID()] = i.getData()
			
		return {
		 'servers': servers
		}
	reqresps['Get Servers'] = _IRC_Get_Servers
	
	def _IRC_Get_User(dictionary):
		return{
		 'user': _irc_servers.getServer(dictionary['irccontext']).getUser(dictionary['username']).getData(dictionary['channel'])
		}
	reqresps['Get User'] = _IRC_Get_User
	
	def _Plugin_Get_All_Plugin_Names(dictionary):
		return {
		 'plugins': GLOBAL.plugin.listAllPlugins()
		}
	reqresps['Get All Plugin Names'] = _Plugin_Get_All_Plugin_Names
	
	def _Plugin_Get_Loaded_Plugin_Info(dictionary):
		return {
		 'plugins': GLOBAL.plugin.listLoadedPlugins()
		}
	reqresps['Get Loaded Plugin Information'] = _Plugin_Get_Loaded_Plugin_Info
	
	def _Plugin_Get_Unloaded_Plugin_Name(dictionary):
		return {
		 'plugins': GLOBAL.plugin.listUnloadedPlugins()
		}
	reqresps['Get Unloaded Plugin Names'] = _Plugin_Get_Unloaded_Plugin_Name
	
	def _PyRC_Get_Autocompletion(dictionary):
		_registered_commands_lock.acquire()
		tokens = _autocompletion_tree.getTokens(dictionary['tokens'], dictionary['irccontext'], dictionary['focus'], _irc_servers)
		_registered_commands_lock.release()
		return {
		 'tokens': tokens
		}
	reqresps['Get Autocompletion'] = _PyRC_Get_Autocompletion
	
	def _PyRC_Get_Environment_Variables(dictionary):
		variables = {
		 'operatingsystem': GLOBAL.ENV_PLATFORM,
		 'ismicrosoft': GLOBAL.ENV_IS_MICROSOFT,
		 'architecture': unicode(GLOBAL.ENV_ARCHITECTURE),
		 'ispsyco': GLOBAL.ENV_PSYCO
		}
		GLOBAL.ENV_VARIABLES_LOCK.acquire()
		for i in GLOBAL.ENV_VARIABLES:
			variables[i] = GLOBAL.ENV_VARIABLES[i]
		GLOBAL.ENV_VARIABLES_LOCK.release()
		
		return variables
	reqresps['Get Environment Variables'] = _PyRC_Get_Environment_Variables
	
	def _PyRC_Get_Ping_Thresholds(dictionary):
		return {
		 'waittime': GLOBAL.IRC_IDLE_WAIT_TIME,
		 'timeout': GLOBAL.IRC_PING_TIMEOUT
		}
	reqresps['Get Ping Thresholds'] = _PyRC_Get_Ping_Thresholds
	
	def _PyRC_Get_Quit_Message(dictionary):
		return {
		 'quitmessage': GLOBAL.USR_VARIABLES['quitmessage']
		}
	reqresps['Get Quit Message'] = _PyRC_Get_Quit_Message
	
	def _PyRC_Get_Root_Path(dictionary):
		return {
		 'path': GLOBAL.PTH_DIR_PyRC_ROOT
		}
	reqresps['Get Root Path'] = _PyRC_Get_Root_Path
	
	def _PyRC_Get_User_Formats(dictionary):
		formats = {}
		for i in GLOBAL.USR_FORMATS:
			formats[i] = GLOBAL.USR_FORMATS[i]
			
		return formats
	reqresps['Get User Formats'] = _PyRC_Get_User_Formats
	
	def _PyRC_Get_User_Path(dictionary):
		return {
		 'path': GLOBAL.PTH_DIR_USER_ROOT
		}
	reqresps['Get User Path'] = _PyRC_Get_User_Path
	
	def _PyRC_Get_Version(dictionary):
		maintainers = {}
		for i in GLOBAL.RLS_PyRC_MAINTAINERS:
			(key, names) = i.split(':', 1)
			maintainers[key.lower()] = tuple(names.split(','))
			
		return {
		 'name': unicode(GLOBAL.RLS_PyRC_NAME),
		 'version': unicode(GLOBAL.RLS_PyRC_VERSION),
		 'url': unicode(GLOBAL.RLS_PyRC_URL),
		 'irc': unicode(GLOBAL.RLS_PyRC_IRC),
		 'license': unicode(GLOBAL.RLS_PyRC_LICENSE),
		 'maintainers': maintainers
		}
	reqresps['Get Version'] = _PyRC_Get_Version
	
	return reqresps
_reqresps = _reqrespGenerator()
del _reqrespGenerator

def processDictionary(dictionary):
	"""
	This function takes a dictionary from a plugin and reacts to it. It is, in
	effect, the most important function in all of PyRC.
	
	The dictionary is discarded if it is not spec-compliant.
	
	@type dictionary: dict
	@param dictionary: The PyRC-spec-compliant dictionary that is to be
	    processed.
	    
	@rtype: None|dict
	@return: The result of processing the dictionary, which is None for all
	    events and a dict for all reqresps unless the reqresp failed to resolve.
	"""
	if not _time_to_die:
		try:
			event_name = dictionary['eventname']
			event = _events.get(event_name) or _reqresps.get(event_name)
			if event:
				return event(dictionary)
			else:
				_event_queue.put(outboundDictionaries.PyRC_Status("Unknown dictionary:\n" + str(dictionary)))
		except SystemExit:
			pass
		except:
			#Check to see if it's a req/resp conflict with a closed server.
			#These are supposed to return None.
			#To debug possible problems, comment this block.
			try:
				if dictionary['eventname'] in _reqresps:
					if not _irc_servers.getServer(dictionary['irccontext']):
						return None
			except:
				pass
				
			#Some attribute in the dictionary wasn't as expected.
			_event_queue.put(outboundDictionaries.PyRC_Processing_Error(GLOBAL.errlog.grabTrace()))
			
