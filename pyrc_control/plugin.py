# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_control.plugin

Purpose
=======
 Provide an interface for managing and interacting with plugins.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import os
import sys
import imp
import time
import threading

import pyrc_common.GLOBAL as GLOBAL
import pyrc_common.asynch

import pyrc_common.dictionaries.outbound as outboundDictionaries
#Dictionaries used by this module:
##PyRC Plugin Crash
##PyRC Plugin Disable
##PyRC Plugin Enable
##PyRC Plugin Load Error
##PyRC Plugin Reload
##PyRC Plugin Unload
##PyRC Status

_ENUM_ACTION_CODES = GLOBAL.enum.Enum("REPLACE", "SKIP_REST", "SKIP_ALL", "NORMAL") #: This enumeration is used to handle Raise Event Dictionary processing.

_LOAD_MODE_FIRST = 0 #: The load type identifier to pass to plugins when they are being loaded for the first time.
_LOAD_MODE_ENABLE = 1 #: The load type identifier to pass to plugins when they are being re-enabled after being disabled.
_LOAD_MODE_RELOAD = -1 #: The load type identifier to pass to plugins when they are being reloaded. The negative value is used to prevent >= approaches, since this is a debug/development feature, and it should not be used in mature plugins.

_UNLOAD_MODE_DISABLE = 1 #: The unload type identifier to pass to plugins when they are being disabled.
_UNLOAD_MODE_RELOAD = -1 #: The unload type identifier to pass to plugins when they are being reloaded. The negative value is used to prevent >= approaches, since this is a debug/development feature, and it should not be used in mature plugins.

_plugins = {}
"""
This is a dictionary of all managed plugins.

Its elements take the following form::
 <module_name:string>: <plugin_wrapper:_Plugin>
"""
_ui = None #: This is a reference to the UI's _UI wrapper.

_raw_event_disabled = True #: True if "Raw Event" dictionaries should be disabled, providing an efficiency boost; False otherwise.
_raw_command_disabled = True #: True if "Raw Command" dictionaries should be disabled, providing an efficiency boost; False otherwise.

_raw_event_ui_override = False #: True if "Raw Event" dictionaries should be enabled for UI consumption after the UI has been set.
_raw_command_ui_override = False #: True if "Raw Command" dictionaries should be enabled for UI consumption after the UI has been set.

_time_to_die = False #: True when all event processing should be disabled because PyRC is shutting down.

def setUI(module_path=None):
	"""
	This function loads a UI for PyRC.
	
	Since the given module name is just a subpath fragment, PyRC looks for
	matches in the user's UI directory before looking for matches in the
	global UI directory, allowing users to maintain custom versions.
	
	If the loaded UI specifies a function in its returned value, that function
	will be executed using PyRC's main thread. This may help to avoid
	workarounds when using UI toolkits that assume they will be run using the
	program's main thread.
	
	Note that this behaviour comes at the cost of having the UI's hookEvent()
	function risk receiving the 'Initialised' and first 'Time Signal' events
	before its display contexts have been created. This should not cause a
	problem, but whatever handling mechanism is used will need to discard or
	cache these events to avoid a crash or lock.
	
	@type module_path: basestring
	@param module_path: The subpath fragment used to identify the plugin that
	    should be loaded.
	
	@rtype: function|None
	@return: The main function of the UI, if specified.
	
	@raise Exception: If an error occurs during the import or loading processes.
	"""
	global _ui
	global _raw_event_disabled
	global _raw_command_disabled
	
	if module_path:
		paths = [
		 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_UI_SUBPATH + os.sep + module_path,
		 GLOBAL.PTH_DIR_PyRC_ROOT + os.sep + GLOBAL.PTH_UI_SUBPATH + os.sep + module_path
		]
		
		_ui = _UI(module_path, GLOBAL.PTH_PLUGIN_MAIN_MODULE, paths, GLOBAL.PTH_UI_SUBPATH, False)
	else:
		_ui = _UI(GLOBAL.PTH_RAW_UI, None, None, None, False)
		
	if _raw_event_disabled and _ui.handlesRawEvent():
		_raw_event_disabled = False
		
	if _raw_command_disabled and _ui.handlesRawCommand():
		_raw_command_disabled = False
		
	return _ui.getStartupFunction()
	
