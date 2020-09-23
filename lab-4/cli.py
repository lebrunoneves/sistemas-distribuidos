import socket
from select import select
import sys

HOST = 'localhost'
PORT = 5004

sock = socket.socket()

sock.connect((HOST, PORT))

inputs = [sys.stdin, sock]

help_list = {
	'help' : 'Lista de comandos',
	'online' : 'Listar usuarios disponíveis',
	'login <username>' : 'Iniciar sessão no sistema',
	'logout' : 'Encerrar sessão no sistema',
	'@username <msg>' : 'Enviar mensagem a usuário',
	'exit' : 'Desconectar do bate-papo'
}

def help():
	menu = '\n'
	menu += '{:^18} {:^35}\n'.format('COMANDO', 'DESCRICAO')
	
	for k, v in help_list.items():
		menu += '{:18} {:35}\n'.format(k, v)
	
	return menu

print('{:^40}\n'.format('BEM-VINDO(A)!'))
print(help())

while True:

	print('\n> ', end='', flush=True)
	
	read, write, exception = select(inputs, [], [])

	for req in read:
		if req == sys.stdin: #entrada padrao
			cmd = input()
			if cmd == 'help': #lista de comandos
				print(help())	
			elif cmd == 'exit': #solicitacao de finalizacao do servidor
				sock.close()
				sys.exit()
			else:
				sock.send(str.encode(cmd)) #envia comando ao servidor
		else: #mensagem do servidor
			msg = sock.recv(1024)
			print(str(msg, encoding='utf-8'))
			
			
