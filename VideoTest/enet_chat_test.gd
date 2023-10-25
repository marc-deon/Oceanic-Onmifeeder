extends Node
const Chatroom = preload("res://chatroom.tscn")

func _on_host_button_pressed():
	#Find Peer 
	var sock := PacketPeerUDPTimeout.new()
	var addr = await sock.register_wait_for_holepunch("JUNNA")
	sock.close()
	
	# ENet stuff
	var conn = ENetConnection.new()
	conn.create_host_bound(addr[2], addr[3])
	var peer = conn.connect_to_host(addr[0], addr[1])

	# Start demo chatroom
	var cr = Chatroom.instantiate()
	cr.init(conn, peer, 0, "星見純那")
	
	get_tree().root.add_child(cr)
	get_tree().root.remove_child(self)


func _on_connect_button_pressed():
	# Find peer
	var sock := PacketPeerUDPTimeout.new()
	var addr = await sock.connect_to_holepunch("JUNNA")
	sock.close()
	
	# ENet stuff
	var conn = ENetConnection.new()
	conn.create_host_bound(addr[2], addr[3])
	var peer = conn.connect_to_host(addr[0], addr[1])

	# Start demo chatroom
	var cr = Chatroom.instantiate()
	cr.init(conn, peer, 0, "大場なな")
	
	get_tree().root.add_child(cr)
	get_tree().root.remove_child(self)