def addPlugin(module_name, tolerate_fault=True):
	"""
	This function loads a plugin into PyRC's plugin structure.
	
	Since the given module name is just a subpath fragment, PyRC looks for
	matches in the user's plugin directory before looking for matches in the
	global plugin directory, allowing users to maintain custom versions.
	
	On a successful load, a "Plugin Loaded" event will be generated.
	
	On an unsucessful load, a "Plugin Loading Error" event will be generated or
	an exception will be thrown, depending on whether faults are tolerated.
	
	@type module_path: basestring
	@param module_path: The subpath fragment used to identify the plugin that
	    should be loaded.
	@type tolerate_fault: bool
	@param tolerate_fault: True if "Plugin Load Error" events should be
	    generated; False if exceptions should be raised.
	
	@return: Nothing.
	
	@raise Exception: If tolerate_fault is not set and an error occurs during
	    the import or loading processes.
	"""
	if module_name in _plugins: #Don't add what already exists.
		return
		
	module_name = unicode(module_name)
	try:
		module_paths = [
		 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH + os.sep + module_name,
		 GLOBAL.PTH_DIR_PyRC_ROOT + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH + os.sep + module_name
		]
		plugin = _Plugin(module_name, GLOBAL.PTH_PLUGIN_MAIN_MODULE, module_paths, GLOBAL.PTH_PLUGIN_SUBPATH, tolerate_fault)
		_plugins[module_name] = plugin
	except PluginLoadError, e:
		trace = tuple(GLOBAL.errlog.grabTrace())
		broadcastEvent(outboundDictionaries.PyRC_Plugin_Load_Error(module_name, trace,	GLOBAL.errlog.logError(GLOBAL.PTH_PLUGIN_SUBPATH, module_name, "Error while loading", trace)))
		return
	except Exception, e:
		raise e
		
	global _raw_event_disabled
	if _raw_event_disabled and plugin.handlesRawEvent():
		_raw_event_disabled = False
		
	global _raw_command_disabled
	if _raw_command_disabled and plugin.handlesRawCommand():
		_raw_command_disabled = False
		
	plugin_data = plugin.getData()
	broadcastEvent(outboundDictionaries.PyRC_Plugin_Load(module_name, plugin_data['name'], plugin_data['version']))
	
def reloadPlugin(module_name):
	"""
	This function reloads a plugin in PyRC's plugin structure. It allows
	developers the ability to modify their scripts without having to restart
	PyRC.

	Caution: Hangs have been reported when reloading plugins with syntax errors
	under Python 2.4.
	
	Prior to reloading, the plugin will be disabled, if it is active.
	After reloading, if the plugin was active, it will be enabled.
	
	On a successful reload, a "Plugin Reloaded" event will be generated.
	
	On an unsuccessful reload, a "Plugin Crash" event will be generated, and the
	plugin will be left in a disabled state.
	
	@type module_path: basestring
	@param module_path: The subpath fragment used to identify the plugin that
	    should be loaded.
	
	@return: Nothing.
	"""
	plugin = _plugins.get(module_name)
	if not plugin: #Unknown plugin specified.
		broadcastEvent(outboundDictionaries.PyRC_Status("'%s' is an unknown plugin. Perhaps it has not been loaded." % module_name))
		return
		
	disabled = None
	try:
		disabled = disablePlugin(module_name, True, _UNLOAD_MODE_RELOAD)
	except:
		return
		
	try:
		plugin.reload()
		plugin_data = plugin.getData()
		broadcastEventAsync(outboundDictionaries.PyRC_Plugin_Reload(module_name, plugin_data['name'], plugin_data['version']))
	except:
		trace = GLOBAL.errlog.grabTrace()
		plugin_data = plugin.getData()
		broadcastEvent(outboundDictionaries.PyRC_Plugin_Crash(trace, module_name, plugin_data['name'], plugin_data['version'], {}, GLOBAL.errlog.logError(GLOBAL.PTH_PLUGIN_SUBPATH, module_name, "Error during reload()")))
		return
		
	if disabled:
		enablePlugin(module_name, _LOAD_MODE_RELOAD)
		
