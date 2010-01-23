"""
 PyRC-GUI module: windowObjects
 Purpose: Provide a central location for all GUI objects related to the PyRC-GUI
  ui.
  
 All code, unless otherwise indicated, is original, and subject to the terms of
  the attached licensing agreement.
 
 (C) Neil Tallim, 2005-2006

 This module falls under the terms of the license stipulated in main.py, which
  you should have received with it.
"""

try:
	import pygtk
	pygtk.require('2.0')
	import gtk
except:
	print "Your system doesn't have PyGTK2."
	print "Under Debian GNU/Linux, it is referenced by python-gtk2."
	print "It should have a similar name under other distributions."
	
	import sys
	sys.exit(1)

try:
	import gtk.glade
except:
	print "Your system doesn't have Glade bindings for Python."
	print "Under Debian GNU/Linux, they are referenced by python-glade2."
	print "They should have a similar name under other distributions."
	
	import sys
	sys.exit(1)

import os

import windowResources

import shared.interpreter as interpreter

_GLADE_FILE = "windows.glade" #: The name of the .glade file.
_MODULE_PATH = None #: The path in which the UI's files are located.

_COLOUR_CONTEXT_INACTIVE = 'black'
_COLOUR_CONTEXT_ACTIVE = 'red'
_COLOUR_CONTEXT_HIGHLIGHT = 'blue'

_IAL = None

_win_main = None #: The main window.
_win_nodes = {}
"""
A dictionary containing a collection of all windows built to contain child
IRC nodes.

Its elements have the following structure::
 {<context_id:int>: {<node_name:unicode>: <:window>}}
"""

def initialise(ial, module_path):
	interpreter.initialise(ial)
	
	global _IAL
	_IAL = ial
	
	global _MODULE_PATH
	_MODULE_PATH = module_path
	
	windowResources.loadPixbufs(module_path)
	
	global _win_main
	_win_main = WinMain("PyRC-GUI", 600, 400, 40, 40, None, False)
	
