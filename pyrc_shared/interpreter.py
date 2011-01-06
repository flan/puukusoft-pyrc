# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_shared.interpreter

Purpose
=======
 Provide a common library for translating user input into PyRC Dictionaries.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2005-2007
"""
import re
import optparse

import pyrc_common.GLOBAL as GLOBAL

ENUM_EXECUTION_CODES = GLOBAL.enum.Enum("SUCCESS", "SUCCESS_REQRESP", "SYNTAX_ERROR", "UNKNOWN") #: An enumeration used to indicate the success of interpretations.

_ial = None #: A reference to the IRC Abstraction Layer, needed to retrieve information to fill dictionaries.
_initialised = False #: True once the interpreter has been initialised. Used to prevent needless processing when the the interpreter is recycled.

def _generateInterpreters():
	"""
	This function compiles a dictionary of functions that may be used to
	interpret user commands.
	
	All of the generated functions have the same signatures as interpret().
	
	@rtype: dict
	@return: A dictionary of user-command-interpreting functions, keyed by
	    handler category ID.
	"""
	def _msg_implementation(message, irc_context, target, action):
		if target[0] in GLOBAL.IRC_CHANNEL_PREFIX:
			dictionary = {
			 'eventname': "Channel Message",
			 'irccontext': irc_context,
			 'channel': target,
			 'message': message,
			 'action': action,
			 'send': True
			}
		else:
			dictionary = {
			 'eventname': "Private Message",
			 'irccontext': irc_context,
			 'username': target,
			 'message': message,
			 'action': action,
			 'send': True
			}
		return (ENUM_EXECUTION_CODES.SUCCESS, (), dictionary)
		
		
	interpreters = {}
	
	def _exit(command, irc_context, focus):
		match = re.match(r"^EXIT(?: (.+))?", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR, (
			 "Invalid syntax. Correct syntax for /exit:",
			 "/exit [message]"), {}
			)
			
		message = match.group(1)
		if not message:
			message = _ial({'eventname': "Get Quit Message"})['quitmessage']
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "PyRC Quit",
		 'message': message
		})
	interpreters['exit'] = _exit
	
	def _ison(command, irc_context, focus):
		match = re.match(r"^ISON (\S+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /ison:",
			 "/ison <user>"), {}
			)
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "IsOn Request",
		 'irccontext': irc_context,
		 'username': match.group(1)
		})
	interpreters['ison'] = _ison
	
	def _join(command, irc_context, focus):
		match = re.match("^JOIN ([" + ''.join(GLOBAL.IRC_CHANNEL_PREFIX) + "]\S+)(?: (\S+))?", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /join:",
			 "/join <channel> [password]"), {}
			)
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "Channel Join",
		 'irccontext': irc_context,
		 'channel': match.group(1),
		 'password': match.group(2)
		})
	interpreters['join'] = _join
	
	def _me(command, irc_context, focus):
		if not focus:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Logic error. /me requires implicit focus"), {}
			)
			
		match = re.match(r"^(?:ME|EMOTE|ACTION) (.+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /me:",
			  "/me <message>"), {}
			)
			
		return _msg_implementation(match.group(1), irc_context, focus, True)
	interpreters['me'] = _me
	
	def _msg(command, irc_context, focus):
		match = re.match(r"^(?:MSG|PRIVMSG) ([\w-]+) (.+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /msg:",
			  "/me <user|channel> <message>"), {}
			)
			
		return _msg_implementation(match.group(2), irc_context, match.group(1), False)
	interpreters['msg'] = _msg
	
	def _nick(command, irc_context, focus):
		match = re.match(r"^NICK (\S+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR, (
			 "Invalid syntax. Correct syntax for /nick:",
			 "/nick <name>"), {}
			)
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "Nickname Change",
		 'irccontext': irc_context,
		 'username': match.group(1)
		})
	interpreters['nick'] = _nick
	
	def _ping(command, irc_context, focus):
		match = re.match(r"^PING(?: ([" + ''.join(GLOBAL.IRC_CHANNEL_PREFIX) + "]?[\w-]+))?", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /ping:",
			 "/ping [user|channel]"), {}
			)
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "Ping",
		 'irccontext': irc_context,
		 'target': match.group(1)
		})
	interpreters['ping'] = _ping
	
	def _plugin(command, irc_context, focus):
		match = re.match(r"PLUGIN (LOAD|RELOAD|DISABLE|ENABLE|LIST) (\S+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /plugin:",
			 "/plugin <load|reload|enable|disable> <plugin>",
			 "/plugin list <all|loaded|unloaded>"), {}
			)
			
		mode = match.group(1).lower()
		event_name = None
		if mode == 'list':
			target = match.group(2).strip().lower()
			if target == 'all':
				event_name = "Get All Plugin Names"
			elif target == 'loaded':
				event_name = "Get Loaded Plugin Information"
			elif target == 'unloaded':
				event_name = "Get Unloaded Plugin Names"
			else:
				return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
				 ("Invalid syntax. Correct syntax for /plugin list:",
				 "/plugin list <all|loaded|unloaded>"), {}
				)
				
			return (ENUM_EXECUTION_CODES.SUCCESS_REQRESP, (), {
			 'eventname': event_name
			})
		elif mode == 'load':
			event_name = "Plugin Load"
		elif mode == 'reload':
			event_name = "Plugin Reload"
		elif mode == 'disable':
			event_name = "Plugin Disable"
		elif mode == 'enable':
			event_name = "Plugin Enable"
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': event_name,
		 'module': match.group(2).strip()
		})
	interpreters['plugin'] = _plugin
	
	def _quit(command, irc_context, focus):
		match = re.compile(r"^QUIT(?: (.+))?", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /quit:",
			 "/quit [message]"), {}
			)
			
		message = match.group(1)
		if not message:
			message = _ial({'eventname': "Get Quit Message"})['quitmessage']
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "Server Quit",
		 'irccontext': irc_context,
		 'message': message
		})
	interpreters['quit'] = _quit
	
	def _raw(command, irc_context, focus):
		match = re.match(r"^(?:RAW|QUOTE) (.+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /raw:",
			 "/raw <command>"), {}
			)
			
		return (ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "Raw Command",
		 'irccontext': irc_context,
		 'data': match.group(1)
		})
	interpreters['raw'] = _raw
	
	def _say(command, irc_context, focus):
		if not focus:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Logic error. /say requires implicit focus"), {}
			)
			
		match = re.match(r"^(?:SAY |/)(.+)", command, re.I)
		if not match:
			return (ENUM_EXECUTION_CODES.SYNTAX_ERROR,
			 ("Invalid syntax. Correct syntax for /say:",
			 "/say <message>"), {}
			)
			
		return _msg_implementation(match.group(1), irc_context, focus, False)
	interpreters['say'] = _say
	
	def _server(command, irc_context, focus):
		match = re.match(r"^(?:SERVER|CONNECT) (.+)", command, re.I)
		if match:
			parser = optparse.OptionParser()
			parser.add_option("-c", "--channels", dest="channels")
			parser.add_option("-f", "--profiles", dest="profiles")
			parser.add_option("-g", "--singleaddress", dest="tryall", action="store_false")
			parser.add_option("-i", "--ident", dest="ident")
			parser.add_option("-n", "--nicknames", dest="nicknames")
			parser.add_option("-o", "--proxy", dest="proxy")
			parser.add_option("-p", "--port", dest="port")
			parser.add_option("-r", "--realname", dest="realname")
			parser.add_option("-s", "--ssl", dest="ssl", action="store_true")
			parser.add_option("--workerthreads", dest="workerthreads")
			(options, arguments) = parser.parse_args(args=match.group(1).split())
			
			if not arguments:
				return (ENUM_EXECUTION_CODES.SYNTAX_ERROR, (
				 "Invalid syntax. Correct syntax for /server:",
				 "/server [options] <address> [password]",
				 "Where options may be any of the following in UNIX format:",
				 " -c <channel[,channel...]> : join channels",
				 " -f <profile[,profile...]> : specify profiles",
				 " -g : only use specified address [default: off]",
				 " -i <ident> : force ident string",
				 " -n <nickname[,nickname...]> : specify nicknames",
				 " -o <proxy> : specify named proxy",
				 " -p <port> : specify port",
				 " -r <name> : force real name string",
				 " -s : use SSL (not supported everywhere) [default: off]",
				 " --workerthreads=<thread_count> : specify worker thread count"
				), {})
				
			con_address = arguments[0].lower()
			con_password = None
			if len(arguments) > 1:
				con_password = arguments[1]
				
			con_channels = ()
			if options.channels:
				con_channels = tuple(options.channels.split(','))
			con_profiles = ()
			if options.profiles:
				con_profiles = tuple(options.profiles.split(','))
			con_try_all = True
			if options.tryall == False:
				con_try_all = False
			con_ident = options.ident
			con_nicknames = None
			if options.nicknames:
				con_nicknames = tuple(options.nicknames.split(','))
			con_proxy = options.proxy
			con_port = options.port
			try:
				con_port = int(con_port)
			except:
				con_port = None
			con_real_name = options.realname
			con_ssl = False
			if options.ssl:
				con_ssl = True
			
			con_options = {}
			if options.workerthreads:
				try:
					con_options['workerthreads'] = int(options.workerthreads)
				except:
					pass
					
		return(ENUM_EXECUTION_CODES.SUCCESS, (), {
		 'eventname': "Server Connect",
		 'address': con_address,
		 'port': con_port,
		 'ssl': con_ssl,
		 'tryall': con_try_all,
		 'proxy': con_proxy,
		 'nicknames': con_nicknames,
		 'ident': con_ident,
		 'realname': con_real_name,
		 'password': con_password,
		 'channels': con_channels,
		 'profiles': con_profiles,
		 'options': con_options
		})
	interpreters['server'] = _server
	
	return interpreters
_interpreters = _generateInterpreters()
del _generateInterpreters

_handlers = (
 (re.compile(r"^(?:MSG|PRIVMSG)", re.I), _interpreters['msg']), #PRIVMSG
 (re.compile(r"^(?:ME|EMOTE|ACTION)", re.I), _interpreters['me']), #ACTION
 (re.compile(r"^PING", re.I), _interpreters['ping']), #PING
 (re.compile(r"^(?:RAW|QUOTE)", re.I), _interpreters['raw']), #RAW
 (re.compile(r"^QUIT", re.I), _interpreters['quit']), #QUIT
 (re.compile(r"^EXIT", re.I), _interpreters['exit']), #EXIT
 (re.compile(r"^NICK", re.I), _interpreters['nick']), #NICK
 (re.compile(r"^JOIN", re.I), _interpreters['join']), #JOIN
 (re.compile(r"^ISON", re.I), _interpreters['ison']), #ISON
 (re.compile(r"^(?:SAY|/)", re.I), _interpreters['say']), #SAY
 #KICK
 #BAN
 #KICKBAN
 #PART
 (re.compile(r"^(?:SERVER|CONNECT)", re.I), _interpreters['server']), #SERVER (No disconnects -- require "QUIT")
 #TOPIC
 #MODE
 #VOICE
 #HOP
 #OP
 #CYCLE
 #CTCP
 (re.compile(r"^PLUGIN", re.I), _interpreters['plugin']), #PLUGIN
)
"""
A tuple of all commands currently supported by the interpreter. Its elements are
themselves tuples that contain a handler ID string and a command-matching
regular expression.
"""
del _interpreters

def initialise(ial):
	"""
	This function must be called before the interpreter may be used. It sets a
	reference to the IAL and registers its commands with PyRC's grammar
	database.
	
	@type ial: function
	@param ial: A reference to the IRC Abstraction Layer's interface.
	
	@return: Nothing.
	"""
	global _initialised
	if not _initialised:
		_initialised = True
		
		global _ial
		_ial = ial
		
		def register(pattern):
			_ial({
			 'eventname': "Register Autocompletion",
			 'pattern': pattern
			})
			
		map(register, (
		 'action', 'emote', 'me',
		 'connect', 'server',
		 'exit',
		 'ison',
		 'join',
		 'msg %u', 'msg %c', 'privmsg %u', 'privmsg %c',
		 'nick',
		 'ping', 'ping %u', 'ping %c',
		 'plugin load %p', 'plugin reload %p',
		 'plugin disable %p', 'plugin enable %p',
		 'plugin list all', 'plugin list loaded', 'plugin list unloaded',
		 'quit',
		 'raw', 'quote',
		 'say',
		))
		
def interpret(command, irc_context, focus=None):
	"""
	This function takes a command string, which is generally anything the user
	prefixes with a '/', and attempts to process it.
	
	It will return a success code depending on the result of processing. These
	codes follow::
	  ENUM_EXECUTION_CODES.SUCCESS:
	    Processing was successful; an IAL-friendly translation is included.
	  ENUM_EXECUTION_CODES.SUCCESS_REQRESP:
	    Processing was successful; a request/response dictionary is included.
	  ENUM_EXECUTION_CODES.SYNTAX_ERROR:
	    Processing was unsuccessful; a description of the problem is included.
	  ENUM_EXECUTION_CODES.UNKNOWN:
	    Processing was unsuccessful; the given command was not recognized, and
	    it has been returned in the translation, keyed by 'command'.
	
	Callers need to provide correct irc_context so the event can be properly
	directed, and focus should be provided where relevant to avoid ambiguity.
	
	@type command: basestring
	@param command: The string to be processed.
	@type irc_context: int
	@param irc_context: The ID of the IRC server to which this message should be
	    sent.
	@type focus: basestring|None
	@param focus: The context where the user typed the string, such as a channel
	    or a query.
	
	@rtype: tuple
	@return: A tuple of the following format::
	     (<execution_code:ENUM_EXECUTION_CODES.EnumValue>,
		  <execution_description:tuple>, <translation:dict>)
	"""
	for i in _handlers:
		if i[0].match(command):
			return i[1](command, irc_context, focus)
			
	return (ENUM_EXECUTION_CODES.UNKNOWN, (), {'command': command})
	