def disablePlugin(module_name, subprocess=False, unload_mode=_UNLOAD_MODE_DISABLE):
	"""
	This function disables a plugin in PyRC's plugin structure. This prevents
	the plugin from receiving future events, and it calls its unloadMe()
	function.
	
	Following disablement, if the plugin processed raw events, all plugins will
	be polled to find out if anything still needs raw events.
	
	On a successful disable, a "Plugin Disabled" event will be generated.
	
	On an unsuccessful disable, a "Plugin Crash" event will be generated, and
	the	plugin will be left in a disabled state.
	
	@type module_path: basestring
	@param module_path: The subpath fragment used to identify the plugin that
	    should be loaded.
	@type subprocess: bool
	@param subprocess: True if this function is being called from a function
	    that needs to know whether it crashed or not.
	@type unload_mode: int
	@param unload_mode: An integer used to identify the type of unload being
	    performed on the plugin.
	
	@return: Nothing.
	
	@raise Exception: If subprocess is set and a plugin fails to be disabled
	    properly.
	"""
	plugin = _plugins.get(module_name)
	if not plugin: #Unknown plugin specified.
		broadcastEvent(outboundDictionaries.PyRC_Status("'%s' is an unknown plugin. Perhaps it has not been loaded." % module_name))
		return
		
	try:
		handled_raw_command = plugin.handlesRawCommand()
		handled_raw_event = plugin.handlesRawEvent()
		
		disabled = plugin.disable(unload_mode)
		
		if handled_raw_command and not _ui.handlesRawCommand():
			global _raw_command_disabled
			continue_raw_commands = False
			for i in _plugins:
				test_plugin = _plugins[i]
				if not test_plugin == plugin and test_plugin.handlesRawCommand():
					continue_raw_commands = True
					break
			if not continue_raw_commands:
				_raw_command_disabled = True
				
		if handled_raw_event and not _ui.handlesRawEvent():
			global _raw_event_disabled
			continue_raw_events = False
			for i in _plugins:
				test_plugin = _plugins[i]
				if not test_plugin == plugin and test_plugin.handlesRawEvent():
					continue_raw_events = True
					break
			if not continue_raw_events:
				_raw_event_disabled = True
				
		plugin_data = plugin.getData()
		if subprocess:
			broadcastEventAsync(outboundDictionaries.PyRC_Plugin_Disable(module_name, plugin_data['name'], plugin_data['version']))
		else:
			broadcastEvent(outboundDictionaries.PyRC_Plugin_Disable(module_name, plugin_data['name'], plugin_data['version']))
			
		return disabled
	except Exception, e:
		trace = GLOBAL.errlog.grabTrace()
		plugin_data = plugin.getData()
		broadcastEvent(outboundDictionaries.PyRC_Plugin_Crash(trace, module_name, plugin_data['name'], plugin_data['version'], {}, GLOBAL.errlog.logError(GLOBAL.PTH_PLUGIN_SUBPATH, module_name, "Error in unloadMe()")))
		
		if subprocess:
			raise e
			
def enablePlugin(module_name, load_mode=_LOAD_MODE_ENABLE):
	"""
	This function enables a plugin in PyRC's plugin structure. This allows the
	plugin to receive future events, and it calls its loadMe() function.
	
	Following enablement, if the plugin processes raw events, raw event
	generation will be restored, assuming it was halted when the plugin was
	disabled.
	
	On a successful enable, a "Plugin Enabled" event will be generated.
	
	On an unsuccessful enable, a "Plugin Crash" event will be generated, and
	the	plugin will be left in a disabled state.
	
	@type module_name: basestring
	@param module_name: The subpath fragment used to identify the plugin that
	    should be loaded.
	@type load_mode: int
	@param load_mode: An integer used to identify the type of load being
	    performed on the plugin.
	
	@return: Nothing.
	"""
	plugin = _plugins.get(module_name)
	if not plugin: #Unknown plugin specified.
		broadcastEvent(outboundDictionaries.PyRC_Status("'%s' is an unknown plugin. Perhaps it has not been loaded." % module_name))
		return
		
	try:
		plugin.enable(load_mode)
		
		global _raw_event_disabled
		if _raw_event_disabled and plugin.handlesRawEvent():
			_raw_event_disabled = False
			
		global _raw_command_disabled
		if _raw_command_disabled and plugin.handlesRawCommand():
			_raw_command_disabled = False
			
		plugin_data = plugin.getData()
		broadcastEvent(outboundDictionaries.PyRC_Plugin_Enable(module_name, plugin_data['name'], plugin_data['version']))
	except:
		trace = GLOBAL.errlog.grabTrace()
		plugin_data = plugin.getData()
		broadcastEvent(outboundDictionaries.PyRC_Plugin_Crash(trace, module_name, plugin_data['name'], plugin_data['version'], {}, GLOBAL.errlog.logError(GLOBAL.PTH_PLUGIN_SUBPATH, module_name, "Error in loadMe()")))
		
def listAllPlugins():
	"""
	This function returns a list of module names, one for each plugin identified
	by PyRC.
	
	@rtype: tuple
	@return: A list of module names.
	"""
	plugin_list = []
	
	pth_user_plugins = GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH + os.sep
	#Check all plugins installed by the user.
	for i in os.listdir(pth_user_plugins):
		if os.path.isfile(pth_user_plugins + i + os.sep + GLOBAL.PTH_PLUGIN_MAIN_MODULE + GLOBAL.PTH_PLUGIN_MAIN_EXTENSION):
			plugin_list.append(i)
			
	pth_root_plugins = GLOBAL.PTH_DIR_PyRC_ROOT + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH + os.sep
	#Check all plugins installed globally.
	for i in os.listdir(pth_root_plugins):
		if not i in plugin_list: #Don't add what's already been found.
			if os.path.isfile(pth_root_plugins + i + os.sep + GLOBAL.PTH_PLUGIN_MAIN_MODULE + GLOBAL.PTH_PLUGIN_MAIN_EXTENSION):
				plugin_list.append(i)
				
	return tuple(plugin_list)
	
