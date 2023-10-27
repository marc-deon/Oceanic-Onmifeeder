extends TextureRect

func create_texture_from_pool_byte_array(bytes):
	# Use the raw bytes to construct an Image
	var img = Image.new()
	img.load_jpg_from_buffer(bytes)
	# Create a Texture from the image and return it
	return ImageTexture.create_from_image(img)

func DrawFrame(bytes):
	# Request next frame
	var t = create_texture_from_pool_byte_array(bytes)
	set_texture(t)

# Called when the node enters the scene tree for the first time.
func _ready():
	pass




	
