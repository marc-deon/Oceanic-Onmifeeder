extends Control

@onready var homePanel = $HBoxContainer/HomePanel
@onready var settingsPanel = $HBoxContainer/SettingsPanel

enum CHANNEL {
	HOLEPUNCH,
	CONTROL,
	STATS,
	VIDEO,
	MAX
}

enum ERROR {
	ERROR, 
	OK, 
	MALFORMED_TIME, 
	INVALID_TIME, 
	INVALID_LENGTH, 
	TEMP_MINMAX, 
	PH_MINMAX, 
	FEED_ERROR
}

enum MESSAGE {
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
var enetPeer:ENetPacketPeer


func ConnectToPeer():
	#Find Peer 
	var sock := PacketPeerUDPTimeout.new()
	var addr = await sock.connect_to_holepunch(hp_key)
	sock.close()
	
	# ENet stuff
	enetConnection = ENetConnection.new()
	enetConnection.create_host_bound(addr[2], addr[3])
	enetPeer = enetConnection.connect_to_host(addr[0], addr[1])
	enetConnected = true
	$Timers/StatTimer.start()
	return [addr[0], addr[1]]


# Called when the node enters the scene tree for the first time.
func _ready():
	# Start with the home panel visible and the side panel minimized
	_on_home_pressed()
	_on_hamburger_toggled(false)


func ProcessHolepunch(bytes:PackedByteArray):
	pass


func ProcessControl(bytes:PackedByteArray):
	pass


func ProcessStats(bytes:PackedByteArray):
	var message = JSON.parse_string(bytes.get_string_from_utf8())
	var error:ERROR = message[0]
	if error != ERROR.OK:
		print("STATS ERROR: ", error)
	
	message = message[1]
	match message:
		MESSAGE.GET_STATS:
			$HBoxContainer/HomePanel/VBoxContainer/Temperature/Value.text = message['temp']
			$HBoxContainer/HomePanel/VBoxContainer/Ph/Value.text = message['ph']


func ProcessVideo(bytes:PackedByteArray):
	if len(bytes) > 0:
		$HBoxContainer/HomePanel/VBoxContainer/Camera.DrawFrame(bytes)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if not enetConnected:
		return
	
	var type_peer_data_channel = enetConnection.service(0)
	
	if not is_visible_in_tree():
		return
	
	var event_type = type_peer_data_channel[0]
	var peer:ENetPacketPeer = type_peer_data_channel[1]
	var channel:int = type_peer_data_channel[3]
	
	match event_type:
		ENetConnection.EVENT_ERROR:
			pass
		ENetConnection.EVENT_DISCONNECT:
			pass
		ENetConnection.EVENT_NONE:
			pass
		ENetConnection.EVENT_CONNECT:
			pass
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
					# Reply with a 1
					peer.put_packet(PackedByteArray([1]))


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
	var peer = await $HBoxContainer/HomePanel/VBoxContainer/Camera.ConnectToPeer()
	$HBoxContainer/HomePanel/VBoxContainer/IP/Value.text = peer[0] + ":" + str(peer[1])

?
func _on_stat_timer_timeout():
	var packet:PackedByteArray = PackedByteArray([MESSAGE.GET_STATS])
	enetPeer.send(CHANNEL.STATS, packet, ENetPacketPeer.FLAG_RELIABLE)