class WinMain(object):
	def __init__(self, title, width, height, networks_size, nicknames_size, colours, maximized):
		#========================================================================
		#The widget tree.
		widget_tree = gtk.glade.XML(_MODULE_PATH + os.sep + _GLADE_FILE, "win_main") 
		
		#========================================================================
		#The core window.
		self._window = widget_tree.get_widget("win_main")
		self._window.resize(width, height)
		self._window.set_title(title)
		
		#========================================================================
		#The first splitter widget.
		self._pne_irc = widget_tree.get_widget("pne_irc")
		self._pne_irc.set_position(networks_size)
		
		#========================================================================
		#The server/channel treeview.
		self._trv_networks = widget_tree.get_widget("trv_networks")
		self._trv_networks.set_property("width-request", 100)
		
		cell_renderer = gtk.CellRendererText()
		trv_column = gtk.TreeViewColumn('Pango Markup', cell_renderer, markup=0)
		trv_column.add_attribute(cell_renderer, 'text', 0)
		trv_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self._trv_networks.append_column(trv_column)
		
		model_networks = gtk.TreeStore(str)
		self._trv_networks.set_model(model_networks)
		
		self._context_status = windowResources.Context(
		 model_networks.append(None, ['<span foreground="%s">Status</span>' % _COLOUR_CONTEXT_INACTIVE]),
		 'Status',
		 0 #Global context.
		)
		self._context_active = self._context_status
		
		self._trv_networks.set_search_column(0)
		
		self._btn_networks = widget_tree.get_widget("btn_networks")
		
		#========================================================================
		#The second, nested, splitter widget.
		self._pne_context = widget_tree.get_widget("pne_context")
		self._pne_context.set_position(self._pne_context.get_allocation().width - nicknames_size)
		
		self._btn_channel = widget_tree.get_widget("btn_channel")
		self._btn_topic = widget_tree.get_widget("btn_topic")
		self._btn_modes = widget_tree.get_widget("btn_modes")
		
		#========================================================================
		#The main chat interface.
		self._txt_chat = widget_tree.get_widget("txt_chat")
		
		buffer_chat = self._context_status.getBuffer()
		self._txt_chat.set_buffer(buffer_chat)
		
		buffer_chat.insert_at_cursor('sometime\t~flan\tlawl, desu\n')
		buffer_chat.insert_at_cursor('sometime2\t~basscaet\tlawl, desu, lorem ipsum, something, something, somethinbg, fjdsakl f jdska; fdjksla fjadksjfkweajlkf fjdsklaf ewajflkf9oewa trahjiuovux jreiu tnrkejhuivhl.znnr  8triuohkczjhuire a hrfjkwnjkehrui vntest\n')
		
		self._btn_nickname = widget_tree.get_widget("btn_nickname")
		self._txt_input = widget_tree.get_widget("txt_input")
		self._btn_send = widget_tree.get_widget("btn_send")
		
		#========================================================================
		#The userlist and latency column.
		self._lst_users = widget_tree.get_widget("lst_users")
		self._lst_users.set_property("width-request", 100)
		
		pixbuf_renderer = gtk.CellRendererPixbuf()
		cell_renderer = gtk.CellRendererText()
		trv_column = gtk.TreeViewColumn()
		trv_column.pack_start(pixbuf_renderer, expand=False)
		trv_column.add_attribute(pixbuf_renderer, 'pixbuf', 0)
		trv_column.pack_start(cell_renderer, expand=True)
		trv_column.add_attribute(cell_renderer, 'text', 1)
		trv_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self._lst_users.append_column(trv_column)
		
		model_users = gtk.ListStore(gtk.gdk.Pixbuf, str)
		self._lst_users.set_model(model_users)
		
		model_users.append([windowResources.PIXBUFS['~'], 'flan'])
		model_users.append([windowResources.PIXBUFS['+'], 'flan2'])
		model_users.append([None, 'flan3'])
		
		self._lst_users.set_search_column(0)
		
		self._lbl_users = widget_tree.get_widget("lbl_users")
		self._lbl_users.set_text("o+1/h0/v0/0 : 1")
		
		self._lbl_ping = widget_tree.get_widget("lbl_ping")
		self._prg_ping_timeout = widget_tree.get_widget("prg_ping_timeout") 
		
		#========================================================================
		#The application menu.
		
		
		#filemenu= wxMenu()
		#filemenu.Append(0, "&Connect"," Connect to an IRC network")
		#filemenu.AppendSeparator()
		#filemenu.Append(1,"E&xit"," Close PyRC")
		
		#menuBar = wxMenuBar()
		#menuBar.Append(filemenu,"&IRC")
		#self._SetMenuBar(menuBar)
		
		
		#========================================================================
		#The status bar.
		self._bar_status = widget_tree.get_widget("bar_status")
		x = self._bar_status.get_context_id("1")
		y = self._bar_status.get_context_id("2")
		self._bar_status.push(x, "1")
		self._bar_status.push(y, "2")
		
		#========================================================================
		#Callback definitions.
		#Handle window destruction events.
		def event_delete(widget, event, data=None):
			gtk.main_quit()
			
			_IAL({'eventname': "PyRC Quit", 'message': None})
			
			return False
		self._window.connect("delete_event", event_delete)
		
		#Handle user text input events.
		def event_process_input(widget, data=None):
			input = self._txt_input.get_text().strip()
			self._txt_input.set_text('')
			
			if input:
				tag = gtk.TextTag()
				tag.set_property("left-margin", 50) #This tag will actually need to be generated on each insert, unfortunately.
				tag.set_property("left-margin-set", True)
				
				self._txt_chat.get_buffer().insert(self._txt_chat.get_buffer().get_end_iter(), '\ndesudesudesu <~flun> ')
				self._txt_chat.get_buffer().insert_with_tags(self._txt_chat.get_buffer().get_end_iter(), input, tag)
		self._txt_input.connect("activate", event_process_input)
		self._btn_send.connect("clicked", event_process_input)
		
		#========================================================================
		#Activation.
		self._window.show()
		gtk.main()
		
	#===========================================================================
	#Extended/convenience functions, mostly referenced from events.
	#Nick change, context highlight, etc.
		
		
