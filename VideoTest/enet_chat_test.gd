extends Node
const Chatroom = preload("res://chatroom.tscn")
#const RudpConnection = preload("res://rudp_connection.gd")

const LOCAL_TEST = true


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
				var addr = await sock.holepunch(clientAddr, clientLocal, int(clientPort), int(clientLocalPort))
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
				var addr = await sock.holepunch(hostAddr, hostLocal, int(hostPort), int(hostLocalPort))
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
