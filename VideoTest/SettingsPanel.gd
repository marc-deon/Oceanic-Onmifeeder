extends PanelContainer
signal language_updated(locale:String)
signal theme_updated(light:bool)
signal apply_remote
signal reset_remote

var use24Hour:bool
var useCelsius:bool

func UpdateSettings(message:Dictionary):
	var hours = message["feed_time"][0]
	var minutes = message["feed_time"][1]
	var length = message["feed_length"]
	var temp_min = message["temp_warning"][0]
	var temp_max = message["temp_warning"][1]
	var ph_min = message["ph_warning"][0]
	var ph_max = message["ph_warning"][1]
	
	$"Tabs/Remote Settings/List/FeedTime/Hours".value = hours
	$"Tabs/Remote Settings/List/FeedTime/Minutes".value = minutes
	$"Tabs/Remote Settings/List/FeedLength/Length".value = length
	$"Tabs/Remote Settings/List/TempWarning/Min".value = temp_min
	$"Tabs/Remote Settings/List/TempWarning/Max".value = temp_max
	$"Tabs/Remote Settings/List/PhWarning/Min".value = ph_min
	$"Tabs/Remote Settings/List/PhWarning/Max".value = ph_max


func GetSettings() -> Dictionary:
	return {
	"feed_time":    [$"Tabs/Remote Settings/List/FeedTime/Hours".value, $"Tabs/Remote Settings/List/FeedTime/Minutes".value],
	"feed_length":  $"Tabs/Remote Settings/List/FeedLength/Length".value,
	"temp_warning": [$"Tabs/Remote Settings/List/TempWarning/Min".value, $"Tabs/Remote Settings/List/TempWarning/Max".value],
	"ph_warning":   [$"Tabs/Remote Settings/List/PhWarning/Min".value, $"Tabs/Remote Settings/PhWarning/Max".value]
	}


func SetRemote(connected:bool):
	$"Tabs/Remote Settings/List/FeedTime/Hours".editable = connected
	$"Tabs/Remote Settings/List/FeedTime/Minutes".editable = connected
	$"Tabs/Remote Settings/List/FeedLength/Length".editable = connected
	$"Tabs/Remote Settings/List/TempWarning/Min".editable = connected
	$"Tabs/Remote Settings/List/TempWarning/Max".editable = connected
	$"Tabs/Remote Settings/List/PhWarning/Min".editable = connected
	$"Tabs/Remote Settings/List/PhWarning/Max".editable = connected


const _languages := ["en_US", "ja", "eo"]
func _on_language_updated(index):
	language_updated.emit(_languages[index])
	var widget = $"Tabs/Remote Settings/List/FeedLength/Length"
	widget.suffix = tr_n("SECONDS_TIME", "", widget.value)


func _on_save_local_pressed():
	pass # Replace with function body.


func _on_apply_remote_pressed():
	apply_remote.emit()


func _on_reset_remote_pressed():
	reset_remote.emit()


func _on_feed_length_value_changed(value):
	$"Tabs/Remote Settings/List/FeedLength/Length".suffix = tr_n("SECONDS_TIME", "", value)
	pass # Replace with function body.


func on_time_format_updated(index):
	use24Hour = bool(index)
	print("use24Hour ", use24Hour)


func on_temp_format_updated(index):
	useCelsius = bool(index)
	print("useCelsius ", useCelsius)

func on_theme_updated(index):
	theme_updated.emit(index == 1)