def listLoadedPlugins():
	"""
	This function iterates through all loaded plugins and returns a dictionary
	of module names paired with their given name, version, online/offline
	states,	author-provided data dictionary, and module.
	
	@rtype: dict
	@return: A dictionary of the following form::
	 {
	  <module_name:unicode>: {
	   'pluginname': <plugin_name:basestring>,
	   'version': <plugin_version:basestring>,
	   'enabled': <enabled:bool>,
	   'data': <plugin_data:dict>,
	   'plugin': <main_module:module>
	  }
	 }
	"""
	plugin_list = {}
	for i in _plugins:
		module_data = _plugins[i].getData()
		plugin_list[i] = {
		 'module': module_data['name'],
		 'version': module_data['version'],
		 'enabled': _plugins[i].isOnline(),
		 'data': module_data,
		 'plugin': _plugins[i].getPlugin()
		}
	return plugin_list
	
def listUnloadedPlugins():
	"""
	This function iterates through all plugins that are known to PyRC, then
	eliminates those that are already loaded.
	
	@rtype: tuple
	@return: A list of module names.
	"""
	return tuple([i for i in listAllPlugins() if not i in _plugins])
	
def handlesRawCommand():
	"""
	This function is used by PyRC's IAL to determine whether "Raw Command"
	dictionaries should be generated and sent to the plugin chain.
	
	@rtype: bool
	@return: True if "Raw Command" dictionaries should be generated.
	"""
	return _raw_command_ui_override or not _raw_command_disabled
	
def handlesRawEvent():
	"""
	This function is used by PyRC's IAL to determine whether "Raw Event"
	dictionaries should be generated and sent to the plugin chain.
	
	@rtype: bool
	@return: True if "Raw Event" dictionaries should be generated.
	"""
	return _raw_event_ui_override or not _raw_event_disabled
	
def toggleRawCommandHandling(enable):
	"""
	This function is used to allow UIs to turn "Raw Command" Event Dictionary
	processing on after PyRC is already running.
	
	Note: If the UI was started with "Raw Command" handling enabled, this
	function will do nothing.
	
	@type enable: bool
	@param enable: True if "Raw Command" handling should be enabled, False to
	    disable.
	
	@return: Nothing.
	"""
	global _raw_command_ui_override
	_raw_command_ui_override = enable
	
def toggleRawEventHandling(enable):
	"""
	This function is used to allow UIs to turn "Raw Event" Event Dictionary
	processing on after PyRC is already running.
	
	Note: If the UI was started with "Raw Event" handling enabled, this function
	will do nothing.
	
	@type enable: bool
	@param enable: True if "Raw Event" handling should be enabled, False to
	    disable.
	
	@return: Nothing.
	"""
	global _raw_event_ui_override
	_raw_event_ui_override = enable
	
