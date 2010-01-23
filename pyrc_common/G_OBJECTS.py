# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_common.G_OBJECTS

Purpose
=======
 Store classes for objects that need to be persistent throughout PyRC's
 lifetime, but which don't really fit anywhere in the other modules.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2006-2007
"""
import threading
import time
import Queue

import GLOBAL

import dictionaries.outbound as outboundDictionaries
#Dictionaries used by this module:
##PyRC Timestamp Landmark

#Classes
#==============================================================================
class EventTimer(threading.Thread):
	"""
	This class provides PyRC's central event timer, which emits signals on every
	fifth minute of the day.
	"""
	def __init__(self):
		"""
		This function is invoked when the Event Timer object is instantiated.
		
		It stores the current time, reset to the start of the minute, and waits
		to be activated.
		
		@return: Nothing.
		"""
		threading.Thread.__init__(self)
		self.setDaemon(True)
		
		current_time = time.localtime()
		self.last_time = (
		 current_time[0],
		 current_time[1],
		 current_time[2], #Date
		 current_time[3], #Hour
		 current_time[4] - (current_time[4] % 5), #Minute
		 0 #:x[6] #Second
		)
		self.setName("Event Timer")
		
	def run(self):
		"""
		This function cycles every two seconds. If, on cycling, it discovers
		that a new five-minute block has started, and it has not yet generated a
		signal for this block, it will notify all plugins of the current time.
		
		The signals it may generate are as follows::
		    0: 5, 10, 20, 25, 35, 40, 50, 55 minutes
		    1: 15, 45 minutes
		    2: 30 minutes
		    3: 1 hour
		    4: 1 day
		
		Only one signal will be generated at any given interval.
		
		@return: Nothing.
		"""
		while True:
			start_time = time.time()
			
			current_time = time.localtime()
			minimum_difference = current_time[4] - self.last_time[4]
			if minimum_difference == 5 or minimum_difference == -55:
				scale = 0
				if minimum_difference == 5:
					if current_time[4] == 30:
						scale = 2
					elif current_time[4] % 15 == 0:
						scale = 1
				elif minimum_difference == -55:
					if current_time[2] == self.last_time[2]:
						scale = 3
					else:
						scale = 4
						
				GLOBAL.plugin.broadcastEvent(outboundDictionaries.PyRC_Time_Signal(time.time(), scale))
				
				self.last_time = current_time
			try:
				time.sleep(2 - (time.time() - start_time))
			except IOError:
				#It took more than two seconds to complete this cycle, but there's
				#really nothing that can be done, so just start the next one now.
				pass
				
				
class WorkerThread(threading.Thread):
	"""
	This class provides PyRC's worker threads, which are persistent handlers
	used to pass events around in the IAL.
	"""
	_queue = None #: A reference to the queue this thread is supposed to watch.
	_alive = True #: False when this thread is expected to stop processing events.
	
	def __init__(self, queue, name):
		"""
		This function is invoked when a WorkerThread object is instantiated.
		
		It accepts a reference to the queue it is supposed to watch and waits to
		be activated.
		
		@type queue: Queue.Queue
		@param queue: A Queue object that will be accessed every cycle to check
		    for new events.
		@type name: basestring
		@param name: The name of the resource that owns this WorkerThread.
		
		@return: Nothing.
		"""
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.setName(name + " - Worker Thread")
		
		self._queue = queue
		
	def kill(self):
		"""
		This function is used to signal the end of the thread's life; it should
		be called when PyRC is closing.
		
		@return: Nothing.
		"""
		self._alive = False
		
	def run(self):
		"""
		This function is called when the WorkerThread is ready to start. It will
		loop, accessing the queue and sending events to plugins until the
		thread is killed.
		
		@return: Nothing.
		"""
		while self._alive:
			try:
				GLOBAL.plugin.broadcastEvent(self._queue.get(True, 1))
			except Exception:
				pass
				
