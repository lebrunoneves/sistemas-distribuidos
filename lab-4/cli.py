import socket
import struct
from select import select
import sys
import os

HOST = 'localhost'
PORT = 5004

sock = socket.socket()

sock.connect((HOST, PORT))

inputs = [sys.stdin, sock]

help_list = {
	'help' : 'Lista de comandos',
	'me': 'Perfil conectado',
	'online' : 'Listar usuarios disponíveis',
	'login <username>' : 'Iniciar sessão no sistema',
	'logout' : 'Encerrar sessão no sistema',
	'@username <msg>' : 'Enviar mensagem a usuário',
	'clear': 'Limpar tela',
	'exit' : 'Desconectar do bate-papo'
}


def help():
	menu = '\n'
	menu += '{:^18} {:^35}\n'.format('COMANDO', 'DESCRICAO')
	
	for k, v in help_list.items():
		menu += '{:18} {:35}\n'.format(k, v)
	
	return menu


def send(sock, data):
	length = len(data)
	sock.sendall(struct.pack('!I', length)) # !I = padrão de envio na rede (big-endian) e formato unsigned int
	sock.sendall(data)


def recv(sock):
	lengthbuf = recvall(sock, 4)

	if not lengthbuf:
		return None

	length, = struct.unpack('!I', lengthbuf)
	return recvall(sock, length)


def recvall(sock, count):
	buf = b''
	while count:
		newbuf = sock.recv(count)
		if not newbuf:
			return None
		buf += newbuf
		count -= len(newbuf)
	return buf


print('{:^40}\n'.format('BEM-VINDO(A)!'))
print(help())

while True:

	print('\n>>> ', end='', flush=True)
	
	read, write, exception = select(inputs, [], [])

	for req in read:
		if req == sys.stdin: #entrada padrao
			cmd = input()
			if cmd == '': #ignorar comandos vazios
				continue
			elif cmd == 'clear': #limpa o terminal
				os.system('clear')
			elif cmd == 'help': #lista de comandos
				print(help())	
			elif cmd == 'exit': #solicitacao de finalizacao do servidor
				sock.close()
				sys.exit()
			else:
				send(sock, str.encode(cmd)) #envia comando ao servidor
		else: #mensagem do servidor
			msg = recv(sock)
			print(str(msg, encoding='utf-8'))
			
			
