"""
 PyRC-GUI module: windowObjectsResources
 Purpose: Provide a central location for all non-window objects used to support
  windows.
  
 All code, unless otherwise indicated, is original, and subject to the terms of
  the attached licensing agreement.
 
 (C) Neil Tallim, 2005-2006

 This module falls under the terms of the license stipulated in main.py, which
  you should have received with it.
"""

import gtk

PIXBUFS = None #: A dictionary of pixbuf icons, keyed by symbol.

def loadPixbufs(rootPath):
	smooth = gtk.gdk.pixbuf_new_from_file(rootPath + '/icons/gui-smooth.png')
	
	global PIXBUFS
	PIXBUFS = {
	 '+': gtk.gdk.pixbuf_new_from_file(rootPath + '/icons/gui-yellow.png'),
	 '%': gtk.gdk.pixbuf_new_from_file(rootPath + '/icons/gui-orange.png'),
	 '@': gtk.gdk.pixbuf_new_from_file(rootPath + '/icons/gui-red.png'),
	 '&': gtk.gdk.pixbuf_new_from_file(rootPath + '/icons/gui-blue.png'),
	 '~': gtk.gdk.pixbuf_new_from_file(rootPath + '/icons/gui-mono.png'),
	 '^': smooth,
	 '*': smooth,
	}
	
class Context: #In heavy development.
	def __init__(self, iter, name, context_id):
		self._iter = iter
		self._name = name #Focus
		self._context_id = context_id #irc context
		self._buffer = gtk.TextBuffer()
		
	def getBuffer(self):
		return self._buffer
		
	def getContextID(self):
		return self._context_id
		
	def getIter(self):
		return self._iter
		
	def getName(self):
		return self._name
		
	def setName(self, name):
		self._name = name
		