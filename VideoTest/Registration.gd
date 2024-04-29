extends MarginContainer
const SERVER_IP = 'highlyderivative.games'
const SERVER_PORT = 4800

var peer:ENetPacketPeer
var enetConnection := ENetConnection.new()
var do_register := false
var do_login := false
var token:Dictionary


func send_register():
	var s = "REGISTER %s %s" % [get_username(), get_password()]
	peer.send(0, s.to_utf8_buffer(), ENetPacketPeer.FLAG_RELIABLE)
	print("sending registration")


func send_login():
	var s = "LOGIN %s %s" % [get_username(), get_password()]
	peer.send(0, s.to_utf8_buffer(), ENetPacketPeer.FLAG_RELIABLE)
	print("sending login")


func get_username():
	return $List/Username/Value.text


func get_password():
	return $List/Password/Value.text


func _ready():
	enetConnection.create_host_bound("0.0.0.0", 0)


func register_success_popup(token):
	var modal := AcceptDialog.new()
	modal.title = "Registration Success"
	modal.set_text("Registered successfully, token hash is\n" + str(token['hash']))
	modal.popup_exclusive_centered(get_tree().root)


func register_fail_popup(error):
	var modal := AcceptDialog.new()
	modal.title = "Registration Error"
	modal.set_text("Account name is probably already taken")
	modal.popup_exclusive_centered(get_tree().root)


func login_success_popup(token):
	var modal := AcceptDialog.new()
	modal.title = "Login Success"
	modal.set_text("Login successful, token hash is\n" + str(token['hash']))
	modal.popup_exclusive_centered(get_tree().root)


func login_fail_popup(error):
	var modal := AcceptDialog.new()
	modal.title = "Login Error"
	modal.set_text("Username or password incorrect")
	modal.popup_exclusive_centered(get_tree().root)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if not visible:
		return

	# type_peer_data_channel
	var tpdc := enetConnection.service(5)
	if tpdc[0] == enetConnection.EVENT_CONNECT:
		peer = tpdc[1]
		if do_login:
			do_login = false
			send_login()
			
		if do_register:
			do_register = false
			send_register()
			
	elif tpdc[0] == enetConnection.EVENT_RECEIVE:
		var bytes = tpdc[1].get_packet()
		var message:Dictionary = JSON.parse_string(bytes.get_string_from_utf8())
		
		match [message['type'], message['error_type']]:
			['LOGIN', 'OK']:
				token = message['message']
				login_success_popup(token)
			['LOGIN', var error]:
				login_fail_popup(error)
			['REGISTER', 'OK']:
				token = message['message']
				register_success_popup(token)
			['REGISTER', var error]:
				register_fail_popup(error)
			_:
				print("this shouldn't happen")


func _on_test_register_pressed():
	if peer:
		send_register()
	else:
		enetConnection.connect_to_host(SERVER_IP, SERVER_PORT)
		do_register = true


func _on_test_login_pressed():
	print("testing login...")
	if peer:
		send_login()
	else:
		enetConnection.connect_to_host(SERVER_IP, SERVER_PORT)
		do_login = true
