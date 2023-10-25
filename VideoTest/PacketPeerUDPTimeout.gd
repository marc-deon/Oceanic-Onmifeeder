class_name PacketPeerUDPTimeout
extends PacketPeerUDP

var _timeout_time:float = 0.2
signal timeout


func wait_timeout() -> bool:
	await Engine.get_main_loop().create_timer(_timeout_time).timeout
	
	if get_available_packet_count() > 0:
		return true
	else:
		timeout.emit()
		return false
	
func set_timeout(_timeout:float):
	_timeout_time = _timeout

func utf8send(msg, ip, port):
	self.set_dest_address(ip, port)
	self.put_packet(msg.to_utf8_buffer())


func utf8get(split:bool):
	var msg = self.get_packet().get_string_from_utf8()
	var addr = self.get_packet_ip()
	var port = self.get_packet_port()
	if split:
		msg = msg.split(" ")
	return [msg, addr, int(port)]


#																							[str, int, str, int]
func holepunch(mainIp:String, altIp:String, tentativePort:int, altPort:int) -> Array:
		"""Handshake function to connect to connect to a main/alt IP."""
		var sock = self
		
		# We must figure out whether to use the public or local IP for the peer
		var actual = ""
		var ourActual:String
		var ourPort:int
		# We can try to contact the peer over this tentative port, but we may have to switch
		var port = tentativePort

		var attempts = 0
		while attempts <= 5:
			attempts += 1
			# Tryblock
			
			# Try to contact peer on internet
			sock.utf8send("HAND1", mainIp, port)

			if altIp:
				# Try to contact peer on local network
				sock.utf8send("HAND1", altIp, port)

			if altPort:
				sock.utf8send("HAND1", mainIp, altPort)
				
				if altIp:
					sock.utf8send("HAND1", altIp, altPort)

				# Listen for message from peer
				await sock.wait_timeout()
				var response = sock.utf8get(true)
				var msg:Array = response[0];
				var ip:String = response[1];
				var p:int     = response[2]

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
						sock.utf8send("HAND2 " + actual + " " + str(port), actual, port)

					# Peer heard our IAM and is responding!
					["HAND2", var oa, var op]:
						# Send one final YOUARE back to them
						port = p
						actual = ip
						ourActual = oa
						ourPort = int(op)
						sock.utf8send("HAND2 " + actual + " " + str(port), actual, port)
						break

					_:
						print("Malformed message")

		print("Handshook ", actual, " ", port, ".")
		return [actual, port, ourActual, ourPort]
