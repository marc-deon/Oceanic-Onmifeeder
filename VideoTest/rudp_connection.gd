extends Node
###############################################################################
#  Reliable UDP  #
##################
#
# This module offers two classes:
# 1. RudpMessage, which is fairly self explanitory
# 2. RudpConnection, which is a little more out-there.
#
# This module was written to solve two needs:
# 1. Establishment of a reliable (i.e. has acknowledgements) connection over
#    a regular UDP port, with some support for holepunching techniques.
# 2. Division of that connection into virtual ports, so
#    that the holepunching only ever has to be done once.
#
# The main way that this should be used is:
#
#   localPort = 1
#   remotePort = 1
#   
#   conn = RudpConnection(...)
#   conn.Connect(...)
#   port = conn.Virtual(localPort, remotePort)
#   
#   try:
#       port.Send("Some message")
#   except RudpTimeout:
#       print("We got no acknowledgement.")
#
#   try:
#       rudp_message = port.Receive()
#       print("message contains", rudp_message.string)
#   except RudpTimeout:
#       print("We got no response.")
#
# I very much hope that this is the final API.
#
###############################################################################

const RudpMessage = preload("res://rudp_message.gd")
const RudpPort = preload("res://rudp_port.gd")

var socket:PacketPeerUDPTimeout
var peer:Array
var ports:Dictionary

const MAX_ATTEMPTS = 5

func CreateSocket(port:int=0) -> PacketPeerUDPTimeout:
	var s = PacketPeerUDPTimeout.new()
	if port:
		s.bind(s)
	return s

func init(port:int=0, _socket=null) -> void:
	if _socket:
		self.socket = _socket
	else:
		self.socket = CreateSocket(port)
	peer = [null, null] # IP-Port pair
	var initialPort := RudpPort.new()
	initialPort.init(0, 0, self)
	ports  = { 0: initialPort }


func _sendto(data, dest):
	"""Passthrough to socket's sendto()."""
	socket.set_dest_address(dest[0], dest[1])
	socket.put_packet(data)


func Send(port:RudpPort, msg:String, system:bool=false) -> void:
	"""Sends a given string to the connected RUDP socket."""
	
	var message = RudpMessage.new()
	message.srcPort  = port.port
	message.destPort = port.peerPort
	message.system   = system 
	message.id       = port.lastId
	message.data     = Marshalls.utf8_to_base64(msg).to_utf8_buffer()
	
	_sendto(message.Encode(), peer)
	_WaitForAck(port.lastId, port)
	port.lastId += 1


func _recvfrom(): #-> tuple[bytes, str, int]:
	"""Passthrough to socket's recvfrom(), but ip and addr are separated."""
	if not await socket.wait_timeout():
		return false
	var msg = socket.get_packet()
	var ip = socket.get_packet_ip()
	var port = socket.get_packet_port()
	return [msg, ip, port]


func _SendAck(incoming:RudpMessage) -> void:
	"""Send an acknowledgement message in response to given incoming."""
	var m = RudpMessage.new()
	m.init(incoming.destPort, incoming.srcPort, true, incoming.id, "ACK")
	var ack = m.Encode()
	_sendto(ack, peer)


# TODO: This being completely from Receive() bugs me. There's a good bit of
# Code shared. Merge? Factor out common?
func _WaitForAck(expectedId:int, virtualPort:RudpPort) -> void:
	"""Wait for acknowledgement, in the mean time queueing other received messages. Throw error upon timeout."""

	var attempts = 0
	while attempts < self.MAX_ATTEMPTS:
		if not await socket.wait_timeout():
			attempts += 1
			continue
		var msg = socket.get_packet()
		var addr = [socket.get_packet_ip(), socket.get_packet_port()]
		if addr != self.peer:
			continue

		var incoming = RudpMessage.Decode(msg)
		
		match [incoming.destPort, incoming.system, incoming.id, incoming.string]:
			[virtualPort.port, true, expectedId, "ACK"]:
				# This is what we were waiting for; leave.
				return

			[0, true, _, "HAND1"]:
				self._SendAck(incoming)

			[0, true, _, "HAND2"]:
				self._SendAck(incoming)
				
			[virtualPort.port, true, _, _]:
				# If this IS intended for us, and IS a system message,
				# but we don't have a specific answer, then panic
				# raise NotImplementedError(incoming.string)
				print("Panic")
				pass

			[var vport, false, _, _]:
				# If this is for anyone else and is NOT a system message,
				# add it to their queue and send an ACK
				self.ports[vport].queue.append(incoming)
				self._SendAck(incoming)

			[var _vport, true, _, _]:
				# if this is for anyone else and IS a system emssage,
				# add it to their queue and that's it
				self.ports[incoming.destPort].queue.append(incoming)

			_:
				# What?
				print("What?")
				pass



func _TryConnect(mainIp:String, tentativePort:int, altIp:String, altPort:int) -> bool:
	"""Handshake function to connect to connect to a main/alt IP."""
	var sock = self.socket

	# We must figure out whether to use the public or local IP for the peer
	var actual = ""
	# We can try to contact the peer over this tentative port, but we may have to switch
	var port = int(tentativePort)

	var attempts = 0
	while attempts < self.MAX_ATTEMPTS:
		# Try to contact peer on internet
		#          port, peerPort, system, id, msg
		var m = RudpMessage.new()
		m.init(0, 0, true, 0, "HAND1")
		var outgoing = m.Encode()
		
		sock.set_dest_address(mainIp, port)
		sock.put_packet(outgoing)

		if altIp:
			# Try to contact peer on local network
			sock.set_dest_address(altIp, port)
			sock.put_packet(outgoing)

		if altPort:
			sock.set_dest_address(mainIp, altPort)
			sock.put_packet(outgoing)
			if altIp:
				sock.set_dest_address(altIp, altPort)
				sock.put_packet(outgoing)

		# Listen for message from peer
		var r = await _recvfrom()
		var msg = r[0]
		var ip = r[1]
		var p = r[2]
		
		msg = Array(RudpMessage.Decode(msg).string.split(" "))
		
		match msg:
			# Peer has made contact with us
			["HAND1"]:
				if ip == mainIp:
					actual = mainIp

				elif ip == altIp:
					actual = altIp

				else:
					# This is a third-party trying to connect
					print("That's my purse!", ip)
					continue

				port = p
				m = RudpMessage.new()
				m.init(0, 0, true, 1, "HAND2")
				outgoing = m.Encode()
				sock.set_dest_address(actual, port)
				sock.put_packet(outgoing)

			# Peer heard our IAM and is responding!
			["HAND2"]:
				# Send one final YOUARE back to them
				port = p
				actual = ip
				m = RudpMessage.new()
				m.init(0,0, true, 1, "HAND2")
				outgoing = m.Encode()
				sock.set_dest_address(actual, port)
				sock.put_packet(outgoing)
				break

			_:
				print("Malformed message ", msg)
				pass
		attempts += 1

	if not actual:
		return false

	self.peer = [actual, port]
	return true


func Connect(ip:String, altIp:String, initialPort:int, altPort:int) -> bool:
	"""Connect to peer RUDP."""
	return await self._TryConnect(ip, initialPort, altIp, altPort)


func Virtual(port:int, peerPort:int) -> RudpPort:
	"""Create a virtual RUDP port on this connection and return it."""
	if port in self.ports:
		# raise KeyError("Duplicate port number")
		print("Not allowed")

	var p = RudpPort.new()
	p.init(port, peerPort, self)
	self.ports[port] = p
	return p
