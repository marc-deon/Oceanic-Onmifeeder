extends Control

@onready var homePanel = $HBoxContainer/HomePanel
@onready var settingsPanel = $HBoxContainer/SettingsPanel

const PLACEHOLDER_MONTH_FORMAT := "numeric"
#const PLACEHOLDER_MONTH_FORMAT := "full"

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
#var hp_key    := "poseidon"

var enetConnection:ENetConnection
var embeddedPeer:ENetPacketPeer

# Holepunch stuff
var hpPeer:ENetPacketPeer
var conn_packet:PackedByteArray
var shouldTryConnect:bool
var tentativePeerAddr:String
var tentativeLocalPeerAddr:String
var tentativePort:int
var tentativeLocalPort:int

var _demo_temp:float
var _demo_flag:=false

func ConnectToHolepunch(user, password) -> void:
	print("connect to hp")
	# Connect to holepunch server
	hpPeer = enetConnection.connect_to_host(hp_addr, hp_port)
	
	# This is the request to connect that we will send later
	var s = " ".join([
		"CONN",							# command
		IP.get_local_addresses()[0],	# Local IP
		user,							# Username
		password,						# Password
		enetConnection.get_local_port()	# Local port
	])
	conn_packet = s.to_utf8_buffer()


# Called when the node enters the scene tree for the first time.
func _ready():
	enetConnection = ENetConnection.new()
	# Bind to all IPv4 addresses, any port; we're connecting, not listening
	enetConnection.create_host_bound("0.0.0.0", 0)
#	enetConnection.create_host_bound("192.168.0.11", 4850)
	
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
			print("connect event to", peerAddr)
			
			# Connected to holepunch server successfully
			if peerAddr == hpPeer.get_remote_address():
				hpPeer = peer
				hpPeer.send(CHANNEL.HOLEPUNCH, conn_packet, hpPeer.FLAG_RELIABLE)
				print("sent conn packet")
			
			# Found a valid connection to embedded over local network
			elif peerAddr == tentativeLocalPeerAddr:
				embeddedPeer = peer
				connected.emit(peer.get_remote_address(), peer.get_remote_port())
				shouldTryConnect = false
				SetRemote(true)
			
			# Found a valid connection to embedded over internet
			elif peerAddr == tentativePeerAddr:
				embeddedPeer = peer
				connected.emit(peer.get_remote_address(), peer.get_remote_port())
				shouldTryConnect = false
				SetRemote(true)


		ENetConnection.EVENT_RECEIVE:
			var response := Array(peer.get_packet().get_string_from_utf8().split(" "))
			match response:
				["CONNTO", var addr, var local, var port, var localport]:
#					hpPeer.peer_disconnect_later()
					shouldTryConnect = true
					# Try to connect once over internet
					tentativePeerAddr = addr
					tentativePort = int(port)
					# And again over local network
					tentativeLocalPeerAddr = local
					tentativeLocalPort = int(localport)
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
			var temp = message['temp']
			if $HBoxContainer/SettingsPanel.useCelsius:
				temp = (temp - 32) * 5/9
			var temp_warning = settingsPanel.GetSettings()['temp_warning']
			if temp < temp_warning[0] or temp > temp_warning[1]:
				SendTempNotification(temp, temp_warning)
			var ph = message['ph']
			$HBoxContainer/HomePanel/VBoxContainer/Temperature/Value.text = "%2.1f˚" % temp
			$HBoxContainer/HomePanel/VBoxContainer/Ph/Value.text = "%2.1f" % ph
			var t = message["last_feed"]
			
			# Aside from the month, these are all numbers (we're ignoring AM/PM for now).
			var year = t[0]
			# THis gets the localized month, e.g. 10 -> October, or 10 -> Oktobro
			var month = tr("MONTH_" + str(t[1]), PLACEHOLDER_MONTH_FORMAT)
			var day = t[2]
			var hour = t[3]
			var minute = "%02.0f" % t[4]
			
			# Good lord 12 hour time sucks ass. wtf?
			var ampm = ""
			if not $HBoxContainer/SettingsPanel.use24Hour:
				ampm = tr("TIME_AM") if hour < 12 else tr("TIME_PM")
				hour = int(hour) % 12
				if hour == 0:
					hour = 12
