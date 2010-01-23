"""
 PyRC plugin: PyRC-GUI
 Purpose: Provide a default GUI for PyRC.
 
 Changelog (brief):
  0.0.1 (19/1/05):
   main.py created.
  
  
 All code, unless otherwise indicated, is original, and subject to the terms of
  the attached licensing agreement.

 Copyright (c) 2004-2005, Neil Tallim
 
 PyRC-GUI is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 
 PyRC-GUI is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with this script; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
__module_data__={
 'name': "PyRC-GUI",
 'version': "0.0.1",
 'author': "Neil Tallim",
 'e-mail': "red.hamsterx@gmail.com"
}

import windows

def _generateEvents():
	events = {}
	
	return events
	
_events = _generateEvents() #: A dictionary of functions used to handle events from the IAL, keyed by eventname.
del _generateEvents
	
def initialise(ial):
	windows.initialise(ial, __module_path__)
	
def hookEvent(dictionary, ial):
	handler = _events.get(dictionary['eventname'])
	if handler:
		handler(dictionary, ial)
	else:	
		print dictionary
		
def loadMe(ial):
	return (False, False, initialise)
	
def unloadMe(ial):
	#Currently, nothing can be saved.
	pass
	