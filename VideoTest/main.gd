extends Control

@onready var homePanel = $HBoxContainer/HomePanel
@onready var settingsPanel = $HBoxContainer/SettingsPanel

signal connected(ip, port)
signal disconnected

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
	FEED_ERROR,
	SAVE_ERROR
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

const hp_addr := "highlyderivative.games"
const hp_port := 4800
var hp_key    := "poseidon"

var enetConnection:ENetConnection = ENetConnection.new()
var embeddedPeer:ENetPacketPeer

# Holepunch stuff
var hpPeer:ENetPacketPeer
var conn_packet:PackedByteArray
var tentativePeerAddr:String
var tentativeLocalPeerAddr:String

func ConnectToHolepunch() -> void:
	# Connect to holepunch server
	hpPeer = enetConnection.connect_to_host(hp_addr, hp_port)
	print("connect to hp")
	
	# This is the request to connect that we will send later
	var s = " ".join(["CONN", IP.get_local_addresses()[0], hp_key, enetConnection.get_local_port()])
	conn_packet = s.to_utf8_buffer()	


# Called when the node enters the scene tree for the first time.
func _ready():
	# Bind to all IPv4 addresses, any port; we're connecting, not listening
	enetConnection.create_host_bound("0.0.0.0", 0)
	
	# Start with the home panel visible and the side panel minimized
	_on_home_pressed()
	_on_hamburger_toggled(true)
	SetRemote(false)


func ProcessHolepunch(type_peer_data_channel:Array):
	var event_type:ENetConnection.EventType = type_peer_data_channel[0]
	var peer:ENetPacketPeer = type_peer_data_channel[1]
	
	match event_type:
		ENetConnection.EVENT_CONNECT:
			var peerAddr:String = peer.get_remote_address()
			
			# Connected to holepunch server successfully
			if peerAddr == hpPeer.get_remote_address():
				hpPeer = peer
				hpPeer.send(CHANNEL.HOLEPUNCH, conn_packet, hpPeer.FLAG_RELIABLE)
				print("sent conn packet")
			
			# Found a valid connection to embedded over local network
			elif peerAddr == tentativeLocalPeerAddr:
				embeddedPeer = peer
				connected.emit(peer.get_remote_address(), peer.get_remote_port())
				SetRemote(true)
			
			# Found a valid connection to embedded over internet
			elif peerAddr == tentativePeerAddr:
				embeddedPeer = peer
				connected.emit(peer.get_remote_address(), peer.get_remote_port())
				SetRemote(true)


		ENetConnection.EVENT_RECEIVE:
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


func ProcessControl(type_peer_data_channel:Array):
	var bytes = type_peer_data_channel[1].get_packet()
	var message:Dictionary = JSON.parse_string(bytes.get_string_from_utf8())
	if message['error'] != ERROR.OK:
		printerr("PROCESS ERROR: ", message['error'] as ERROR)
	
	match message['message_type'] as MESSAGE:
		MESSAGE.GET_SETTINGS:
			print("got settings")
			$HBoxContainer/SettingsPanel.UpdateSettings(message)
		
		MESSAGE.SAVE_SETTINGS:
			var e:ERROR = message['error']
			var modal := AcceptDialog.new()
			if e == ERROR.OK:
				modal.title = "Success"
				modal.set_text("Saved successfully")
			else:
				modal.title = "Setting Save Error"
				modal.set_text(str(e))
			modal.popup_exclusive_centered(get_tree().root)

		MESSAGE.MANUAL_FEED:
			var e:ERROR = message['error']
#			var modal := AcceptDialog.new()
			if e == ERROR.OK:
				$HBoxContainer/HomePanel/VBoxContainer/FadeLabel.fade_in("Fed successfully!", Color.GREEN)
			else:
				$HBoxContainer/HomePanel/VBoxContainer/FadeLabel.fade_in("Feed error!", Color.RED)


func ProcessStats(type_peer_data_channel:Array):
	var bytes = type_peer_data_channel[1].get_packet()
	var message:Dictionary = JSON.parse_string(bytes.get_string_from_utf8())
	if message['error'] != ERROR.OK:
		printerr("STATS ERROR: ", message['error'])

	match message['message_type'] as MESSAGE:
		MESSAGE.GET_STATS:
			$HBoxContainer/HomePanel/VBoxContainer/Temperature/Value.text = "%2.1f˚" % message['temp']
			$HBoxContainer/HomePanel/VBoxContainer/Ph/Value.text = "%2.1f" % message['ph']
			var t = message["last_feed"]
			
			# Aside from the month, these are all numbers (we're ignoring AM/PM for now).
			var year = t[0]
			# THis gets the localized month, e.g. 10 -> October, or 10 -> Oktobro
			var month = tr("MONTH_" + str(t[1]))
			var day = t[2]
			var hour = t[3]
			var minute = t[4]
			
			# Good lord 12 hour time sucks ass. wtf?
			var ampm = ""
			if TranslationServer.get_locale() == "en_US":
				ampm = "AM" if hour < 12 else "PM"
				hour = int(hour) % 12
				if hour == 0:
					hour = 12
			
			# tr() fetches the apropriate format for the given locale,
			# and .format supplies the apropriate substiutions
			$HBoxContainer/HomePanel/VBoxContainer/LastFeed/Value.text =tr(
				"DATE_TIME_FORMAT"
				).format({ YEAR = year, MONTH = month, DAY = day, HOUR = hour, MINUTE = minute, AMPM = ampm })


