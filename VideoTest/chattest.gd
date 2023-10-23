extends VBoxContainer
const ChatMessage = preload("res://chatmessage.tscn")
const RudpPort = preload("res://rudp_port.gd")

const nana = "大場なな"
const junna = "星見純那"

var localUser:String = nana
var send_socket:RudpPort
var receive_socket:RudpPort

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

func DecodeMessage(msg:String) -> Dictionary:
	var utf8 = Marshalls.base64_to_utf8(msg)
	return JSON.parse_string(utf8)

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
	send_socket.Send(s)


func _ready():
	$DialogueTimer.wait_time = sec_per_chara
	$DialogueTimer.start()

func init(_send_socket:RudpPort, _receive_socket:RudpPort, username:String):
	ClearLog()
	localUser = username
	$HBoxContainer/RichTextLabel.text = localUser
	var color = Color.YELLOW if username == nana else Color.LIGHT_SKY_BLUE if username == junna else Color.ANTIQUE_WHITE
	$HBoxContainer/RichTextLabel.add_theme_color_override("default_color", color)
	self.send_socket = _send_socket
	self.receive_socket = _receive_socket
	AddMessage("System", Time.get_time_string_from_system(false), "Welcome to the chat, %s!" % localUser)

func _process(delta):
	Listen()

func Listen() -> void:
	var received = await receive_socket.Receive()
	var string:String = received.string
	# In hindsight, doing a substring here in python lazy. Python might do it,
	# but of *course* other languages won't use the b"" format. They might not
	# even have byte literals in the first place!
	var message:Dictionary = DecodeMessage(string)
	
	if message['system'] and message['text'] == "DISCONNECT":
		pass
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
