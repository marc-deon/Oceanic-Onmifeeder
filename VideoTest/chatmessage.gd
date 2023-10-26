extends HBoxContainer

func init(username:String, time:String, text:String, color:Color):
	$vbox/hbox/User.text = username
	$vbox/hbox/User.add_theme_color_override("default_color", color)
	$vbox/hbox/Time.text = "[i]" + time + "[/i]"
	$vbox/hbox/Message.text = text

func kirin():
	$vbox/hbox/User.add_theme_font_override("normal_font", load("res://NotoColorEmoji.ttf"))
