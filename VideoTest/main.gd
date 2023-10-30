extends Control

@onready var homePanel = $HBoxContainer/HomePanel
@onready var settingsPanel = $HBoxContainer/SettingsPanel

enum CHANNEL {
	NONE,
	HOLEPUNCH,
	CONTROL,
	STATS,
	VIDEO,
	MAX
}

enum ERROR {
	NONE,
	OK,
	MALFORMED_TIME,
	INVALID_TIME,
	INVALID_LENGTH,
	TEMP_MINMAX,
	PH_MINMAX,
	FEED_ERROR
}

enum MESSAGE {
	NONE,
	GET_SETTINGS, 
	GET_STATS, 
	MANUAL_FEED, 
	SET_FEED_TIME, 
	SET_FEED_LENGTH, 
	SET_TEMP_WARNING, 
	SET_PH_WARNING, 
	RESET_SETTINGS, 
	SAVE_SETTINGS
}

const hp_addr := "4800.highlyderivative.games"
const hp_port := 4800
var hp_key    := "poseidon"

var enetConnected:bool = false
var enetConnection:ENetConnection = ENetConnection.new()
var embeddedPeer:ENetPacketPeer

func ConnectToPeerEnet() -> Array:
	# Bind to all IPv4 addresses, any port; we're connecting, not listening
	enetConnection.create_host_bound("0.0.0.0", 0)
	
	# Connect to holepunch server
	var hpPeer:ENetPacketPeer
	hpPeer = enetConnection.connect_to_host(hp_addr, hp_port)
	
	# This is the request to connect that we will send later
	var s = " ".join(["CONN", IP.get_local_addresses()[0], hp_key, enetConnection.get_local_port()])
	var conn_packet = s.to_utf8_buffer()
	
	#var tentativePeer:ENetPacketPeer
	var tentativePeerAddr:String
	var tentativeLocalPeerAddr:String
	#var tentativeLocalPeer:ENetPacketPeer
	
	while true:
		var type_peer_data_channel:Array = enetConnection.service(500)
		var event_type:ENetConnection.EventType = type_peer_data_channel[0]
		var peer:ENetPacketPeer = type_peer_data_channel[1]
		
		if event_type == ENetConnection.EVENT_CONNECT:
			var peerAddr:String = peer.get_remote_address()
			
			# Connected to holepunch server successfully
			if peerAddr == hpPeer.get_remote_address():
				hpPeer = peer
				hpPeer.send(CHANNEL.HOLEPUNCH, conn_packet, hpPeer.FLAG_RELIABLE)
			
			# Found a valid connection to embedded over local network
			elif peerAddr == tentativeLocalPeerAddr:
				embeddedPeer = peer
				break
			
			# Found a valid connection to embedded over internet
			elif peerAddr == tentativePeerAddr:
				embeddedPeer = peer
				break
			
			
		elif event_type == ENetConnection.EVENT_RECEIVE:
			var response := Array(peer.get_packet().get_string_from_utf8().split(" "))
			match response:
				["CONNTO", var addr, var local, var port, var localport]:
					hpPeer.peer_disconnect()
					
					# Try to connect once over internet
					tentativePeerAddr = addr
					enetConnection.connect_to_host(addr, int(port))
					# And again over local network
					tentativeLocalPeerAddr = local
					enetConnection.connect_to_host(local, int(localport))
					# We're done with the holepunch peer now
				_:
					print("unknown response ", response)

	# We only need one of these
#	if embeddedPeer == tentativePeer:
#		tentativeLocalPeer.peer_disconnect()
#	elif embeddedPeer == tentativeLocalPeer:
#		tentativePeer.peer_disconnect()
#	else:
#		print("What?")
#		breakpoint

	#Start Timers
	$Timers/StatTimer.start()
	return [embeddedPeer.get_remote_address(), embeddedPeer.get_remote_port()]

# Called when the node enters the scene tree for the first time.
func _ready():
	# Start with the home panel visible and the side panel minimized
	_on_home_pressed()
	_on_hamburger_toggled(true)


func ProcessHolepunch(bytes:PackedByteArray):
	pass


func ProcessControl(bytes:PackedByteArray):
	pass


func ProcessStats(bytes:PackedByteArray):
	var message:Dictionary = JSON.parse_string(bytes.get_string_from_utf8())
	if message['error'] != ERROR.OK:
		printerr("STATS ERROR: ", message['error'])

	match message['message_type'] as MESSAGE:
		MESSAGE.GET_STATS:
			$HBoxContainer/HomePanel/VBoxContainer/Temperature/Value.text = "%2.1f˚" % message['temp']
			$HBoxContainer/HomePanel/VBoxContainer/Ph/Value.text = "%2.1f" % message['ph']


func ProcessVideo(bytes:PackedByteArray):
	if len(bytes) > 0:
		$HBoxContainer/HomePanel/VBoxContainer/Camera.DrawFrame(bytes)


func RequestVideo():
	embeddedPeer.send(CHANNEL.VIDEO, PackedByteArray([1]), ENetPacketPeer.FLAG_UNRELIABLE_FRAGMENT | ENetPacketPeer.FLAG_UNSEQUENCED)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if not embeddedPeer:
		return
	
	var type_peer_data_channel = enetConnection.service(0)

	var event_type = type_peer_data_channel[0]
	var peer:ENetPacketPeer = type_peer_data_channel[1]
	var channel:int = type_peer_data_channel[3]
	
	if $HBoxContainer/HomePanel/VBoxContainer/Camera.is_visible_in_tree():
		RequestVideo()
	
	match event_type:
		ENetConnection.EVENT_RECEIVE:
			var bytes = peer.get_packet()
			
			match channel:
				CHANNEL.HOLEPUNCH:
					ProcessHolepunch(bytes)
				
				CHANNEL.CONTROL:
					ProcessControl(bytes)

				CHANNEL.STATS:
					ProcessStats(bytes)

				CHANNEL.VIDEO:
					ProcessVideo(bytes)


# Toggle visibility of side pannel buttons
func _on_hamburger_toggled(button_pressed):
	for child in $HBoxContainer/SidePanel/VBoxContainer.get_children():
		if child != $HBoxContainer/SidePanel/VBoxContainer/Hamburger:
			child.visible = button_pressed


# Enable the home panel and disable all others
func _on_home_pressed():
	homePanel.visible = true
	settingsPanel.visible = false


# Enable the settings pannel and disable all others
func _on_settings_pressed():
	homePanel.visible = false
	settingsPanel.visible = true


func _on_connect_pressed():
	$HBoxContainer/HomePanel/VBoxContainer/IP/Label.text = "Connecting..."
	$HBoxContainer/HomePanel/VBoxContainer/IP/Value.text = "..."
	var peer = ConnectToPeerEnet()
	$HBoxContainer/HomePanel/VBoxContainer/IP/Label.text = "Connected to: "
	$HBoxContainer/HomePanel/VBoxContainer/IP/Value.text = peer[0] + ":" + str(peer[1])

func _on_disconnect_pressed():
	$HBoxContainer/HomePanel/VBoxContainer/IP/Label.text = "Not connected"
	$HBoxContainer/HomePanel/VBoxContainer/IP/Value.text = ""
	embeddedPeer.peer_disconnect()

func _on_stat_timer_timeout():
	var packet:PackedByteArray = PackedByteArray([MESSAGE.GET_STATS])
	embeddedPeer.send(CHANNEL.STATS, packet, ENetPacketPeer.FLAG_RELIABLE)








