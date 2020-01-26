# Again we import the necessary socket python module
import socket
import math
from struct import unpack
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


while True:
    data, addr = serverSock.recvfrom(1024*2)
    print(data)
    print(decode_osc(data))