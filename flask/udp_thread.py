#! /usr/bin/env python
from threading import Thread, Event, Lock
import socket
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

class UDPThread(Thread):
    def __init__(self, local_address="127.0.0.1", target_address="127.0.0.1", port_no=5005):
        self.local_address = local_address
        self.target_address = target_address
        self.port_no = port_no
        self.text_lock = Lock()
        self.outputs = []
        self.shutdown_flag = Event()
        self.serverSock = None
        super(UDPThread, self).__init__()
        self.daemon = True

    # Will be called when thread.start is called
    def run(self):
        # declare our serverSocket upon which
        # we will be listening for UDP messages
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # One difference is that we will have to bind our declared IP address
        # and port number to our newly declared serverSock
        self.serverSock.bind((self.local_address, self.port_no))

        while not self.shutdown_flag.is_set():
            data, addr = self.serverSock.recvfrom(1024*2)
            decoded = decode_osc(data)
            self.receive_cb(decoded)

    # Empty function called when a message is recieved to be implemented by user
    def receive_cb(self, msg):
        pass

    # Function to send out text
    def send_text(self, text):
        if not self.serverSock:
            return
        self.serverSock.sendto(encode_osc(str(text)), (self.target_address, self.port_no))