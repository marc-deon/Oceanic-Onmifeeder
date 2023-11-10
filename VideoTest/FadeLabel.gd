extends Label

@export
var fade_in_time:float = 1
@export
var stay_time:float = 3
@export
var fade_out_time:float = 1


func fade_in(message:String="", color:Color=Color.WHITE):
	if message:
		text = message
	
	var half_size = get_parent().size.x/2
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_QUINT)
	
	# Fade in from the right side of parent
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "position:x", 0, fade_in_time).from(half_size)
	tween.parallel().tween_property(self, "modulate", color, fade_in_time)
	
	# Just wait a bit
	tween.tween_interval(stay_time)
	
	# Fade out to the left side of parent
	tween.set_ease(Tween.EASE_IN)
	tween.tween_property(self, "position:x", -half_size, fade_out_time)
	tween.parallel().tween_property(self, "modulate", Color.TRANSPARENT, fade_out_time)


func _ready():
	modulate = Color.TRANSPARENT
