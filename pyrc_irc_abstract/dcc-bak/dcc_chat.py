"""
 PyRC module: ircAbstract.dccChat
 Purpose: Handle DCC Chat connections.
 
 All code, unless otherwise indicated, is original, and subject to the terms of
 the attached licensing agreement.
 
 (C) Neil Tallim, 2004
 Version: 0.0.1

 This module falls under the terms of the license stipulated in PyRC.py, which
 you should have received with it.
"""

class Chat: #The connection will be handled at the next level up.
	def __init__(self, username, svr):
		#Run a check against username for all channels you're in; if detailed data is available, use it. If not, thread whois immediately.
		#Display a list of all common channels you share with the user to help identify the reason for the message.
		self.scrollLog = []
		self.userName = username
		
	def appendEvent(self, textToAdd, scrollCap, source = None):
		"""Add a new entry to the channel log."""
		if source == None:
			source = self.username
			
		if len(self.scrollLog) == scrollCap:
			del x[0]
			
		xTime = time.localtime()
		self.scrollLog.append([textToAdd, xTime])
		return xTime
		
	def getLog(self):
		return self.scrollLog
		
	def setLog(self, sLog):
		self.scrollLog = sLog
		
