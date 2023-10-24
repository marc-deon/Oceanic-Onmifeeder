class_name PacketPeerUDPTimeout
extends PacketPeerUDP

var _timeout_time:float = 0.2
signal timeout


func wait_timeout() -> bool:
	await Engine.get_main_loop().create_timer(_timeout_time).timeout
	
	if get_available_packet_count() > 0:
		return true
	else:
		timeout.emit()
		return false
	
func set_timeout(_timeout:float):
	_timeout_time = _timeout