class WinChild(object):
	def __init__(self, title, width, height, networks_size, nicknames_size, colours, maximized):
		#========================================================================
		#The widget tree.
		widget_tree = gtk.glade.XML(_MODULE_PATH + os.sep + _GLADE_FILE, "win_child") 
		
		#========================================================================
		#The core window.
		self._window = widget_tree.get_widget("win_child")
		self._window.resize(width, height)
		self._window.set_title(title)
		
		#========================================================================
		#The first splitter widget.
		self._pne_irc = widget_tree.get_widget("pne_irc")
		self._pne_irc.set_position(networks_size)
		
		#========================================================================
		#The server/channel treeview.
		self._trv_networks = widget_tree.get_widget("trc_networks")
		self._trv_networks.set_property("width-request", 100)
		
		cell_renderer = gtk.CellRendererText()
		trv_column = gtk.TreeViewColumn('Pango Markup', cell_renderer, markup=0)
		trv_column.add_attribute(cell_renderer, 'text', 0)
		trv_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self._trv_networks.append_column(trv_column)
		
		model_networks = gtk.TreeStore(str)
		self._treeChannels.set_model(model_networks)
		
		self._context_status = windowResources.Context(
		 model_networks.append(None, 'Global', ['<span foreground="%s">Global</span>' % _COLOUR_CONTEXT_INACTIVE]),
		 'Status',
		 0 #Global context.
		)
		self._context_active = self._context_status
		
		self._trv_networks.set_search_column(0)
		
		self._btn_networks = widget_tree.get_widget("btn_networks")
		
		#========================================================================
		#The second, nested, splitter widget.
		self._pne_context = widget_tree.get_widget("pne_context")
		self._pne_context.set_position(self._pne_context.get_allocation().width - nicknames_size)
		
		self._btn_channel = widget_tree.get_widget("btn_channel")
		self._btn_topic = widget_tree.get_widget("btn_topic")
		self._btn_modes = widget_tree.get_widget("btn_modes")
		
		#========================================================================
		#The main chat interface.
		self._txt_chat = widget_tree.get_widget("txt_chat")
		
		self._txt_chat.set_buffer(self._context_global.getBuffer())
		
		self._btn_nickname = widget_tree.get_widget("btn_nickname")
		self._txt_input = widget_tree.get_widget("txt_input")
		self._btn_send = widget_tree.get_widget("btn_send")
		
		#========================================================================
		#The userlist and latency column.
		self._lst_users = widget_tree.get_widget("lst_users")
		self._lst_users.set_property("width-request", 100)
		
		pixbuf_renderer = gtk.CellRendererPixbuf()
		cell_renderer = gtk.CellRendererText()
		trv_column = gtk.TreeViewColumn()
		trv_column.pack_start(pixbuf_renderer, expand=False)
		trv_column.add_attribute(pixbuf_renderer, 'pixbuf', 0)
		trv_column.pack_start(cell_renderer, expand=True)
		trv_column.add_attribute(cell_renderer, 'text', 1)
		trv_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self._lst_users.append_column(trv_column)
		
		model_users = gtk.ListStore(gtk.gdk.Pixbuf, str)
		self._lst_users.set_model(model_users)
		
		model_users.append([windowResources.PIXBUFS['~'], 'flan'])
		model_users.append([windowResources.PIXBUFS['+'], 'flan2'])
		model_users.append([None, 'flan3'])
		
		lst_users.set_search_column(0)
		
		self._lbl_users = widget_tree.get_widget("lbl_users")
		self._lbl_users.set_text("o+1/h0/v0/0 : 1")
		
		self._lbl_ping = widget_tree.get_widget("lbl_ping")
		self._prg_ping_timeout = widget_tree.get_widget("prg_ping_timeout")
		
#Userlist popup:
#All known details
#...
#-
#Whois
#-
#Kick (clickable, same as first sub) -> Kick, Kick...
#(Options below are visible only if required information has been gathered)
#Ban (clickable, same as first sub) -> Every banmask combination
#Kickban -> Every banmask combination
#Kickban... -> Every bannable combination

#Every menu should be expandable.


#Modify UI to support i8n

#Update mode buttons when the channel context changes.
#Rebuild buttons so they always represent all modes supported by the server in any given context.
