extends Node
const Chatroom = preload("res://chatroom.tscn")
const RudpConnection = preload("res://rudp_connection.gd")

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
			["EXPECT", var clientaddr, var clientlocal, var clientport, var clientlocalport]:

				# Start demo chatroom
				var conn = RudpConnection.new()
				conn.init(0, sock)

				var conn_result
				if LOCAL_TEST:
					conn_result = await conn.Connect('127.0.0.1', "", int(clientport), int(clientlocalport))
				else:
					conn_result = await conn.Connect(clientaddr, clientlocal, int(clientport), int(clientlocalport))
				var sendsock = conn.Virtual(1, 2)
				var recvsock = conn.Virtual(2, 1)

				var cr = Chatroom.instantiate()
				cr.init(sendsock, recvsock, "星見純那")
				
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
			["CONNTO", var hostaddr, var hostlocal, var hostport, var hostlocalport]:
				# Start demo chatroom
				var conn = RudpConnection.new()
				conn.init(0, sock)

				var conn_result
				if LOCAL_TEST:
					conn_result = await conn.Connect('127.0.0.1', "", int(hostport), int(hostlocalport))
				else:
					conn_result = await conn.Connect(hostaddr, hostlocal, int(hostport), int(hostlocalport))
				var sendsock = conn.Virtual(1, 2)
				var recvsock = conn.Virtual(2, 1)

				var cr = Chatroom.instantiate()
				cr.init(sendsock, recvsock, "大場なな")
				get_tree().root.add_child(cr)
				get_tree().root.remove_child(self)
				break

			_:
				print("Invalid response", msg)