def broadcastEvent(dictionary, skip_ui=False, skip_plugins=False):
	"""
	This function passes an Event Dictionary to the plugins managed by PyRC.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to send to each plugin.
	@type skip_ui: bool
	@param skip_ui: True if the UI should not see this event.
	@type skip_plugins: bool
	@param skip_plugins: True if all non-UI plugins should not see this event.
	
	@return: Nothing.
	"""
	if not _time_to_die: #If PyRC is closing, ignore this event.
		for i in _plugins:
			if skip_plugins:
				break
			plugin = _plugins[i]
			
			#Unwrap the dictionary, if applicable.
			unwrapped = False
			if dictionary['eventname'] == "Emit Known":
				unwrapped = True
				dictionary = dictionary['eventdict']
				
			#Process the dictionary.
			try:
				(action_code, result_dictionary) = processResult(plugin.processDictionary(dictionary, unwrapped))
				if not action_code == _ENUM_ACTION_CODES.NORMAL:
					if action_code == _ENUM_ACTION_CODES.REPLACE:
						dictionary = result_dictionary
					elif action_code == _ENUM_ACTION_CODES.SKIP_REST:
						dictionary = result_dictionary
						skip_plugins = True
						break
					elif action_code == _ENUM_ACTION_CODES.SKIP_ALL:
						skip_plugins = True
						skip_ui = True
						break
			except:
				try:
					trace = GLOBAL.errlog.grabTrace()
					plugin_data = plugin.getData()
					broadcastEventAsync(outboundDictionaries.PyRC_Plugin_Crash(trace, plugin.getName(), plugin_data['name'], plugin_data['version'], dictionary, GLOBAL.errlog.logErrorPlugin(GLOBAL.PTH_PLUGIN_SUBPATH, plugin_data, plugin.getName(), dictionary, trace)))
				except:
					pass
					
			#Rewrap the dictionary, if applicable.
			if unwrapped:
				dictionary = {
				 'eventname': "Emit Known",
				 'eventdict': dictionary
				}
				
		#Handle wrapped events.
		if not skip_plugins:
			if dictionary['eventname'] == "Emit Generic":
				GLOBAL.irc_interface.processDictionary({
				 'eventname': "Raw Command",
				 'irccontext': dictionary['irccontext'],
				 'data': dictionary['message']
				})
				skip_ui = True
			elif dictionary['eventname'] == "Emit Known":
				GLOBAL.irc_interface.processDictionary(dictionary['eventdict'])
				skip_ui = True
				
		#Handle UI processing.
		if not skip_ui:
			try:
				if not _ui.handlesRawEvent() and dictionary['eventname'] == "Raw Event":
					return
				if not _ui.handlesRawCommand() and dictionary['eventname'] == "Raw Command":
					return
				_ui.processDictionary(dictionary)
			except:
				try:
					trace = GLOBAL.errlog.grabTrace()
					plugin_data = _ui.getData()
					broadcastEvent(outboundDictionaries.PyRC_Plugin_Crash(trace, _ui.getName(), plugin_data['name'], plugin_data['version'], dictionary, GLOBAL.errlog.logErrorPlugin(GLOBAL.PTH_PLUGIN_SUBPATH, plugin_data, _ui.getName(), dictionary, trace)))
				except:
					pass
					
def broadcastEventAsync(dictionary):
	"""
	This function allows a dictionary to be broadcasted to all plugins using a
	one-shot thread. It should be used only in cases where a worker thread
	cannot reasonably wait for an event to complete.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to be broadcasted to all plugins.
	
	@return: Nothing.
	"""
	pyrc_common.asynch.AsyncherSingleArg(broadcastEvent, dictionary).start()
	
	
def processResult(dictionary):
	"""
	This function processes the value returned by a plugin following its receipt
	of an event dictionary.
		
	It is here that Raise Event Dictionaries are processed.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to be processed.
	
	@rtype: tuple
	@return: A tuple containing an _ENUM_ACTION_CODES.EnumValue and a
	    replacement Event Dictionary, if applicable.
	"""
	if dictionary:
		if dictionary['behaviour'] == "replace":
			return (_ENUM_ACTION_CODES.REPLACE, dictionary['eventdict'])
		elif dictionary['behaviour'] == "skiprest":
			return (_ENUM_ACTION_CODES.SKIP_REST, dictionary['eventdict'])
		elif dictionary['behaviour'] == "skipall":
			return (_ENUM_ACTION_CODES.SKIP_ALL, None)
	else:
		return (_ENUM_ACTION_CODES.NORMAL, None)
		
def killAll():
	"""
	This function unloads all plugins in use by PyRC.
	
	It should be called only when PyRC is closing, and it must be called from a
	non-daemonic context.
	
	@return: Nothing.
	"""
	#Disable all event processing.
	global _time_to_die
	_time_to_die = True
	
	#Build a list of all plugins and the UI and call their unload() functions.
	active_list = [pyrc_common.asynch.Asyncher(_ui.unload)]
	for i in _plugins:
		active_list.append(pyrc_common.asynch.Asyncher(_plugins[i].unload))
		
	for i in active_list:
		i.start()
		
	#While any plugins are still being unloaded, wait.
	inactive_list = []
	while True:
		#Remove all unloaded plugins from the list to reduce processing time.
		for i in inactive_list:
			active_list.remove(i)
		inactive_list = []
		
		if not active_list: #All plugins have been unloaded.
			break
			
		time.sleep(0.1)
		
		for i in active_list:
			if i.isAlive(): #At least one plugin is still waiting, so keep going.
				break
			else:
				inactive_list.append(i)
				
				
