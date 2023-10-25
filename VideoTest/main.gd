extends Control

@onready var homePanel = $HBoxContainer/HomePanel
@onready var settingsPanel = $HBoxContainer/SettingsPanel

# Called when the node enters the scene tree for the first time.
func _ready():
	# Start with the home panel visible and the side panel minimized
	_on_home_pressed()
	_on_hamburger_toggled(false)


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