func ProcessVideo(type_peer_data_channel:Array):
	var bytes = type_peer_data_channel[1].get_packet()
	if len(bytes) > 0:
		$HBoxContainer/HomePanel/VBoxContainer/Camera.DrawFrame(bytes)


func RequestVideo():
	if embeddedPeer.get_state() == embeddedPeer.STATE_CONNECTED:
		embeddedPeer.send(CHANNEL.VIDEO, PackedByteArray([1]), ENetPacketPeer.FLAG_UNRELIABLE_FRAGMENT | ENetPacketPeer.FLAG_UNSEQUENCED)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	
	var type_peer_data_channel = enetConnection.service(0)

	var event_type:ENetConnection.EventType = type_peer_data_channel[0]
	var peer:ENetPacketPeer = type_peer_data_channel[1]
	var channel:CHANNEL = type_peer_data_channel[3]
	
	if $HBoxContainer/HomePanel/VBoxContainer/Camera.is_visible_in_tree():
		if embeddedPeer:
			RequestVideo()
	
	match [event_type, channel]:
		[_, CHANNEL.HOLEPUNCH]:
			ProcessHolepunch(type_peer_data_channel)
		
		[ENetConnection.EVENT_CONNECT, CHANNEL.NONE]:
			ProcessHolepunch(type_peer_data_channel)
		
		[ENetConnection.EVENT_RECEIVE, CHANNEL.CONTROL]:
			ProcessControl(type_peer_data_channel)

		[ENetConnection.EVENT_RECEIVE, CHANNEL.STATS]:
			ProcessStats(type_peer_data_channel)

		[ENetConnection.EVENT_RECEIVE, CHANNEL.VIDEO]:
			ProcessVideo(type_peer_data_channel)
		
		[ENetConnection.EVENT_DISCONNECT, _]:
			if embeddedPeer and peer == embeddedPeer:
				disconnected.emit()
		
		[ENetConnection.EVENT_NONE, _]:
			pass
		
		[var ev, var chan]:
			print("unknown event-channel ", ev, " ", chan)


# Toggle visibility of side pannel buttons
func _on_hamburger_toggled(button_pressed):
	for child in $HBoxContainer/SidePanel/VBoxContainer.get_children():
		if child != $HBoxContainer/SidePanel/VBoxContainer/Hamburger:
			child.visible = button_pressed


# Enable the home panel and disable all others
func _on_home_pressed():
	homePanel.visible = true
	settingsPanel.visible = false
	$HBoxContainer/SidePanel/VBoxContainer/Settings.disabled = false
	$HBoxContainer/SidePanel/VBoxContainer/Home.disabled = true


# Enable the settings pannel and disable all others
func _on_settings_pressed():
	homePanel.visible = false
	settingsPanel.visible = true
	$HBoxContainer/SidePanel/VBoxContainer/Settings.disabled = true
	$HBoxContainer/SidePanel/VBoxContainer/Home.disabled = false


func _on_connect_success(ip:String, port:int):
	$Timers/StatTimer.start()
	RefreshSettings()
	display_ip(ip, port)


func SetRemote(connected:bool):
	$HBoxContainer/SidePanel/VBoxContainer/Connect.disabled = connected
	$HBoxContainer/SidePanel/VBoxContainer/Disconnect.disabled = not connected
	
	$HBoxContainer/SettingsPanel.SetRemote(connected)


func _on_connect_pressed():
	ConnectToHolepunch()
	$HBoxContainer/HomePanel/VBoxContainer/IP.text = "Connecting..."


func _on_disconnect_pressed():
	$HBoxContainer/HomePanel/VBoxContainer/IP.text = "Not connected"
	if embeddedPeer:
		embeddedPeer.peer_disconnect()


func _on_stat_timer_timeout():
	var packet:PackedByteArray = PackedByteArray([MESSAGE.GET_STATS])
	if embeddedPeer.get_state() == embeddedPeer.STATE_CONNECTED:
		embeddedPeer.send(CHANNEL.STATS, packet, ENetPacketPeer.FLAG_RELIABLE)


func RefreshSettings():
	var packet = JSON.stringify({"message_type":MESSAGE.GET_SETTINGS}).to_utf8_buffer()
	embeddedPeer.send(CHANNEL.CONTROL, packet, ENetPacketPeer.FLAG_RELIABLE)


func _on_settings_remote_apply_pressed():
	var d = $HBoxContainer/SettingsPanel.GetSettings()
	d["message_type"] = MESSAGE.SAVE_SETTINGS
	var packet = JSON.stringify(d).to_utf8_buffer()
	embeddedPeer.send(CHANNEL.CONTROL, packet, ENetPacketPeer.FLAG_RELIABLE)


func _on_feed_button_pressed():
	if embeddedPeer:
		$HBoxContainer/HomePanel/VBoxContainer/FadeLabel.fade_in("Feeding...")
		var packet = JSON.stringify({"message_type": MESSAGE.MANUAL_FEED}).to_utf8_buffer()
		embeddedPeer.send(CHANNEL.CONTROL, packet, ENetPacketPeer.FLAG_RELIABLE)
	else:
		$HBoxContainer/HomePanel/VBoxContainer/FadeLabel.fade_in("Not connected!", Color.RED)


func display_ip(ip:String="", port:int=0):
	if embeddedPeer and not ip:
		ip = embeddedPeer.get_remote_address()
		port = embeddedPeer.get_remote_port()
		
	$HBoxContainer/HomePanel/VBoxContainer/IP.text = tr("Connected to: ").format({ip=ip, port=port})


func ChangeLocale(locale:String):
	TranslationServer.set_locale(locale)
	display_ip()