class _PluginPrototype(object):
	"""
	This class serves as a wrapper for plugins within PyRC's plugin
	architecture. It cannot be instantiated directly; use _Plugin or _UI.
	"""
	_module_name = None #: A string containing the path fragment that identifies this plugin.
	_module = None #: A reference to the main module of this plugin.
	_lock = None #: A threading.Lock object used to prevent multiple simultaneous accesses to this plugin.
	_processes_raw_command = False #: True if this plugin handles raw commands. False otherwise.
	_processes_raw_event = False #: True if this plugin handles raw events. False otherwise.
	
	def _init_(self, module_name, file_name, paths, subpath, tolerate_fault):
		"""
		This function provides the actual loading handling for plugins.
		
		@type module_name: basestring
		@param module_name: The path fragment that identifies the module to be
		    loaded.
		@type file_name: basestring
		@param file_name: The name of the Python module to load, such as "main"
		    for "main.py".
		@type paths: list
		@param paths: A list of paths to search when trying to find the Python
		    module to load.
		@type subpath: basestring
		@param subpath: The subpath in which searching should occur; this is
		    always 'uis' or 'plugins', unless the global constants change.
		@type tolerate_fault: bool
		@param tolerate_fault: If True, any raised exceptions will be simplified
		    for displaying to the user. If False, the full error will be raised,
		    allowing for a complete stack trace.
		
		@return: Nothing.
		
		@raise PluginLoadError: If tolerate_fault is set and an error occurs
		    while loading or processing the UI.
		@raise OSError: If the plugin's data path could not be created.
		@raise Exception: If tolerate_fault is not set and an error occurs while
		    loading or processing the UI.
		"""
		try:
			(self._module, path) = self._load(file_name, paths, subpath, module_name)
			self._module.__module_path__ = path
			self._module._data_path = GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_CONFIG_SUBPATH + os.sep + subpath + os.sep + self._module_name + os.sep
		except Exception, e:
			if tolerate_fault:
				raise PluginLoadError(u"Failed to load '%s': %s" % (self._module_name, str(e)))
			else:
				raise e
				
		if not os.path.isdir(self._module._data_path):
			os.mkdir(self._module._data_path, 0700)
			
	def _load(self, name, paths, subpath, module_name):
		"""
		This function attempts to load a plugin for use by PyRC.
		
		It works by trying to arbitrarily pull a Python script from the
		filesystem into PyRC's interpreter and binding it to this _UI object.
		
		@type name: basestring
		@param name: The name of the Python module to load, such as "main" for
		    "main.py".
		@type paths: list
		@param paths: A list of paths to search when trying to find the Python
		    module to load.
		@type subpath: basestring
		@param subpath: The subpath in which searching should occur; this is
		    always 'uis' or 'plugins', unless the global constants change.
		@type module_name: basestring
		@param module_name: The path fragment that identifies the module to be
		    loaded.
		
		@rtype: tuple
		@return: The loaded module and the path in which it was found.
			
		@raise ImportError: If a problem occurs while locating the module.
		@raise Exception: If a problem occurs while loading the module.
		"""
		path = None
		try:
			file, file_path, description = imp.find_module(name, paths)
			file.close()
			
			path = os.path.split(file_path)[0] + os.sep
			sys.path.insert(0, path)
			
			module = __import__(os.path.join(subpath, module_name, name), globals(), locals(), [''])
			sys.modules[file_path] = module
			
			return (module, path)
		except Exception, e:
			if path:
				sys.path.remove(path)
				
			raise e
				
	def unload(self):
		"""
		This function is called when the plugin should be unloaded from PyRC's
		plugin architecture.
		
		@return: Nothing.
		
		@raise Exception: If a problem occurs while unloading the module.
		"""
		try:
			self._lock.acquire()
			self._module.unloadMe(GLOBAL.irc_interface.processDictionary)
		finally:
			self._lock.release()
			
	def getData(self):
		"""
		This function returns the author-provided meta-data for the plugin.
		
		It will contain the following elements::
		 'name': <plugin_name:basestring>
		 'version: <plugin_version:basestring>
		
		It may contain the following elements::
		 'author': <plugin_author:basestring>
		 'e-mail': <authors_email:basestring>
		
		No other elements are currently specified in the PyRC plugin specs,
		though the author is free to store any information they would like to
		make known to other plugins.
		
		@rtype: dict
		@return: A dictionary containing author-provided meta-data.
		"""
		return self._module.__module_data__
		
	def getName(self):
		"""
		This function returns the plugin's module name.
		
		@rtype: unicode
		@return: The plugin's module name.
		"""
		return self._module_name
		
	def getPlugin(self):
		"""
		This function returns the plugin's main module.
		
		@rtype: module
		@return: The plugin's main module.
		"""
		return self._module
		
	def handlesRawCommand(self):
		"""
		This function is used to determine whether this plugin processes raw
		commands or not.
		
		@rtype: bool
		@return: True if this plugin handles raw commands; False otherwise.
		"""
		try:
			self._lock.acquire()
			return self._processes_raw_command
		finally:
			self._lock.release()
			
	def handlesRawEvent(self):
		"""
		This function is used to determine whether this plugin processes raw
		events or not.
		
		@rtype: bool
		@return: True if this plugin handles raw events; False otherwise.
		"""
		try:
			self._lock.acquire()
			return self._processes_raw_event
		finally:
			self._lock.release()
			
	def processDictionary(self, dictionary):
		"""
		This function is called when an Event Dictionary is available for
		processing.
		
		@type dictionary: dict
		@param dictionary: The Event Dictionary to be processed.
		
		@return: Nothing.
		"""
		try:
			self._lock.acquire()
			self._module.hookEvent(dictionary, GLOBAL.irc_interface.processDictionary)
		finally:
			self._lock.release()
			
			
