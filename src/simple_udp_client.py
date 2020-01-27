import math
from struct import unpack, pack

def decode_osc(data, current_string=""):
	length = data.find(b'\0')
	if length == -1:
		return current_string[:-1]
	string = data[0:length].decode('latin-1')
	if string.find(',s') != -1:
		string = ""
	elif string == "int":
		string = ""
	elif string == ",i":
		nextData = int(math.ceil((length+1) / 4.0) * 4)
		return unpack(">i", data[nextData:nextData+4])[0]
	else:
		string = string + " "
	nextData = int(math.ceil((length+1) / 4.0) * 4)
	return decode_osc(data[nextData:], current_string + string)

def encode_osc(data):
	if type(data) is str:
		byte_string = b''
		for count, string in enumerate(data.split(' ')):
			if count == 1:
				n_words = len(data.split(' ')) - 1
				OSCstringLength = math.ceil((n_words+2) / 4.0) * 4
				byte_string = byte_string + pack(">%ds" % (OSCstringLength), b"," + b"s"*n_words)
			OSCstringLength = math.ceil((len(string)+1) / 4.0) * 4
			byte_string = byte_string +  pack(">%ds" % (OSCstringLength), string.encode('latin-1'))
		return byte_string
	if type(data) is int:
		return pack(">4s", b"int") + pack(">4s", b",i") + pack(">i", data)

if __name__ == '__main__':
	import socket
	# Here we define the UDP IP address as well as the port number that we have
	# already defined in the client python script.
	UDP_IP_ADDRESS = "192.168.1.2"
	UDP_PORT_NO = 5005

	# declare our serverSocket upon which
	# we will be listening for UDP messages
	serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# One difference is that we will have to bind our declared IP address
	# and port number to our newly declared serverSock
	serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))

	while True:
	    data, addr = serverSock.recvfrom(1024*2)
	    print(data)
	    decoded = decode_osc(data)
	    print(decoded)
	    send_str = "\nThe Attainder taken from Jonathan Butler\n(Reverse) The day the Court were present w'th them. \nBridget Butler and Sarah Good affirmed in open Court that the above n'th Press were not persons, but were  spirits of grace from God: and the afflicted asked whether they were  any way got along with him; but they denied it, their Lord being  with them as a friend or no way got along with them. \nBrought up on a Gospel Question, was it not to yourself why no one hath taken care to notice  who you are a thing contrary to the Peace of our Sovereign Lord and Lady the King and  Queen? I meant myself; in the end I do not know; and am sure there is a God in heaven to find God in every soul -- the afflicted, they can not be found in any  other body to give their opinion of my truth.\nI can give no other opinion of things besides my soul.\nI know it is false to accuse the Press which does all this to set up this evident malice. to the best of my faculties.\nI am as clear as the clear mouther from any other person or spirit  or no spirit. \nIf you will"
	    sock.sendto(encode_osc(send_str), (UDP_IP_ADDRESS, UDP_PORT_NO))