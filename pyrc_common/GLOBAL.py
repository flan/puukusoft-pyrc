# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.GLOBAL

Purpose
=======
 Store constants, environment variables, and Singleton objects in a
 centralised location, thereby removing trace confusion.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2006-2007
"""
import threading

#Modules
#==============================================================================
import enum
def initialise():
	"""
	This function is used to prevent a recusrive import lookup from happening.
	
	All modules imported by this function depend on GLOBAL, so GLOBAL must be
	loaded before they can be loaded, or else they will try to load GLOBAL while
	while it is already being loaded, which will fail.
	
	@return: Nothing.
	"""
	global plugin
	import pyrc_control.plugin as plugin
	global errlog
	import pyrc_common.errlog as errlog
	global irc_interface
	import pyrc_irc_abstract.irc_interface as irc_interface
	
#Constants
#==============================================================================
#Release variables
#######################################
RLS_PyRC_NAME = "PyRC" #: The current name of PyRC.
RLS_PyRC_VERSION = "0.1.9" #: The current version of PyRC.
RLS_PyRC_URL = "http://hamsterx.homelinux.org/" #: The URL at which the PyRC project page is located.
RLS_PyRC_IRC = "#animesuki.os@irc.synirc.net" #: The IRC channel in which PyRC development discussion takes place.
RLS_PyRC_LICENSE = "GPLv2" #: The license under which PyRC is distributed.
RLS_PyRC_MAINTAINERS = (
 "authors:Neil Tallim",
 "documenters:Neil Tallim",
 "artists:Neil Tallim",
)#: A list of all maintainers associated with the PyRC project. Names are comma-delimited.

#IRC constants
#######################################
IRC_DEFAULT_PORT = 6667 #: The default port to try for non-SSL connections to an IRC server.
IRC_DEFAULT_PORT_SSL = 7001 #: The default port to try for SSL connections to an IRC server.
IRC_IDLE_WAIT_TIME = 300 #: The number of seconds to wait before attempting to PING an IRC server if no events have been received.
IRC_PING_TIMEOUT = 120 #: The number of seconds to wait before declaring a PING failed.
IRC_CHANNEL_PREFIX = ('#', '+', '!') #: A list of known channel prefixes.
IRC_IGNORED_MODES = ('b', 'd', 'e', 'I') #: A list of modes not processed by PyRC; these are managed entirely by the IRC server, so PyRC does not need to track them.
IRC_LINE_TERMINATOR = "\r\n" #: The string used to indicate the end of a line in an IRC server's stream.
IRC_RANK_ORDER = ('O', '!', 'q', 'a', 'o', 'h', 'v') #: The order of rank precedence, in tokens, on IRC networks.
IRC_RANK_PREFIX = ('*', '^', '~', '&', '@', '%', '+') #: The order of rank precedence, in symbols, on IRC networks.
IRC_RANK_MAP = {} #: A lookup for deriving symbols from IRC rank tokens.
#{'!': '^', 'a': '&', 'h': '%', 'O': '*', 'q': '~', 'o': '@', 'v': '+'}
IRC_RANK_MAP_REVERSE = {} #: A reverse-lookup version of IRC_RANK_MAP.
#{'@': 'o', '%': 'h', '&': 'a', '+': 'v', '*': 'O', '^': '!', '~': 'q'}
IRC_PACKET_SIZE = 8192 #: The number of bytes to read from an IRC server each cycle.

#Population routines
#######################################
for i in range(len(IRC_RANK_ORDER)):
	IRC_RANK_MAP[IRC_RANK_ORDER[i]] = IRC_RANK_PREFIX[i]
for i in IRC_RANK_ORDER:
	IRC_RANK_MAP_REVERSE[IRC_RANK_MAP[i]] = i
	
#Paths
#######################################
PTH_CONFIG_SUBPATH = "conf" #: The subpath in which PyRC's plugins' configuration files are stored.
PTH_ERROR_SUBPATH = "errors" #: The subpath in which PyRC's error logs are stored.
PTH_LOG_SUBPATH = "logs" #: The subpath in which PyRC's logs are stored.
PTH_MODULE_SUBPATH = "modules" #: The subpath in which PyRC's modules are stored.
PTH_PLUGIN_SUBPATH = "plugins" #: The subpath in which PyRC's plugins are stored.
PTH_UI_SUBPATH = "uis" #: The subpath in which PyRC's UIs are stored.
PTH_PLUGIN_MAIN_MODULE = "main" #: The name of the main module of a PyRC plugin.
PTH_ERROR_LOGFILE_EXTENSION = ".log" #: The extension used to write log files.
PTH_PLUGIN_MAIN_EXTENSION = ".py" #: The extension used to identify Python files.
PTH_RAW_UI = "RawUI" #: The string used to identify RawUI, used in place of a real path.
PTH_NETWORKS_CONFIG_FILE = "networks.xml" #: The file in which PyRC's networks are located.
PTH_PROFILES_CONFIG_FILE = "profiles.xml" #: The file in which PyRC's profiles are located.
PTH_SETTINGS_CONFIG_FILE = "settings.xml" #: The file in which PyRC's settings are located.

#Patterns
#######################################
PTN_TRUTH = ('true', 'yes', '1', 'y', 't', 'on') #: A list of all known strings that imply truth.

#Enumerations
#######################################
ENUM_PLATFORM_ARCHITECTURE = enum.Enum("x86", "x86_64", "ppc", "sparc", "alpha", "unknown") #: An enumeration of hardware architectures.
ENUM_SERVER_SEND_PRIORITY = enum.Enum("NOW", "CRITICAL", "VERY_HIGH", "HIGH", "AVERAGE", "LOW") #: An enumeration of priorities at which events should be sent to IRC networks.

#Environment variables
#==============================================================================
#Operating environment
#######################################
ENV_IS_MICROSOFT = False #: True if PyRC is running on a Microsoft operating system, which may indicate the need to use workarounds.
ENV_PLATFORM = None #: The name of the operating system on which PyRC is running.
ENV_ARCHITECTURE = None #: The type of hardware architecture on which PyRC is running. An ENUM_PLATFORM_ARCHITECTURE.EnumValue value.
ENV_PSYCO = False #: True if Psyco is in use; False otherwise.
ENV_LINEBREAK = "\n" #: The string to place at the end of all lines when writing a logfile.
ENV_VARIABLES = {} #: A collection of all plugin-specified environment variables.
ENV_VARIABLES_LOCK = threading.Lock() #: A lock used to prevent multiple simultaneous accesses to the environment variables.

#IRC
#######################################
IRC_AUTO_RECONNECT = True #: True if PyRC should automatically try to reconnect to servers when it is disconnected by a non-kill.

#DCC
#######################################
DCC_LOCAL_IP = None #: The value to return as PyRC's local IP.

#Paths
#######################################
PTH_DIR_USER_ROOT = None #: The path of the user's .PyRC/ directory.
PTH_DIR_PyRC_ROOT = None #: The path in which PyRC is installed.
PTH_CONFIG_PATH = None #: The path in which PyRC should look for its config files.

#User-specified variables
#######################################
USR_FORMATS = {} #: Any user-specified formats, generally used for localization.
USR_VARIABLES = {} #: Any user-specified variables, such as default quit messages.
USR_SERVER_THREADS = 3 #: The number of worker threads to create for each ircAbstract.ircServer if not specified in the network config.
