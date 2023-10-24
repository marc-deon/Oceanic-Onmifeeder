extends Node
const Chatroom = preload("res://chatroom.tscn")
#const RudpConnection = preload("res://rudp_connection.gd")

const LOCAL_TEST = true

func utf8send(sock, msg, ip, port):
	sock.set_dest_address(ip, port)
	sock.put_packet(msg.to_utf8_buffer())


func utf8get(sock:PacketPeerUDPTimeout, split:bool):
	var msg = sock.get_packet().get_string_from_utf8()
	var addr = sock.get_packet_ip()
	var port = sock.get_packet_port()
	if split:
		msg = msg.split(" ")
	return [msg, addr, int(port)]


#																							[str, int]
func holepunch(sock:PacketPeerUDPTimeout, mainIp:String, altIp:String, tentativePort:int, altPort:int) -> Array:
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
			utf8send(sock, "HAND1", mainIp, port)

			if altIp:
				# Try to contact peer on local network
				utf8send(sock, "HAND1", altIp, port)

			if altPort:
				utf8send(sock, "HAND1", mainIp, altPort)
				
				if altIp:
					utf8send(sock, "HAND1", altIp, altPort)

				# Listen for message from peer
				await sock.wait_timeout()
				var response = utf8get(sock, true)
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
						utf8send(sock, "HAND2 " + actual + " " + str(port), actual, port)

					# Peer heard our IAM and is responding!
					["HAND2", var oa, var op]:
						# Send one final YOUARE back to them
						port = p
						actual = ip
						ourActual = oa
						ourPort = int(op)
						utf8send(sock, "HAND2 " + actual + " " + str(port), actual, port)
						break

					_:
						print("Malformed message")

		print("Handshook ", actual, " ", port, ".")
		return [actual, port, ourActual, ourPort]


func _on_host_button_pressed():
	var sock := PacketPeerUDPTimeout.new()
	sock.set_dest_address("highlyderivative.games", 4800)
	sock.put_packet("FRSH".to_utf8_buffer())
	var local := IP.get_local_addresses()[0]
	var ourport := sock.get_local_port()
	
	# Send message to holepunch server
	var s := "HOST {local} {user} {ourport}".format({"local":local, "user":"JUNNA", "ourport":ourport})
	sock.put_packet(s.to_utf8_buffer())
	
	# Listen for response
	while true:
		if not await sock.wait_timeout():
			continue
		
		var msg = Array(sock.get_packet().get_string_from_utf8().split(" "))
		match msg:
			# Request for spot succeeded
			["HOSTING"]:
				print("Hosting at...", local)

			# Server says that a peer is trying to contact us
			["EXPECT", var clientAddr, var clientLocal, var clientPort, var clientLocalPort]:
				# Find our peer
				print("host hp ", clientAddr, " ", clientLocal, " ", int(clientPort), " ", int(clientLocalPort))
				var addr = await holepunch(sock, clientAddr, clientLocal, int(clientPort), int(clientLocalPort))
				local = addr[2]
				ourport = addr[3]
				# We don't need this anymore
				sock.close()
				
				# ENet stuff
				var conn = ENetConnection.new()
				conn.create_host_bound(local, ourport)
				var peer = conn.connect_to_host(addr[0], addr[1])

				# Start demo chatroom
				var cr = Chatroom.instantiate()
				cr.init(conn, peer, 0, "星見純那")
				
				get_tree().root.add_child(cr)
				get_tree().root.remove_child(self)
				break
				
			# Refreshed connection to server
			["OK"]:
				print("OK")
				pass

			_:
				print("Invalid response ", msg)


func _on_connect_button_pressed():
	var sock := PacketPeerUDPTimeout.new()
	sock.set_dest_address("highlyderivative.games", 4800)
	sock.put_packet("FRSH".to_utf8_buffer())
	var local := IP.get_local_addresses()[0]
	var ourport := sock.get_local_port()
	
	# Send message to holepunch server
	var s := "CONN {local} {user} {ourport}".format({"local":local, "user":"JUNNA", "ourport":ourport})
	sock.put_packet(s.to_utf8_buffer())
	
	# Wait for response
	while true:
		if not await sock.wait_timeout():
			continue
		var msg := Array(sock.get_packet().get_string_from_utf8().split(" "))
		match msg:
			# Received message with our peer's info
			["CONNTO", var hostAddr, var hostLocal, var hostPort, var hostLocalPort]:
				# Find our peer
				
				print("client hp ", hostAddr, " ", hostLocal, " ", int(hostPort), " ", int(hostLocalPort))
				var addr = await holepunch(sock, hostAddr, hostLocal, int(hostPort), int(hostLocalPort))
				local = addr[2]
				ourport = addr[3]
				# We don't need this anymore
				sock.close()

				# ENet stuff
				var conn = ENetConnection.new()
				conn.create_host_bound(local, ourport)
				var ip = addr[0]
				var port = addr[1]
				print(ip, " ", port)
				var peer = conn.connect_to_host(ip, port)

				# Start demo chatroom
				var cr = Chatroom.instantiate()
				cr.init(conn, peer, 0, "大場なな")
				
				get_tree().root.add_child(cr)
				get_tree().root.remove_child(self)
				break

			_:
				print("Invalid response", msg)
