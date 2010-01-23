# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.asynch

Purpose
=======
 Provide generic facilities to execute functions asynchronously.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import threading

class Asyncher(threading.Thread):
	"""
	This class can be used to run functions asynchronously.
	
	Any arguments passed to it will be received as a tuple.
	If no arguments are passed, it will be called with nothing.
	"""
	def __init__(self, function, *optArgs):
		"""
		This function is invoked when a new Asyncher object is created.
		
		It caches the function and any given arguments.
		
		@type function: function
		@param function: The function to be called when this thread starts.
		@type optargs: *variable
		@param optargs: Any number of arguments that may be passed to the
		    function.
		"""
		threading.Thread.__init__(self)
		self.func = function
		self.args = optArgs
		
	def run(self):
		"""
		This function is called when the thread is started. It invokes the set
		function with any given arguments.
		
		@return: Nothing.
		"""
		if self.args:
			self.func(self.args)
		else:
			self.func()
			
			
class AsyncherSingleArg(threading.Thread):
	"""
	This class can be used to run functions asynchronously, like the one above,
	but since it only accepts one argument, it's more useful in producing clean,
	consistent code.
	"""
	def __init__(self, function, arg):
		"""
		This function is invoked when a new AsyncherSingleArg object is created.
		
		It caches the function and given argument.
		
		@type function: function
		@param function: The function to be called when this thread starts.
		@type args: variable
		@param optargs: An argument to be passed to the set function.
		"""
		threading.Thread.__init__(self)
		self.func = function
		self.arg = arg
		
	def run(self):
		"""
		This function is called when the thread is started. It invokes the set
		function with the given argument.
		
		@return: Nothing.
		"""
		self.func(self.arg)
		