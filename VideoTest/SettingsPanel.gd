extends PanelContainer
# TODO: Probably a lot of this file should moved to a settings singleton.
signal language_updated(locale:String)
signal theme_updated(light:bool)
signal apply_remote
signal reset_remote

var use24Hour:bool
var useCelsius:bool
var _useLight:bool # This is only a local variable.

const _languages := ["en_US", "ja", "eo"]
enum TIME_FORMAT {TIME_12, TIME_24}
enum TEMP_FORMAT {TEMP_F, TEMP_C}
enum THEME {THEME_DARK, THEME_LIGHT}


func _ready():
	ApplyLocalSettings(ReadLocalSettings())


# Read the local settings file and return a corrosponding dictionary
func ReadLocalSettings() -> Dictionary:
	var file := FileAccess.open("user://LocalSettings.json", FileAccess.READ)
	if file:
		return JSON.parse_string(file.get_as_text())
	else:
		# error
		# Return default
		return {
			'language': "en_US",
			'time_format': TIME_FORMAT.TIME_12,
			'temp': TEMP_FORMAT.TEMP_F,
			'theme': THEME.THEME_DARK
		}


# Apply local settings from a given dictionary
func ApplyLocalSettings(settings:Dictionary) -> void:
	var lang_index = _languages.find(settings["language"])
	$"Tabs/Local Settings/List/Languages/ItemList".select(lang_index)
	_on_language_updated(-1, settings["language"])
	$"Tabs/Local Settings/List/TimeFormat/ItemList".select(settings["time_format"])
	on_time_format_updated(settings["time_format"])
	$"Tabs/Local Settings/List/TempFormat/ItemList".select(settings["temp"])
	on_temp_format_updated(settings["temp"])
	$"Tabs/Local Settings/List/Theme/ItemList".select(settings["theme"])
	on_theme_updated(settings["theme"])


# Write currently applied local settings to file, return error
func WriteLocalSettings() -> bool:
	var d := {
			'language': TranslationServer.get_locale(),
			'time_format': 	int(use24Hour),
			'temp': 		int(useCelsius),
			'theme': 		int(_useLight)
		}
	var file := FileAccess.open("user://LocalSettings.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(d))
		return false
	else:
		return true


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
	var foo1 = $"Tabs/Remote Settings/List/FeedTime/Hours".value
	var foo2 = $"Tabs/Remote Settings/List/FeedTime/Minutes".value
	var foo3 = $"Tabs/Remote Settings/List/FeedLength/Length".value
	var foo4 = $"Tabs/Remote Settings/List/TempWarning/Min".value
	var foo5 = $"Tabs/Remote Settings/List/TempWarning/Max".value
	var foo6 = $"Tabs/Remote Settings/List/PhWarning/Min".value
	var foo7 = $"Tabs/Remote Settings/List/PhWarning/Max".value
	return {
	"feed_time":    [foo1, foo2],
	"feed_length":  foo3,
	"temp_warning": [foo4, foo5],
	"ph_warning":   [foo6, foo7]
	}


func SetRemote(connected:bool):
	$"Tabs/Remote Settings/List/FeedTime/Hours".editable = connected
	$"Tabs/Remote Settings/List/FeedTime/Minutes".editable = connected
	$"Tabs/Remote Settings/List/FeedLength/Length".editable = connected
	$"Tabs/Remote Settings/List/TempWarning/Min".editable = connected
	$"Tabs/Remote Settings/List/TempWarning/Max".editable = connected
	$"Tabs/Remote Settings/List/PhWarning/Min".editable = connected
	$"Tabs/Remote Settings/List/PhWarning/Max".editable = connected


func _on_save_local_pressed():
	WriteLocalSettings()


func _on_apply_remote_pressed():
	apply_remote.emit()


func _on_reset_remote_pressed():
	reset_remote.emit()


func _on_feed_length_value_changed(value):
	$"Tabs/Remote Settings/List/FeedLength/Length".suffix = tr_n("SECONDS_TIME", "", value)


## Local Settings

func _on_language_updated(index, lang=""):
	# If a language is provided via string, index will be unused
	if not lang:
		lang = _languages[index]
	language_updated.emit(lang)
	var widget = $"Tabs/Remote Settings/List/FeedLength/Length"
	widget.suffix = tr_n("SECONDS_TIME", "", widget.value)

func on_time_format_updated(index):
	use24Hour = bool(index)
	print("use24Hour ", use24Hour)

func on_temp_format_updated(index):
	useCelsius = bool(index)
	print("useCelsius ", useCelsius)

func on_theme_updated(index):
	_useLight = index
	theme_updated.emit(index == THEME.THEME_LIGHT)
