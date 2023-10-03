extends TextureRect
# This is the app.

const host_name := "4800.highlyderivative.games"
var host_ip 	:= ""
const host_port := 4800
var username    := "Poseidon"

var hp_public := ""
var hp_local  := ""
var holepunched_ip   := ""
var holepunched_port := 0

var peers:PacketPeerUDP = PacketPeerUDP.new()

func create_texture_from_pool_byte_array(byte_array):
	# Use the raw bytes to construct an Image
	var img = Image.new()
	img.load_jpg_from_buffer(byte_array)
	# Create a Texture from the image and return it
	return ImageTexture.new().create_from_image(img)

# Called when the node enters the scene tree for the first time.
func _ready():
	host_ip = IP.resolve_hostname(host_name)
	peers.connect_to_host(host_ip, host_port)
	get_node("../IP/Value").text = host_name + ":" + str(host_port)


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	if not is_visible_in_tree():
		return
	
	while holepunched_ip == "":
		peers.put_packet(("PUNCH " + username).to_utf8_buffer())
		var return_packet = peers.get_packet()
		if not return_packet:
			return
		var return_string = return_packet.get_string_from_utf8()
		return_string = return_string.strip_edges()
		print("returned", return_packet)
		
		if return_string == "INVALID USERNAME":
			await get_tree().create_timer(5).timeout
			return
		else:
			var parts = return_string.split(" ")
			if parts[0] != "PUNCHING":
				print("Invalid response", parts)
			var hp_public = parts[1]
			# TODO: If we want to support same-NAT connections, we should use hp_local,
			# see which of the two responds (first), and use that as the holepunched
			holepunched_ip = hp_public
			#hp_local = parts[2]
			holepunched_port = int(parts[3])
			
			return
	
	print("requesting frame from", holepunched_ip)
	
	# Request next frame
	var p = peers.get_packet()
	if len(p) > 0:
		var t = create_texture_from_pool_byte_array(p)
		set_texture(t)
		print(get_texture())
	peers.put_var(1)
