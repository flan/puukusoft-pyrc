# -*- coding: utf-8 -*-
"""
8-Squall: A script to answer all of life's many yes-or-no questions.

This script was inspired by the "Magic Eight Squall" that appeared in Mark
Shallow's Adventurers!, strip 155. http://www.adventurers-comic.com/d/0155.html

Purpose
=======
 To decide the fate of those who dare ask.
 
 Also, this provides a practical, non-intelligence-insulting example of how to
 write plugins for PyRC.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2006-2007
"""
__module_data__={
 'name': "Magic 8-Squall",
 'version': "1.0.0",
 #Optional
 'author': "Neil Tallim",
 'e-mail': "red.hamsterx@gmail.com"
} #: This dictionary contains information used to identify this plugin within PyRC.

_data_path = None #: This string will be set when the plugin is loaded; it should be used to store all data and configuration settings.

import random
import re

import pyrc_shared.convenience as pyrc

_RESPONSE_REGEXP = re.compile("^.?8-squall(.?) .+[?+/].*", re.I) #: This compiled regular expression object is used to quickly filter strings that this script should process.

_RESPONSES_8SQUALL = (
 "Meh.",
 "Whatever.",
 "Go away.",
 "...",
 "You're on your own.",
 "Leave me alone.",
 "Just give up.",
 "My sources say '...'",
 "All signs point to 'whatever'.",
 "Life sucks.",
 "Nobody loves me.",
 "Nobody loves you.",
 "Cutting is the answer.",
) #: This tuple contains a list of responses to pick from when in 8-Squall mode.

_RESPONSES_8BALL = (
 "Don't count on it.",
 "Most certainly.",
 "Probably.",
 "My sources say no.",
 "No.",
 "The outlook is promising.",
 "The outlook is bleak.",
 "All signs point to yes.",
 "As I see it, yes.",
 "Based on all I know, no.",
 "You're better off not knowing.",
) #: This tuple contains a list of responses to pick from when in 8-Ball mode.

_ALLOWED_SOURCES = {
 'synIRC': (
  '#o.o',
  '#utc!',
 )
}
"""
This dictionary is used to specify the sources that this script will accept
events from.

It is a two-tier (network)->(channel|user) structure.
"""

def loadMe(ial, load_mode):
	"""
	This function is called when the script is loaded.
	
	In its current form, 8-Squall uses hardcoded response lists, so all it needs
	to do here is identify which events it needs to watch. PyRC will take care
	of all internal hook-ups and filtering.
	
	Note: If 8-Squall were to load data, it would use the path specified in the
	variable _data_path, which points to a location in ~/.PyRC for this script's
	exclusive use. This variable is created by PyRC when this script is loaded.
	
	@type ial: function
	@param ial: A reference to the IRC Abstraction Layer's interface.
	@type unload_mode: int
	@param unload_mode: A value used to indicate the conditions under which this
	    plugin is being unloaded.
	    
	    Possible values follow::
	        0:
	            The plugin is being loaded for the first time in this instance
	            of PyRC.
	        1:
	            The plugin is being enabled after being set offline.
	        -1:
	            The plugin is being reloaded. This should only happen when
		        plugins are being actively developed, and it must be noted that
		        there is no guarantee that the reload will succeed.
	
	@rtype: tuple
	@return: A tuple containing tuples identifying the 'eventname' value of
	    each Event Dictionary type this script would like to receive, coupled
		with a reference to the function that will be used for processing, and a
		boolean value indicating whether input should be taken from the user
		(True) or the network/internal events (False).
	"""
	return (
	 ("Channel Message", processChannelMessage, False),
	 ("Channel Message Local", processChannelMessage, False)
	)
	
def unloadMe(ial, unload_mode):
	"""
	This function is called when the script is disabled.
	
	8-Squall is a very simple script, so it has no clean-up tasks to perform,
	but if it did, they would go here.
	
	Note: If 8-Squall were to save data, it would use the path specified in the
	variable _data_path, which points to a location in ~/.PyRC for this script's
	exclusive use. This variable is created by PyRC when this script is loaded.
	
	@type ial: function
	@param ial: A reference to the IRC Abstraction Layer's interface.
	@type unload_mode: int
	@param unload_mode: A value used to indicate the conditions under which this
	    plugin is being unloaded.
	    
	    Possible values follow::
	        1:
	            The plugin is being disabled either because it is being taken
	            offline or because PyRC is shutting down.
	        -1:
	            The plugin is being reloaded. This should only happen when
		        plugins are being actively developed, and it must be noted that
		        there is no guarantee that the reload will succeed.
	
	@return: Nothing.
	"""
	pass
	
def processChannelMessage(dictionary, ial):
	"""
	This function was specified in loadMe() as the handler for "Channel Message"
	and "Channel Message Local" Event Dictionaries. As such, it will be called
	each time one of these Event Dictionaries is passed through PyRC's plugin
	chain.
	
	@type dictionary: dict
	@param dictionary: The Event Dictionary to be processed.
	@type ial: function
	@param ial: A reference to the IRC Abstraction Layer's interface.
	
	@rtype: dict|None
	@return: Nothing, at least in this case. A Raise Event Event Dictionary
	    could be returned if this function needed to alter the way in which
	    PyRC's plugin chain processed this event.
	"""
	handling_data = pyrc.handleChannelMessage(dictionary, _ALLOWED_SOURCES)
	#The function above returns None if the event isn't from an allowed source.
	#In Python, anything that can be considered a form of NoneType, such as an
	#empty string, empty container, 0, False, and None, can be matched with the
	#following 'if not' syntax.
	if not handling_data:
		return
		
	#This applies the regular expression specified above to the received string
	#to find out if it is a request for 8-Squall.
	match = _RESPONSE_REGEXP.match(dictionary['message'])
	if match:
		(user_name, local) = handling_data #This breaks the tuple into a string and a bool. Indexing would work, too, but this is more clear.
		
		message = None #This specifies a variable used to store the message
		               #string when it is generated. It is declared here because
					   #any variables declared in a sub-scope, like an 'if' or
					   #anything else that gets indented, save for 'try's, is
					   #valid only within that sub-scope, and this value is
					   #needed later.
		if match.group(1) != ':' and random.randint(0, 2) == 2:
			#8-Squall mode is used only one third of the time. The user may use
			#a colon, as in '8-Squall: x?' to force 8-Ball mode.
			message = user_name + ", 8-Squall speaks: " + random.choice(_RESPONSES_8SQUALL)
		else:
			message = user_name + ", 8-Squall's 8-Ball has concluded: " + random.choice(_RESPONSES_8BALL)
			
		#This causes PyRC to send the response to the IRC network. Easy.
		pyrc.respondToChannelMessage(message, dictionary)
		
