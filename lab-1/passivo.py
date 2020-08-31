import socket

HOST = ''
PORT = 5801

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((HOST, PORT))

sock.listen(1)

newSock, address = sock.accept()


while True:
	msg = newSock.recv(1024)

	if not msg:
		break
	
	newSock.send(msg)
	
newSock.close()
sock.close()
