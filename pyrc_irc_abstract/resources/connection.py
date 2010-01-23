# -*- coding: utf-8 -*-
"""
PyRC module: pyrc_irc_abstract.resources.connection

Purpose
=======
 Provide resources for communicating with remote servers.
 
Legal
=====
 All code, unless otherwise indicated, is original, and subject to the terms of
 the GPLv2, which is provided in COPYING.
 
 (C) Neil Tallim, 2004-2007
"""
import socket
import select
import threading
import time

class _Socket(object):
	"""
	This abstract class defines operations that a socket can perform in relation
	to an IRC server.
	
	Specifically, it defines connect, read, write, and close operations.
	"""
	_alive_lock = None #: A lock used to prevent multiple simultaneous accesses to the _is_alive variable.
	_is_alive = False #: True if the connection to the server is active.
	_address = None #: A tuple containing the URL and port to which this socket is connected.
	
	def __init__(self):
		"""
		This function would be invoked if it were possible to instantiate an
		_Socket object, but it is abstract, so it can't be done.
		
		Instantiate one of its inheriting classes instead.
		
		@return: Nothing.
		
		@raise InstantiationError: If instantiation is attempted.
		"""
		raise InstantiationError(u"_Socket is an abstract class, so it cannot be instantiated.")
		
	def close(self):
		"""
		This function closes the socket.
		
		@return: Nothing.
		"""
		self._setAlive(False)
		self._close()
		
	def _close(self):
		"""
		This function provides a logical implementation for close(). It must be
		overridden to properly subclass _Socket.
		
		@return: Nothing.
		"""
		pass
		
	def connect(self, host, port):
		"""
		This function establishes a connection to an IRC server.
		
		@type host: basestring
		@param host: The addess of the IRC server to which a connection will be
		    established. This may be a DNS address, an IP address, or a hostname.
		@type port: int
		@param port: The port on the IRC server to which a connection will be
		    established.
		
		@return: Nothing.
		
		@raise ConnectionError: If a connection could not be established.
		"""
		self._connect(host, port)
		self._setAlive(True)
		
	def _connect(self, host, port):
		"""
		This function provides a logical implementation for connect(). It must be
		overridden to properly subclass _Socket.
		
		@type host: basestring
		@param host: The addess of the IRC server to which a connection will be
		    established. This may be a DNS address, an IP address, or a hostname.
		@type port: int
		@param port: The port on the IRC server to which a connection will be
		    established.
		
		@return: Nothing.
		
		@raise ConnectionError: If a connection could not be established.
		"""
		pass
		
	def getAddress(self):
		"""
		This function returns the URL and port of the server to which this
		socket is connected, if it is connected.
		
		@rtype: tuple|None
		@return: A tuple containing the URL and port to which this socket is
		    connected, or None if no connection has been attemped.
		"""
		return self._address
		
	def isAlive(self):
		"""
		This function tests whether the _Socket is alive or dead.
		
		@rtype: bool
		@return: The _Socket's liveliness.
		"""
		self._alive_lock.acquire()
		
		alive = self._is_alive
		
		self._alive_lock.release()
		return alive
		
	def readData(self, packet_size):
		"""
		This function reads data from the IRC server.
		
		@type packet_size: int
		@param packet_size: The number of bytes to read.
		
		@rtype: basestring|None
		@return: The data received from the IRC server, or None if no data was
		    available.
		
		@raise InvalidStateError: If the socket is dead.
		@raise IncomingTransmissionError: If a problem occurred when reading data
		    from the connection.
		@raise SocketPollError: If a problem occurred when resolving select().
		"""
		if self.isAlive():
			return self._readData(packet_size)
		else:
			raise InvalidStateError(u"This _Socket is not connected to a server; it cannot read data.")
			
	def _readData(self, packet_size):
		"""
		This function provides a logical implementation for readData(). It must
		be overridden to properly subclass _Socket.
		
		@type packet_size: int
		@param packet_size: The number of bytes to read.
		
		@rtype: basestring|None
		@return: The data received from the IRC server, or None if no data was
		    available.
		
		@raise IncomingTransmissionError: If a problem occurred when reading data
		    from the connection.
		@raise SocketPollError: If a problem occurred when resolving select().
		"""
		pass
		
	def sendData(self, data):
		"""
		This function sends data to the IRC server.
		
		@type data: basestring
		@param data: The string to be sent to the IRC server.
		
		@return: Nothing.
		
		@raise InvalidStateError: If the socket is dead.
		@raise OutgoingTransmissionError: If a problem occurred when writing data
		    to the connection.		
		"""
		if self.isAlive():
			self._sendData(data)
		else:
			raise InvalidStateError(u"This _Socket is not connected to a server; it cannot send data.")
			
	def _sendData(self, data):
		"""
		This function provides a logical implementation for sendData(). It must
		be overridden to properly subclass _Socket.
		
		@type data: basestring
		@param data: The string to be sent to the IRC server.
		
		@return: Nothing.
		
		@raise OutgoingTransmissionError: If a problem occurred when writing data
		    to the connection.		
		"""
		pass
		
	def _setAlive(self, alive):
		"""
		This function marks the _Socket as alive or dead.
		
		@type alive: bool
		@param alive: The _Socket's state.
		
		@return: Nothing.
		"""
		self._alive_lock.acquire()
		
		self._is_alive = alive
		
		self._alive_lock.release()
		
