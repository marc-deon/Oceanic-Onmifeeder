extends Node

var srcPort:int
var destPort:int
var system:bool
var id:int
var data:PackedByteArray

func Encode() -> PackedByteArray:
	var d = {'srcPort':srcPort,'destPort':destPort,'system':system,'id':id, 'data':string}
	var j := JSON.stringify(d)
	var e = Marshalls.utf8_to_base64(j).to_utf8_buffer()
	return e


func init(_srcPort, _destPort, _system, _id, _data:String):
	self.srcPort = _srcPort
	self.destPort = _destPort
	self.system = _system
	self.id = _id
	self.data = _data.to_utf8_buffer()


# Message <- dict <- json
static func Decode(msg:PackedByteArray):
	var b64 = msg.get_string_from_utf8()
	var utf8 = Marshalls.base64_to_utf8(b64)
	var parsed = JSON.parse_string(utf8)
	var m = new()
	m.srcPort = parsed["srcPort"]
	m.destPort = parsed["destPort"]
	m.system = parsed["system"]
	m.id = parsed["id"]
	# since json doesn't support bytes, the data will come in as a string
	m.data = parsed["data"].to_utf8_buffer()
	
	return m


# Message data as string
var string:String:
	get:
		var foo = data.get_string_from_utf8()
		return foo
