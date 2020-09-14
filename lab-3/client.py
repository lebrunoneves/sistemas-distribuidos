import socket

HOST = 'localhost'
PORT = 5003

sock = socket.socket()

sock.connect((HOST, PORT))

filename = input()
while filename != 'exit':
	sock.send(str.encode(filename))

	msgBack = sock.recv(1024)
	print(str(msgBack, encoding='utf-8'))
	
	filename = input()

sock.close()