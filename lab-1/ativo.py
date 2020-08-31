import socket

HOST = 'localhost'
PORT = 5801

sock = socket.socket()

sock.connect((HOST, PORT))

msg = input()
while msg != 'exit':
	sock.send(str.encode(msg))

	msgBack = sock.recv(1024)
	print(str(msgBack, encoding='utf-8'))
	
	msg = input()

sock.close()
