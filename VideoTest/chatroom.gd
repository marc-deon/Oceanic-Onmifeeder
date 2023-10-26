extends VBoxContainer
const ChatMessage = preload("res://chatmessage.tscn")

const nana = "大場なな"
const junna = "星見純那"

var localUser:String = nana
var conn:ENetConnection
var peer:ENetPacketPeer
var channel:int

var dialogue = [
	["　　", "   "],
	["大場なな", "純那ちゃん、まだ起きての？ "],
	["　　", "   "],
	["星見純那", "はい、でもたった今完成した、今すぐ寝るよ "],
	["　　", "   "],
	["大場なな", "あっ "],
	["　　", "   "],
	["大場なな", "はい。。。じゃ、おやすみなさい "],
	["　　", "   "],
	["星見純那", "お休み、なな "]
]

const sec_per_chara = 1.0 / 9.0

var dialogue_line = 0
var dialogue_char = 0
func AdvanceDialogue():
	if dialogue_line >= len(dialogue):
		var msg = AddMessage("🦒", Time.get_time_string_from_system(false), "わかります", Color.WHITE)
		msg.kirin()
		$DialogueTimer.stop()
		return
		
	var person = dialogue[dialogue_line][0]
	var line = dialogue[dialogue_line][1]
	if person == localUser:
		$HBoxContainer/TextEdit.text += line[dialogue_char]
	dialogue_char += 1
	
	if dialogue_char >= len(line):
		dialogue_char = 0
		dialogue_line += 1
		
		if person == localUser:
			_on_text_edit_text_submitted($HBoxContainer/TextEdit.text)
	pass

func DecodeMessage(msg:PackedByteArray) -> Dictionary:
	#var utf8 = Marshalls.base64_to_utf8(msg)
	return JSON.parse_string(msg.get_string_from_utf8())

func ClearLog():
	while $Log.get_child_count() > 0:
		$Log.remove_child($Log.get_child(0))


func AddMessage(username:String, time:String, text:String, color:Color=Color.LIGHT_GRAY):
	var m = ChatMessage.instantiate()
	m.init(username, time, text, color)
	$Log.add_child(m)
	return m
	

func SendMessage(time:String, message:String, system:bool=false):
	var s = JSON.stringify({"system":system, "user":localUser, "text":message, "time":time})
	peer.send(self.channel, s.to_utf8_buffer(), ENetPacketPeer.FLAG_RELIABLE)


func _ready():
	$DialogueTimer.wait_time = sec_per_chara
	$DialogueTimer.start()

func init(conn:ENetConnection, peer:ENetPacketPeer, channel:int, username:String):
	print("init")
	ClearLog()
	localUser = username
	$HBoxContainer/RichTextLabel.text = localUser
	var color = Color.YELLOW if username == nana else Color.LIGHT_SKY_BLUE if username == junna else Color.ANTIQUE_WHITE
	$HBoxContainer/RichTextLabel.add_theme_color_override("default_color", color)
	self.conn = conn
	self.peer = peer
	self.channel = channel
	AddMessage("System", Time.get_time_string_from_system(false), "Welcome to the chat, %s!" % localUser)

func _process(delta):
	Listen()

func Listen() -> void:
	var type_peer_data_channel = conn.service(0)
	var event_type = type_peer_data_channel[0]
	var peer:ENetPacketPeer = type_peer_data_channel[1]
	
	match event_type:
		ENetConnection.EVENT_ERROR:
			AddMessage("System", Time.get_time_string_from_system(false), "Error: Disconnected")
		ENetConnection.EVENT_DISCONNECT:
			AddMessage("System", Time.get_time_string_from_system(false), "Disconnected")
		ENetConnection.EVENT_NONE:
			pass
		ENetConnection.EVENT_CONNECT:
			AddMessage("System", Time.get_time_string_from_system(false), "Cconnected")
		ENetConnection.EVENT_RECEIVE:
			var bytes := peer.get_packet()
			var message:Dictionary = DecodeMessage(bytes)
	
			var color = Color.YELLOW if message['user'] == nana else Color.LIGHT_SKY_BLUE if message['user'] == junna else Color.ANTIQUE_WHITE
			AddMessage(message["user"], message["time"], message["text"], color)
	


func _on_text_edit_text_submitted(new_text:String):
	var time = Time.get_time_string_from_system(false)
	var color = Color.YELLOW if localUser == nana else Color.LIGHT_SKY_BLUE if localUser == junna else Color.ANTIQUE_WHITE
	AddMessage(localUser, time, new_text, color)
	$HBoxContainer/TextEdit.clear()
	SendMessage(time, new_text)


func _on_dialogue_timer_timeout():
	AdvanceDialogue()
