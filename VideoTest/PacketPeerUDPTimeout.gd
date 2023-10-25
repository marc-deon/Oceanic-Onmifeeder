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
	
func set_timeout(_timeout:float) -> void:
	_timeout_time = _timeout

func utf8send(msg:String, ip:String="", port:int=0) -> void:
	if ip != "" and port != 0:
		set_dest_address(ip, port)
	put_packet(msg.to_utf8_buffer())


func utf8get(split:bool) -> Array: # [String, String, int]
	var msg = get_packet().get_string_from_utf8()
	var addr = get_packet_ip()
	var port = get_packet_port()
	if split:
		msg = msg.split(" ")
	return [msg, addr, int(port)]

func register_wait_for_holepunch(key:String) -> Array:
	utf8send("FRSH", "highlyderivative.games", 4800)
	var local := IP.get_local_addresses()[0]
	var ourport := get_local_port()
	
	# Send message to holepunch server
	var s := "HOST {local} {user} {ourport}".format({"local":local, "user":key, "ourport":ourport})
	utf8send(s)
	
	# Listen for response
	while true:
		if not await wait_timeout():
			continue
		
		var msg:Array = utf8get(true)[0]
		
		match msg:
			# Request for spot succeeded
			["HOSTING"]:
				print("Hosting at...", local)

			# Server says that a peer is trying to contact us
			["EXPECT", var clientAddr, var clientLocal, var clientPort, var clientLocalPort]:
				# Find our peer
				print("host hp ", clientAddr, " ", clientLocal, " ", int(clientPort), " ", int(clientLocalPort))
				var addr = await holepunch(clientAddr, clientLocal, int(clientPort), int(clientLocalPort))
				return addr
				
			# Refreshed connection to server
			["OK"]:
				print("OK")
				pass

			_:
				print("rwfh Invalid response ", msg)
	return []

func connect_to_holepunch(key:String) -> Array:
	utf8send("FRSH", "highlyderivative.games", 4800)
	var local := IP.get_local_addresses()[0]
	var ourport := get_local_port()
	
	# Send message to holepunch server
	var s := "CONN {local} {user} {ourport}".format({"local":local, "user":key, "ourport":ourport})
	utf8send(s)
	
	# Wait for response
	while true:
		if not await wait_timeout():
			continue
		
		var msg:Array = utf8get(true)[0]
		
		match msg:
			# Received message with our peer's info
			["CONNTO", var hostAddr, var hostLocal, var hostPort, var hostLocalPort]:
				# Find our peer
				var addr = await holepunch(hostAddr, hostLocal, int(hostPort), int(hostLocalPort))
				# We don't need this anymore
				close()
				return addr

			_:
				print("cth Invalid response ", msg)

	return []

func holepunch(mainIp:String, altIp:String, tentativePort:int, altPort:int) -> Array: # [str, int, str, int]
	"""Handshake function to connect to connect to a main/alt IP."""
	
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
		utf8send("HAND1", mainIp, port)

		if altIp:
			# Try to contact peer on local network
			utf8send("HAND1", altIp, port)

		if altPort:
			utf8send("HAND1", mainIp, altPort)
			
			if altIp:
				utf8send("HAND1", altIp, altPort)

			# Listen for message from peer
			await wait_timeout()
			var response = utf8get(true)
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
					utf8send("HAND2 " + actual + " " + str(port), actual, port)

				# Peer heard our IAM and is responding!
				["HAND2", var oa, var op]:
					# Send one final YOUARE back to them
					port = p
					actual = ip
					ourActual = oa
					ourPort = int(op)
					utf8send("HAND2 " + actual + " " + str(port), actual, port)
					break

				_:
					print("Malformed message")

	print("Handshook ", actual, " ", port, ".")
	return [actual, port, ourActual, ourPort]