class BasicSocket(_Socket):
	"""
	This class provides an implementation of _Socket for non-secure connections.
	"""
	_socket = None #: The socket object along which all server communication occurs.
	
	def __init__(self):
		"""
		This function is invoked when creating a new BasicSocket object.
		
		@return: Nothing.
		"""
		self._alive_lock = threading.Lock()
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
	def _close(self):
		"""
		This function provides the functionality of _Socket.close().
		
		@return: Nothing.
		"""
		try:
			self._socket.close()
		except socket.error:
			pass
			
	def _connect(self, host, port):
		"""
		This function provides the functionality of _Socket.connect().
		
		@type host: basestring
		@param host: The addess of the IRC server to which a connection will be
		    established.
		@type port: int
		@param port: The port on the IRC server to which a connection will be
		    established.
		
		@return: Nothing.
		
		@raise ConnectionError: If a connection could not be established.
		"""
		try:
			self._address = (host, port)
			self._socket.connect(self._address)
		except socket.error, error_data:
			raise ConnectionError(u"Failed to connect to socket: %s" % error_data)
			
	def _readData(self, packet_size):
		"""
		This function provides the functionality of _Socket.readData().
		
		@type packet_size: int
		@param packet_size: The number of bytes to read.
		
		@rtype: basestring|None
		@return: The data received from the IRC server, or None if no data was
		    available.
		
		@raise IncomingTransmissionError: If a problem occurred when reading data
		    from the connection.
		@raise SocketPollError: If a problem occurred when resolving select().
		"""
		try:
			(input_events, output_events, error_events) = select.select([self._socket], [], [], 0.1)
			if self._socket in input_events:
				return self._readData_(packet_size)
			else:
				return None
		except select.error:
			raise SocketPollError(u"Failed to read state of socket.")
			
	def _readData_(self, packet_size):
		"""
		This function provides the functionality of _readData().
		
		@type packet_size: int
		@param packet_size: The number of bytes to read.
		
		@rtype: basestring
		@return: The data received from the IRC server.
		
		@raise IncomingTransmissionError: If a problem occurred when reading data
		    from the connection.
		"""
		try:
			return self._socket.recv(packet_size)
		except socket.error:
			raise IncomingTransmissionError("Failed to read data from server.")
			
	def _sendData(self, data):
		"""
		This function provides the functionality of _Socket.sendData().
		
		@type data: basestring
		@param data: The string to be sent to the IRC server.
		
		@return: Nothing.
		
		@raise OutgoingTransmissionError: If a problem occurred when writing data
		    to the connection.
		"""
		try:
			self._socket.sendall(data)
		except socket.error:
			raise OutgoingTransmissionError(u"Failed to send data to server.", data)
			
