extends Node

const RudpMessage = preload("res://rudp_message.gd")

var port:int
var peerPort:int
var parent

var queue:Array[RudpMessage] = []
var lastId:int = 0

# (Virtual) RUDP port
var socket:
	get:
		return self.parent.socket


func init(_port:int, _peerPort:int, _parent) -> void:
	self.port = _port
	self.peerPort = _peerPort
	self.parent = _parent


func Send(msg:String, system:bool=false):
	"""Send a message optionally marked as a system message."""
	# TODO: We should maybe have a private _SendSystem instead for this.
	self.parent.Send(self, msg, system)


func Receive():
	"""Wait for message, return it and send an ACK. Also queue message for other ports in the mean time."""

	var incoming = null
	# Check queue
	if len(self.queue) > 0:
		incoming = self.queue.pop_front()

	else:
		while true:
				if not await self.socket.wait_timeout():
					continue
					
				var msg = self.socket.get_packet()
				var ip = self.socket.get_packet_ip()
				var addr = self.socket.get_packet_port()
				if ip != self.parent.peer[0] or addr != self.parent.peer[1]:
					# This is a stranger, ignore them
					continue

				
				incoming = RudpMessage.Decode(msg)

				if (not incoming.system) or (incoming.string != "ACK"):
					# The only time we're not going to send ACK is when the message we receive
					# it IS a system message AND the message itself is ACK
					self.parent._SendAck(incoming)

				if incoming.destPort != self.port:
					# Add to other port's queue
					self.parent.ports[incoming.destPort].queue.append(incoming)

				if not incoming.system:
					break

	return incoming