#			if 
#				month = tr("MONTH_" + str(t[1]), PLACEHOLDER_MONTH_FORMAT)
#			else:
#				_PLACEHOLDER_MONTH_FORMAT = ""
			
			# tr() fetches the apropriate format for the given locale,
			# and .format supplies the apropriate substiutions
			$HBoxContainer/HomePanel/VBoxContainer/LastFeed/Value.text =tr(
				"DATE_TIME_FORMAT", PLACEHOLDER_MONTH_FORMAT
				).format({ YEAR = year, MONTH = month, DAY = day, HOUR = hour, MINUTE = minute, AMPM = ampm })


func ProcessVideo(type_peer_data_channel:Array):
	var bytes = type_peer_data_channel[1].get_packet()
	if len(bytes) > 0:
		$HBoxContainer/HomePanel/VBoxContainer/Camera.DrawFrame(bytes)


func RequestVideo():
	if embeddedPeer.get_state() == embeddedPeer.STATE_CONNECTED:
		embeddedPeer.send(CHANNEL.VIDEO, PackedByteArray([1]), ENetPacketPeer.FLAG_UNRELIABLE_FRAGMENT | ENetPacketPeer.FLAG_UNSEQUENCED)


func TryConnect():
	enetConnection.connect_to_host(tentativePeerAddr,  tentativePort)
	enetConnection.connect_to_host(tentativeLocalPeerAddr, tentativeLocalPort)

func SendTempNotification(t, temp_warning):
	_demo_flag = false
	if t < temp_warning[0]:
		OS.execute("notify-send", ["Omnifeeder","Warning:\nTemperature low!\n" + str(t) + "˚"])
	if t > temp_warning[1]:
		OS.execute("notify-send", ["Omnifeeder","Warning:\nTemperature high!\n" + str(t) + "˚"])
		
	pass

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	
	if _demo_flag:
		var temp_warning = settingsPanel.GetSettings()['temp_warning']
		print("flag set", _demo_temp, " ", temp_warning[0], " ", temp_warning[1])
		if _demo_temp < temp_warning[0] or _demo_temp > temp_warning[1]:
			SendTempNotification(_demo_temp, temp_warning)
	
	# I don't love this, but... it does work.
	# Fixes the issue of:
	# When going through NAT, the first connection attempt is dropped upon arrival because no outbound data has been sent yet. 
	if shouldTryConnect:
		TryConnect()
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
			print("discon event")
			print("embeddedpeer, peer =", embeddedPeer, peer)
			if embeddedPeer and peer == embeddedPeer:
				disconnected.emit()
		
		[ENetConnection.EVENT_NONE, _]:
			pass
		
		[ENetConnection.EVENT_ERROR, _]:
			printerr("Enet error occurred")
		
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

func on_disconnect():
	$HBoxContainer/HomePanel/VBoxContainer/IP.text = "Not connected"
	SetRemote(false)

func _on_connect_pressed():
	var userpass = $HBoxContainer/SettingsPanel.GetUserPass()
	ConnectToHolepunch(userpass[0], userpass[1])
	$HBoxContainer/HomePanel/VBoxContainer/IP.text = "Connecting..."


func _on_disconnect_pressed():
	on_disconnect()
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
	if embeddedPeer and embeddedPeer.get_state() == embeddedPeer.STATE_CONNECTED:
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


const lighttheme = preload("res://LightTheme.tres")
func ChangeTheme(light):
	if light:
		theme = lighttheme
	else:
		theme = null


func _on_demo_high_pressed():
	_demo_temp = 100
	_demo_flag = true


func _on_demo_low_pressed():
	_demo_temp = -10
	_demo_flag = true
