# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.errlog

Purpose
=======
 Provide facilities for trapping and recording errors.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import os
import os.path
import sys
import traceback
import time

import GLOBAL

def grabTrace():
	"""
	This function returns the most recent stack trace PyRC's interpreter generated.
	
	@rtype: tuple
	@return: A line-by-line list of the most recent stack trace.
	"""
	try:
		(type, value, trace) = sys.exc_info() 
		filtered_trace = []
		for i in traceback.format_exception(type, value, trace):
			filtered_trace.append(i[:-1])
		return tuple(filtered_trace)
	except:
		return ()
		
def logErrorPlugin(path, plugin_data, module_name, dictionary, trace=None):
	"""
	This function writes a stack trace to a logfile when a plugin crashes.
	
	@type path: basestring
	@param path: The subpath of the plugin that crashed, either 'uis' or
	    'plugins'.
	@type plugin_data: dict
	@param plugin_data: The author-provided meta-data of the plugin.
	@type module_name: unicode
	@param module_name: The PyRC-registered name of the plugin that crashed.
	@type dictionary: dict
	@param dictionary: The Event Dictionary that caused this crash.
	@type trace: basestring|None
	@param trace: The stack trace of the crash, if previously grabbed.
	
	@rtype: unicode
	@return: The path of the logfile where the error was recorded, or a
	    description of the problem if logging failed.
	"""
	log_path = "logfile because PyRC is shutting down"
	try:
		log_path = os.path.join(GLOBAL.PTH_DIR_USER_ROOT, GLOBAL.PTH_ERROR_SUBPATH, path, module_name + GLOBAL.PTH_ERROR_LOGFILE_EXTENSION)
		error_log = open(log_path, 'a')
		try:
			error_log.write("%s v.%s crashed -- Unknown reason [%s]%s" % (plugin_data['name'], plugin_data['version'], time.asctime(), GLOBAL.ENV_LINEBREAK))
			
			error_log.write(_generateSeparator())
			if not trace:
				trace = grabTrace()
			if trace:
				for i in trace:
					error_log.write("%s%s" % (i, GLOBAL.ENV_LINEBREAK))
			else:
				error_log.write("Unable to grab trace.%s" % GLOBAL.ENV_LINEBREAK)
				
			error_log.write("%sThe dictionary responsible was:%s" % (GLOBAL.ENV_LINEBREAK, GLOBAL.ENV_LINEBREAK))
			error_log.write(str(dictionary))
			if 'author' in plugin_data:
				error_log.write(GLOBAL.ENV_LINEBREAK * 2)
				
				error_log.write("Contact %s" % plugin_data['author'])
				if 'e-mail' in plugin_data:
					error_log.write(" at %s" % plugin_data['e-mail'])
				error_log.write(" if you have a patch or wish to report this bug.%s" % GLOBAL.ENV_LINEBREAK)
				
				error_log.write(GLOBAL.ENV_LINEBREAK * 3)
		finally:
			error_log.close()
	except:
		log_path = u"Unable to write to %s" % log_path
	return log_path
	
def logError(path, module_name, reason, trace=None):
	"""
	This function writes a stack trace to a logfile when PyRC fails to load a
	module.
	
	@type path: basestring
	@param path: The subpath of the module that failed to load, either 'uis' or
	    'plugins'.
	@type module_name: unicode
	@param module_name: The PyRC-registered name of the module that failed to
	    load.
	@type reason: basestring
	@param reason: A description of the problem that occurred.
	
	@rtype: unicode
	@return: The path of the logfile where the error was recorded, or a
	    description of the problem if logging failed.
	"""
	log_path = "logfile because PyRC is shutting down"
	try:
		log_path = os.path.join(GLOBAL.PTH_DIR_USER_ROOT, GLOBAL.PTH_ERROR_SUBPATH, path, module_name + "-loading" + GLOBAL.PTH_ERROR_LOGFILE_EXTENSION)
		error_log = open(log_path, 'a')
		try:
			error_log.write("Failed to load module -- %s [%s]%s" % (reason, time.asctime(), GLOBAL.ENV_LINEBREAK))
			
			error_log.write(_generateSeparator())
			if not trace:
				trace = grabTrace()
			if trace:
				for i in grabTrace():
					error_log.write("%s%s" % (i, GLOBAL.ENV_LINEBREAK))
			else:
				error_log.write("Unable to grab trace.%s" % GLOBAL.ENV_LINEBREAK)
				
			error_log.write(GLOBAL.ENV_LINEBREAK * 3)
		finally:
			error_log.close()
	except Exception, e:
		log_path = u"Unable to write to %s" % log_path
	return log_path
	
def _generateSeparator():
	return '-' * 80 + GLOBAL.ENV_LINEBREAK
	