class SSLSocket(BasicSocket):
	"""
	This class provides a version of BasicSocket enhanced to provide SSL
	encryption.
	"""
	_ssl_socket = None #: The SSL wrapper placed around the raw socket object.
	
	def __init__(self):
		"""
		This function is invoked when creating a new SSLSocket object.
		
		@return: Nothing.
		"""
		BasicSocket.__init__(self)
		
	def _connect(self, host, port):
		"""
		This function overrides the functionality of BasicSocket._connect().
		
		@type host: basestring
		@param host: The addess of the IRC server to which a connection will be
		    established.
		@type port: int
		@param port: The port on the IRC server to which a connection will be
		    established.
		
		@return: Nothing.
		
		@raise ConnectionError: If a connection could not be established.
		"""
		BasicSocket._connect(self, host, port)
		self._ssl_socket = socket.ssl(self._socket)
		
	def _readData_(self, packet_size):
		"""
		This function overrides the functionality of BasicSocket._readData_().
		
		@type packet_size: int
		@param packet_size: The number of bytes to read.
		
		@rtype: basestring
		@return: The data received from the IRC server.
		
		@raise IncomingTransmissionError: If a problem occurred when reading data
		    from the connection.
		"""
		try:
			return self._ssl_socket.read(packet_size)
		except socket.error:
			raise IncomingTransmissionError(u"Failed to read SSL data from server.")
		
	def _sendData(self, data):
		"""
		This function overrides the functionality of BasicSocket._sendData().
		
		@type data: basestring
		@param data: The string to be sent to the IRC server.
		
		@return: Nothing.
		
		@raise OutgoingTransmissionError: If a problem occurred when writing data
		    to the connection.
		"""
		try:
			self._ssl_socket.write(data)
		except socket.error:
			raise OutgoingTransmissionError(u"Failed to send SSL data to server.", data)
			
			
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
		
class InstantiationError(Error):
	"""
	This class represents problems that might occur during class instantiation.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new InstantiationError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		self.description = unicode(description)
		
class InvalidStateError(Error):
	"""
	This class represents problems associated with calling functions on
	uninitialized objects.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new InvalidStateError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		self.description = unicode(description)
		
class ServerError(Error):
	"""
	This class serves as the base from which all exceptions associated with a
	server connection are derived.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new Error object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		Error.__init__(self, description)
		
class ConnectionError(ServerError):
	"""
	This class represents problems that might occur when attempting to connect
	to a server.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new ConnectionError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		ServerError.__init__(self, description)
		
class IncomingTransmissionError(ServerError):
	"""
	This class represents problems that might occur when receiving data from a
	server.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new IncomingTransmissionError
		object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		ServerError.__init__(self, description)
		
class OutgoingTransmissionError(ServerError):
	"""
	This class represents problems that might occur when sending data to a
	server.
	"""
	message = None #: A string containing the message that was to be sent.
	
	def __init__(self, description, message):
		"""
		This function is invoked when creating a new OutgoingTransmissionError
		object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		@type message: basestring
		@param message: The message that was supposed to be sent when this object
		    was generated.
		
		@return: Nothing.
		"""
		ServerError.__init__(self, description)
		self.message = unicode(message)
		
class SocketPollError(ServerError):
	"""
	This class represents problems that might occur when reading the state of a
	socket.
	"""
	def __init__(self, description):
		"""
		This function is invoked when creating a new SocketPollError object.
		
		@type description: basestring
		@param description: A description of the problem that this object
		    represents.
		
		@return: Nothing.
		"""
		ServerError.__init__(self, description)
		