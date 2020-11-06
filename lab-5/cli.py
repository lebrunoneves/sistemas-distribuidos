import sys
import socket
import struct
from select import select

HOST = 'localhost'
PORT = 7000

inputs = [sys.stdin]

help_list = {
	'insere <no_id> <chave> <valor>' : 'Inserir novo par chave-valor em nó',
	'busca <no_id> <chave>': 'Buscar por chave em nó'
}

def help():
	menu = '\n'
	menu += '{:^40} {:^40}\n'.format('COMANDO', 'DESCRICAO')
	
	for k, v in help_list.items():
		menu += '{:40} {:40}\n'.format(k, v)
	
	return menu
	


def initialize_client():
	# cria o socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Internet( IPv4 + TCP) 

	# vincula a localizacao do servidor
	sock.bind((HOST, PORT))

	# coloca-se em modo de espera por conexoes
	sock.listen(5) 

	# configura o socket para o modo nao-bloqueante
	sock.setblocking(False)

	# inclui o socket principal na lista de entradas de interesse
	inputs.append(sock)

	return sock


def send(sock, data):
	length = len(data)
	sock.sendall(struct.pack('!I', length))
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
	

def insert(node, key, value):
	# estabelece conexao com nó
	sock = socket.socket()
	sock.connect((HOST, 5000 + int(node)))
	
	msg = str.encode('insere {} {}'.format(key, value));
	send(sock, msg)
	
	sock.close()


def find(node, key):
	# estabelece conexao com nó
	sock = socket.socket()
	sock.connect((HOST, 5000 + int(node)))
	
	msg = str.encode('busca {} {}'.format(PORT, key));
	send(sock, msg)
	
	sock.close()

sock = initialize_client()

print(help())

while True:
	try:
		print('> ', end='', flush=True)
		
		read, write, exception = select(inputs, [], [])
		
		for req in read:
			if req == sys.stdin: #entrada padrao
				cmd = input()
				if cmd == '': #ignorar comandos vazios
					continue
				if cmd == 'exit':
					raise SystemExit()		
				elif cmd.startswith('insere'):
					cmd = cmd.split()
					node = cmd[1]
					key = cmd[2]
					value = cmd[3]
					insert(node, key, value)
					
				elif cmd.startswith('busca'):
					cmd = cmd.split()
					node = cmd[1]
					key = cmd[2]
					find(node, key)
					
			elif req == sock: #pedido de conexao
				newsock, endr = sock.accept()
				
				msg = recv(newsock)
				print('\t', end='')
				print(str(msg, encoding='utf-8'))
				
				newsock.close()
	except IndexError:
		print('\tErro no comando')
	except ConnectionRefusedError:
		print('\tNó desativado ou inexistente')	
	except (KeyboardInterrupt, SystemExit, EOFError):
		print('\n\tTerminou')		
		sys.exit()	
			
			
			
			
			
			