class _Plugin(_PluginPrototype):
	"""
	This class serves as a wrapper for plugins within PyRC's plugin
	architecture.
	
	It is instantiated once per plugin loaded by PyRC.
	"""
	_handlers = None #: A dictionary of functions used to handle Event Dictionaries, keyed by eventname and unwrapped status.
	_online = True #: True if this plugin is enabled and ready to receive events.
	
	def __init__(self, module_name, file_name, paths, subpath, tolerate_fault):
		"""
		This function is invoked when a new _Plugin object is created.
		
		@type module_name: basestring
		@param module_name: The path fragment that identifies the module to be
		    loaded.
		@type file_name: basestring
		@param file_name: The name of the Python module to load, such as "main"
		    for "main.py".
		@type paths: list
		@param paths: A list of paths to search when trying to find the Python
		    module to load.
		@type subpath: basestring
		@param subpath: The subpath in which searching should occur; this is
		    always 'plugins', unless the global constant changes.
		@type tolerate_fault: bool
		@param tolerate_fault: If True, any raised exceptions will be simplified
		    for displaying to the user. If False, the full error will be raised,
		    allowing for a complete stack trace.
		
		@return: Nothing.
		
		@raise PluginLoadError: If tolerate_fault is set and an error occurs
		    while loading or processing the plugin.
		@raise OSError: If the plugin's data path could not be created.
		@raise Exception: If tolerate_fault is not set and an error occurs while
		    loading or processing the plugin.
		"""
		self._lock = threading.Lock()
		self._module_name = module_name
		self._handlers = {}
		
		self._init_(module_name, file_name, paths, subpath, tolerate_fault)
			
		try:
			self._loadModule(_LOAD_MODE_FIRST)
		except Exception, e:
			if tolerate_fault:
				raise PluginLoadError(u"Plugin '%s' did not conform to specs: %s" % (self._module_name, str(e)))
			else:
				raise e
				
	def _loadModule(self, load_mode):
		"""
		This function is used to load the plugin, enabling it to process Event
		Dictionaries.
		
		All handlers will be generated by this function.
		
		@type load_mode: int
		@param load_mode: An integer used to identify the type of load being
			performed on the plugin.
		
		@return: Nothing.
		
		@raise Exception: If a problem occurs during the enabling process.
		"""
		for i in self._module.loadMe(GLOBAL.irc_interface.processDictionary, load_mode):
			self._handlers[(i[0], i[2])] = i[1]
			if not self._processes_raw_event and i[0] == "Raw Event":
				self._processes_raw_event = True
			if not self._processes_raw_command and i[0] == "Raw Command":
				self._processes_raw_command = True
				
	def reload(self):
		"""
		This function is used to reload the plugin, allowing developers to
		load new code.
		
		Caution: In Python 2.4, hangs have been reported when reloading modules
		with syntax errors.
		
		@return: Nothing.
		
		@raise Exception: If a problem occurs during the reloading process.
		"""
		try:
			self._lock.acquire()
			self._module = reload(self._module)
		finally:
			self._lock.release()
			
	def unload(self):
		"""
		This function is called when the plugin should be unloaded from PyRC's
		plugin architecture.
		
		@return: Nothing.
		"""
		try:
			self.disable(_UNLOAD_MODE_DISABLE)
		except:
			pass
			
	def disable(self, unload_mode):
		"""
		This function is used to disabled the plugin, preventing it from
		processing Event Dictionaries.
		
		If the plugin was already disabled, this function will do nothing.
		
		All handlers will be unbound by this function.
		
		@type unload_mode: int
		@param unload_mode: An integer used to identify the type of unload being
			performed on the plugin.
		
		@rtype: bool
		@return: True if the plugin was disabled; False if the plugin was
		    already disabled.
		
		@raise Exception: If a problem occurs during the disabling process.
		"""
		try:
			self._lock.acquire()
			if not self._online: #Already disabled.
				return False
				
			self._online = False
			self._processes_raw_command = False
			self._processes_raw_event = False
			self._handlers = {}
			
			self._module.unloadMe(GLOBAL.irc_interface.processDictionary, unload_mode)
			return True
		finally:
			self._lock.release()
			
	def enable(self, load_mode):
		"""
		This function is used to enable the plugin, restoring its ability to
		process Event Dictionaries.
		
		If the plugin was already enabled, this function will do nothing.
		
		All handlers will be regenerated by this function.
		
		@type load_mode: int
		@param load_mode: An integer used to identify the type of load being
			performed on the plugin.
		
		@rtype: bool
		@return: True if the plugin was enabled; False if the plugin was already
		    enabled.
		
		@raise Exception: If a problem occurs during the enabling process.
		"""
		try:
			self._lock.acquire()
			if self._online: #Already enabled.
				return False
				
			self._loadModule(load_mode)
			
			self._online = True
			return True
		finally:
			self._lock.release()
			
	def isOnline(self):
		"""
		This function is used to determine whether this plugin is able to accept
		events or not.
		
		@rtype: bool
		@return: True if this plugin is online; False otherwise.
		"""
		return self._online
			
	def processDictionary(self, dictionary, unwrapped):
		"""
		This function is called when an Event Dictionary is available for
		processing.
		
		If this plugin has a handler for the received dictionary's type, it will
		be used. Else, the dictionary will be ignored.
		
		If this plugin is offline, the dictionary will not be processed.
		
		@type dictionary: dict
		@param dictionary: The Event Dictionary to be processed.
		@type unwrapped: bool
		@param unwrapped: True if the dictionary was in an Emit Known wrapper or
		    False if the dictionary came from an IRC network.
		
		@rtype: dict|None
		@return: None if the dictionary is unprocessed or if the handler did not
		    attempt to alter the processing flow. A Raise Event Dictionary if
		    the dictionary's processing flow is supposed to be altered.
		"""
		try:
			self._lock.acquire()
			
			if self._online:
				handler = self._handlers.get((dictionary['eventname'], unwrapped))
				if not handler:
					return
					
				return handler(dictionary.copy(), GLOBAL.irc_interface.processDictionary)
		finally:
			self._lock.release()
			
			
