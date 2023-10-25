extends TextureRect
# This is the app.

const hp_addr := "4800.highlyderivative.games"
const hp_port := 4800
var hp_key    := "poseidon"

var enetConnected:bool = false
var enetConnection:ENetConnection = ENetConnection.new()

func ConnectToPeer():
	#Find Peer 
	var sock := PacketPeerUDPTimeout.new()
	var addr = await sock.connect_to_holepunch(hp_key)
	sock.close()
	
	# ENet stuff
	enetConnection = ENetConnection.new()
	enetConnection.create_host_bound(addr[2], addr[3])
	enetConnection.connect_to_host(addr[0], addr[1])
	enetConnected = true
	return [addr[0], addr[1]]
	


func create_texture_from_pool_byte_array(byte_array):
	# Use the raw bytes to construct an Image
	var img = Image.new()
	img.load_jpg_from_buffer(byte_array)
	# Create a Texture from the image and return it
	return ImageTexture.new().create_from_image(img)

# Called when the node enters the scene tree for the first time.
func _ready():
	pass

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	
	if not enetConnected:
		return
	
	var type_peer_data_channel = enetConnection.service(0)
	
	if not is_visible_in_tree():
		return
	
	var event_type = type_peer_data_channel[0]
	var peer:ENetPacketPeer = type_peer_data_channel[1]
	
	match event_type:
		ENetConnection.EVENT_ERROR:
			pass
		ENetConnection.EVENT_DISCONNECT:
			pass
		ENetConnection.EVENT_NONE:
			pass
		ENetConnection.EVENT_CONNECT:
			pass
		ENetConnection.EVENT_RECEIVE:
			# Request next frame
			var bytes = peer.get_packet()
			if len(bytes) > 0:
				var t = create_texture_from_pool_byte_array(bytes)
				set_texture(t)
				print(get_texture())
			peer.put_packet(PackedByteArray([1]))

	
