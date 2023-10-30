extends PanelContainer


func UpdateSettings(message:Dictionary):
	var hours = message["feed_time"][0]
	var minutes = message["feed_time"][1]
	var length = message["feed_length"]
	var temp_min = message["temp_warning"][0]
	var temp_max = message["temp_warning"][1]
	var ph_min = message["ph_warning"][0]
	var ph_max = message["ph_warning"][1]
	
	$VBoxContainer/FeedTime/Hours.value = hours
	$VBoxContainer/FeedTime/Minutes.value = minutes
	$VBoxContainer/FeedLength/Length.value = length
	$VBoxContainer/TempWarning/Min.value = temp_min
	$VBoxContainer/TempWarning/Max.value = temp_max
	$VBoxContainer/PhWarning/Min.value = ph_min
	$VBoxContainer/PhWarning/Max.value = ph_max