class _UI(_PluginPrototype):
	"""
	This class serves as a wrapper for UIs within PyRC's plugin
	architecture.
	
	It is instantiated once per session.
	"""
	_startup_function = None #: The function that launches the UI's actual frontend.
	
	def __init__(self, module_name, file_name, paths, subpath, tolerate_fault):
		"""
		This function is invoked when a new _UI object is created.
		
		If no UI is specified, the built-in RawUI will be loaded.
		
		@type module_name: basestring
		@param module_name: The path fragment that identifies the module to be
		    loaded.
		@type file_name: basestring
		@param file_name: The name of the Python module to load, such as "main"
		    for "main.py".
		@type paths: list
		@param paths: A list of paths to search when trying to find the Python
		    module to load.
		@type subpath: basestring
		@param subpath: The subpath in which searching should occur; this is
		    always 'uis', unless the global constant changes.
		@type tolerate_fault: bool
		@param tolerate_fault: If True, any raised exceptions will be simplified
		    for displaying to the user. If False, the full error will be raised,
		    allowing for a complete stack trace.
		
		@return: Nothing.
		
		@raise PluginLoadError: If tolerate_fault is set and an error occurs
		    while loading or processing the UI.
		@raise OSError: If the plugin's data path could not be created.
		@raise Exception: If tolerate_fault is not set and an error occurs while
		    loading or processing the UI.
		"""
		self._lock = threading.Lock()
		self._module_name = module_name
		
		if module_name == GLOBAL.PTH_RAW_UI:
			import raw_ui
			self._module = raw_ui
		else:
			self._init_(module_name, file_name, paths, subpath, tolerate_fault)
			
		(self._processes_raw_command, self._processes_raw_event, self._startup_function) = self._module.loadMe(GLOBAL.irc_interface.processDictionary)
		
	def getStartupFunction(self):
		"""
		This function is used to retrieve the function that launches the UI's
		frontend, if one is specified.
		
		@rtype: function|None
		@return: The startup function specified or None if loadMe() handles
		    everything.
		"""
		return self._startup_function
		
		
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
		self.description = unicode(description)
		
		
class PluginLoadError(Error):
	"""
	This class represents problems that might occur when trying to load a plugin.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new PluginLoaderror object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		Error.__init__(self, description)
		
