import socket
import server_process

HOST = ''
PORT = 5802

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((HOST, PORT))

sock.listen(1)

newSock, address = sock.accept()

while True:
	filename_bytes = newSock.recv(1024)

	if not filename_bytes:
		break
	
	filename = str(filename_bytes, encoding='utf-8')

	word_counter = server_process.get(filename)

	if word_counter:
		newSock.send(str.encode(str(word_counter)))
	else:
		newSock.send(str.encode('null'))
	
newSock.close()
sock.close()