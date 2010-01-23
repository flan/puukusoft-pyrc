#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
PyRC: An IRC client framework written in Python

Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the attached licensing agreement.
 
 Copyright (c) Neil Tallim, 2004-2007
 
 PyRC is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 
 PyRC is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA 
"""
import sys
import os
import types
import shutil
import optparse
import re

try:
	import Ft.Xml
except:
	print "Your system doesn't have the 4Suite XML package installed."
	print "Please install this package and run this script again."
	sys.exit()
	
import pyrc_common.GLOBAL as GLOBAL
GLOBAL.initialise() #Load GLOBAL's module mesh.
import pyrc_common.G_OBJECTS as G_OBJECTS
import pyrc_common.C_FUNCS as C_FUNCS

import pyrc_control.config.settings as settings
import pyrc_init

import pyrc_common.dictionaries.outbound as outboundDictionaries
#Dictionaries used by this module:
##PyRC Initialised

if __name__ == "__main__":
	#Read commandline arguments
	########################################
	parser = optparse.OptionParser(version="%s v%s" % (GLOBAL.RLS_PyRC_NAME, GLOBAL.RLS_PyRC_VERSION))
	parser.add_option("-c", "--config", dest="config_path", help="Use config files in CONFIG_PATH instead of ~/.PyRC", metavar="CONFIG_PATH")
	parser.add_option("-i", "--interface", dest="interface", help="Load MODULE_NAME instead of the default interface", metavar="MODULE_NAME")
	parser.add_option("-p", "--plugins", dest="plugins", help="Load specific plugins from a comma-delimited list instead of the defaults", metavar="PLUGINS")
	(options, arguments) = parser.parse_args()

	GLOBAL.PTH_CONFIG_PATH = options.config_path
	interface = options.interface
	plugins = options.plugins
	if plugins:
		plugins = tuple(plugins.split(','))
	del parser
	del options
	del arguments

	#Initialise PyRC's environment
	########################################
	print "Initialising environment...",
	#Determine the operating environment.
	pyrc_init.identifyPlatform()
	if GLOBAL.ENV_IS_MICROSOFT:
		GLOBAL.ENV_LINEBREAK = "\r\n"
		
	#Set the user and PyRC root paths.
	pyrc_init.setRootPaths()
		
	#Set PyRC's root directory as the first search path for imports.
	sys.path.insert(0, GLOBAL.PTH_DIR_PyRC_ROOT)
	#...And then give precedence to the user's directory.
	sys.path.insert(0, GLOBAL.PTH_DIR_USER_ROOT)

	#Build paths if necessary.
	pyrc_init.buildUserProfilePaths()
		
	#Copy config files if necessary.
	if not GLOBAL.PTH_CONFIG_PATH:
		GLOBAL.PTH_CONFIG_PATH = GLOBAL.PTH_DIR_USER_ROOT
		if not os.path.isfile(GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_SETTINGS_CONFIG_FILE):
			shutil.copy(GLOBAL.PTH_DIR_PyRC_ROOT + os.sep + "sample" + os.sep + GLOBAL.PTH_SETTINGS_CONFIG_FILE, GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_SETTINGS_CONFIG_FILE)
			os.chmod(GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_SETTINGS_CONFIG_FILE, 0600)
		if not os.path.isfile(GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_NETWORKS_CONFIG_FILE):
			shutil.copy(GLOBAL.PTH_DIR_PyRC_ROOT + os.sep + "sample" + os.sep + GLOBAL.PTH_NETWORKS_CONFIG_FILE, GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_NETWORKS_CONFIG_FILE)
			os.chmod(GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_NETWORKS_CONFIG_FILE, 0600)
		if not os.path.isfile(GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_PROFILES_CONFIG_FILE):
			shutil.copy(GLOBAL.PTH_DIR_PyRC_ROOT + os.sep + "sample" + os.sep + GLOBAL.PTH_PROFILES_CONFIG_FILE, GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_PROFILES_CONFIG_FILE)
			os.chmod(GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_PROFILES_CONFIG_FILE, 0600)
			
	#Initialisation is done, so dereference the setup resource.
	del pyrc_init
	print "Complete"


	#Load PyRC's settings
	########################################
	print "Loading settings...",
	try:
		settings.load()
		
		GLOBAL.USR_VARIABLES['userinfo'] = settings.getOption("irc.userinfo")
		GLOBAL.USR_VARIABLES['quitmessage'] = settings.getOption("irc.defaultquitmessage")
		GLOBAL.IRC_AUTO_RECONNECT = settings.getOption("irc.autoreconnect")
		
		GLOBAL.ENV_PSYCO = C_FUNCS.evaluateTruth(settings.getOption("pyrc.usepsyco"))
		GLOBAL.USR_SERVER_THREADS = int(settings.getOption("pyrc.serverworkerthreads"))
		ial_worker_threads = int(settings.getOption("pyrc.workerthreads"))
		
		#Validate IPv4.
		local_ip = re.search(r"(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})", settings.getOption("dcc.localip"))
		if local_ip:
			if int(local_ip.group(1)) <= 255 and int(local_ip.group(2)) <= 255 and int(local_ip.group(3)) <= 255 and int(local_ip.group(4)) <= 255:
				GLOBAL.DCC_LOCAL_IP = '.'.join(local_ip.groups())
		del local_ip
		
		GLOBAL.USR_FORMATS['timestamp'] = settings.getFormat("timestamp")
		GLOBAL.USR_FORMATS['datestamp'] = settings.getFormat("datestamp")
		GLOBAL.USR_FORMATS['timedatestamp'] = settings.getFormat("timedatestamp")
		
		if not interface:
			interface = settings.getInterface()
		if not plugins:
			plugins = settings.getPlugins()
		ctcps = settings.getCTCPs()
		
		settings.unload()
	except Ft.Lib.UriException:
		print "Failed -- XML file was not found"
		print "Fatal error"
		sys.exit()
	except Ft.Xml.ReaderException:
		print "Failed -- XML file did not validate"
		print "Fatal error"
		sys.exit()
	except Exception, e:
		print "Failed -- %s" % str(e)
		print "Fatal error"
		sys.exit()
	#Configuration is done, so dereference the settings resource.
	del settings
	print "Complete"

	#Apply settings
	########################################
	print "Applying settings"
	#Set CTCP responses
	if ctcps:
		import pyrc_irc_abstract.resources.ctcp_core
		for i in ctcps:
			pyrc_irc_abstract.resources.ctcp_core.addResponse(i[0], i[1], i[2])
		del pyrc_irc_abstract.resources.ctcp_core
	del ctcps

	#Initialise IAL
	GLOBAL.irc_interface.initialise(ial_worker_threads)
	del ial_worker_threads


	#Load modules
	########################################
	#Begin loading non-plugin modules
	print "Loading additional modules"

	#Check to see if we want to try loading Psyco.
	if GLOBAL.ENV_PSYCO:
		print "\tLoading Psyco...",
		try:
			global psyco
			import psyco
			psyco.profile(0.01)
			print "Complete"
		except ImportError:
			GLOBAL.ENV_PSYCO = False
			print "Failed -- module could not be found"
		except:
			GLOBAL.ENV_PSYCO = False
			print "Failed -- unknown error"
			print "\t\tError log: %s" % GLOBAL.errlog.logError(GLOBAL.PTH_MODULE_SUBPATH, "psyco", "reason unknown")
			
	#Load plugins.
	if plugins:
		print "Loading plugins"
		for i in plugins:
			if not i[1]: #Plugin was disabled in the config file.
				print "\tNot loading %s." % i[0]
				continue
				
			print "\tLoading %s..." % i[0],
			try:
				GLOBAL.plugin.addPlugin(i[0], False)
				print "Complete"
			except ImportError:
				print "Failed -- module could not be loaded"
				print "\t\tError log: %s" % GLOBAL.errlog.logError(GLOBAL.PTH_PLUGIN_SUBPATH, i[0], "plugin missing or error in loadMe()")
			except:
				print "Failed -- unknown error"
				print "\t\tError log: %s" % GLOBAL.errlog.logError(GLOBAL.PTH_PLUGIN_SUBPATH, i[0], "reason unknown")
	del plugins

	#Set interface.
	print "Loading interface"
	interface_function = None
	if not interface:
		interface = GLOBAL.PTH_RAW_UI
	print "\tLoading %s..." % interface,
	try:
		try:
			interface_function = GLOBAL.plugin.setUI(interface)
			print "Complete"
		except ImportError:
			print "Failed -- module could not be loaded"
			print "\t\tError log: %s" % GLOBAL.errlog.logError(GLOBAL.PTH_UI_SUBPATH, interface, "plugin missing or error in loadMe()")
			if interface == GLOBAL.PTH_RAW_UI:
				print "Fatal error"
				sys.exit()
				
			print "\tFalling back to Raw UI...",
			interface = GLOBAL.PTH_RAW_UI
			interface_function = GLOBAL.plugin.setUI()
			print "Complete"
	except:
		print "Failed -- unknown error"
		print "\t\tError log: %s" % GLOBAL.errlog.logError(GLOBAL.PTH_UI_SUBPATH, interface, "reason unknown")
		print "Fatal error"
		sys.exit()
	del interface
	
	
	#Start PyRC
	########################################
	#Notify all plugins that everything is set.
	GLOBAL.plugin.broadcastEvent(outboundDictionaries.PyRC_Initialised())

	#Start the global event timer
	G_OBJECTS.EventTimer().start()
	
	#Run the UI with the main thread, if requested.
	#######################################################
	if interface_function:
		interface_function(GLOBAL.irc_interface.processDictionary)
	else:
		del interface_function
		