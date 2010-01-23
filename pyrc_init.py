# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_init

Purpose
=======
 House complicated initialisation routines that would look ugly and take
 unnecessary space in the main init script.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2006-2007
"""
import os
import os.path
import sys

import pyrc_common.GLOBAL as GLOBAL

def buildUserProfilePaths():
	"""
	This function is used to generate PyRC's directory structure.
	
	If any directories already exist, they will be ignored. Else, they will be
	created.
	
	@return: Nothing.
	
	@raise Exception: If an error occurs while accessing the filesystem.
	"""
	def buildPath(path):
		if not os.path.isdir(path):
			os.mkdir(path, 0700)
			
	map(buildPath, (
	 GLOBAL.PTH_DIR_USER_ROOT,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_UI_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_ERROR_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_ERROR_SUBPATH + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_ERROR_SUBPATH + os.sep + GLOBAL.PTH_UI_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_ERROR_SUBPATH + os.sep + GLOBAL.PTH_MODULE_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_CONFIG_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_CONFIG_SUBPATH + os.sep + GLOBAL.PTH_PLUGIN_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_CONFIG_SUBPATH + os.sep + GLOBAL.PTH_UI_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_CONFIG_SUBPATH + os.sep + GLOBAL.PTH_MODULE_SUBPATH,
	 GLOBAL.PTH_DIR_USER_ROOT + os.sep + GLOBAL.PTH_LOG_SUBPATH
	))
	
def identifyPlatform():
	"""
	This function is used to determine the operating system on which PyRC is
	running.
	
	This function sets the following global constants::
	 ENV_PLATFORM
	 ENV_ARCHITECTURE
	 ENV_IS_MICROSOFT
	
	This code is based on a Python-licensed example at
	http://mail.python.org/pipermail/distutils-sig/2000-September/001466.html
	
	@return: Nothing.
	"""
	is_microsoft = False
	if os.name == "posix":
		(os_version, host, release, version, machine) = os.uname()
		architecture = None
		if machine in ['i386', 'i468', 'i586', 'i686']:
			architecture = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.x86
		elif machine == 'x86_64':
			architecture = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.x86_64
		elif machine == 'sparc':
			architecture = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.sparc
		elif machine == 'ppc':
			architecture = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.ppc
		elif machine == 'alpha':
			architecture = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.alpha
		else:
			architecture = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.unknown
			
		platform_name = os_version.lower()
		if platform_name == "linux":
			platform_name = "Linux %s[%s]" % (release, machine)
		elif platform_name == "sunos":
			if int(release[0]) >= 5:
				os_version = "Solaris"
				release = "%d.%s" % (int(release[0]) - 3, release[2:])
			platform_name = "%s %s %s" % (os_version, release, machine)
		elif platform_name == "irix":
			platform_name = "Irix %s" % release
		else:
			platform_name = "%s %s %s" % (os_version, release, machine)
			
		GLOBAL.ENV_PLATFORM = platform_name
		GLOBAL.ENV_ARCHITECTURE = architecture
		GLOBAL.ENV_IS_MICROSOFT = is_microsoft
	else:
		platform_name = None
		if os.name in ("nt", "ce"):
			is_microsoft = True
			windows_details = sys.getwindowsversion()
			windows_version = "%i.%i" % (windows_details[0], windows_details[1])
			if windows_details[3] == 0:
				platform_name = winVersion
			elif windows_details[3] == 1:
				platform_name = "9x (%s)" % windows_version
			elif windows_details[3] == 2:
				if windows_details[0] == 5:
					if windows_details[1] == 0:
						platform_name = "2000"
					elif windows_details[1] == 1:
						platform_name = "XP"
					elif windows_details[1] == 2:
						platform_name = "2003"
					else:
						platform_name = "NT%s" % windows_version
				else:
					platform_name = "NT%s" % windows_version
			elif windows_details[3] == 3:
				platform_name = "CE"
			else:
				platform_name == "Unknown"
			platform_name = "Microsoft(r) Windows(r) %s" % platform_name
		else:
			platform_name = sys.platform
			
		GLOBAL.ENV_PLATFORM = platform_name
		GLOBAL.ENV_ARCHITECTURE = GLOBAL.ENUM_PLATFORM_ARCHITECTURE.x86
		GLOBAL.ENV_IS_MICROSOFT = is_microsoft
		
def setRootPaths():
	"""
	This function is used to set PyRC's root and user paths, which are needed
	for pretty much all file access.
	
	This function sets the following global constants::
	 PTH_DIR_PyRC_ROOT
	 PTH_DIR_USER_ROOT
	
	@return: Nothing.
	"""
	#Assume PyRC is in PATH or this is Microsoft Windows.
	main_path = sys.modules['__main__'].__file__
	pth_PyRC_root = main_path[:-(len(main_path) - main_path.rfind(os.sep))]
	
	def _getPyRCRoot(path):
		#This function tests to see whether PyRC's main path is at or below '.'.
		#It should never need to be called, but it was used during development.
		if path == '.':
			path = None
		current_path = os.path.abspath(".")
		if path:
			current_path += os.sep + path
			
		return current_path
		
	if not pth_PyRC_root: #Windows
		pth_PyRC_root = _getPyRCRoot(pth_PyRC_root)
	elif pth_PyRC_root[0] != '/': #Unix, non-absolute.
		pth_PyRC_root = _getPyRCRoot(pth_PyRC_root)
		
	GLOBAL.PTH_DIR_PyRC_ROOT = pth_PyRC_root
	GLOBAL.PTH_DIR_USER_ROOT = os.path.expanduser("~/.PyRC")
	