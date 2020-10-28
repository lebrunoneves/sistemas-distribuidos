import sys
import socket
import select
import struct
from hashlib import sha1 
from threading import Thread
from multiprocessing import Process

HOST = 'localhost'
# valor a partir do qual serao geradas portas paras os nós
START_PORT = 5000

# valores armazenados pelo nó
db = {}

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
	

def initialize_node(port):
	# cria o socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Internet( IPv4 + TCP) 

	# vincula a localizacao do servidor
	sock.bind((HOST, port))

	# coloca-se em modo de espera por conexoes
	sock.listen(5) 

	# configura o socket para o modo nao-bloqueante
	sock.setblocking(False)

	return sock


def insert(node_port, key, value):
	# estabelece conexao com nó
	sock = socket.socket()
	sock.connect((HOST, node_port))
	
	msg = str.encode('insere {} {}'.format(key, value));
	send(sock, msg)
	
	sock.close()


def find(node_port, client, key):
	# estabelece conexao com nó
	sock = socket.socket()
	sock.connect((HOST, node_port))
	
	msg = str.encode('busca {} {}'.format(client, key));
	send(sock, msg)
	
	sock.close()


def find_closest_pred(key_hash, finger_table, n):
	keys_list = list(finger_table.keys())
	closest_pred = finger_table[keys_list[0]]
	distance = key_hash - keys_list[0]
	
	for i in range(1, len(keys_list) ):
		if ( key_hash - keys_list[i] + 2**n) % 2**n < distance:
			closest_pred = finger_table[keys_list[i]]
			distance = key_hash - keys_list[i]
			
	return closest_pred
	
	
def get_hash(key, n):
	return int(sha1(str.encode(key)).hexdigest(), 32) % 2**int(n)

	
def attend_request(clisock, endr, n, node_id, port, finger_table):	
	
	while True:
		#recebe a requisicao em bytes
		req = recv(clisock)
		
		if not req: # dados vazios: cliente encerrou
			clisock.close() # encerra a conexao com o cliente
			return
			
		req = str(req, encoding='utf-8').split()
		
		if req[0] == 'insere':	
			key = req[1]
			value = req[2]
			
			key_hash = get_hash(key, n)
			
			if key_hash == node_id:
				db[key] = value
				print(db)
			else:
				if key_hash in finger_table.keys():
					insert(finger_table[key_hash], key, value)
				else:
					# encontrar o predecessor mais perto da chave
					closest_pred = find_closest_pred(key_hash, finger_table, n)
					insert(closest_pred, key, value)
			
		elif req[0] == 'busca':
			client = req[1]
			key = req[2]
			
			key_hash = get_hash(key, n)
			
			if key_hash == node_id:
				retsock = socket.socket()
				retsock.connect((HOST, int(client)))
				
				msg = str.encode('{} -> {} no nó {}'.format(key, db[key], node_id));
				send(retsock, msg)
				
				retsock.close()
						
			else:
				if key_hash in finger_table.keys():
					find(finger_table[key_hash], client, key)
				else:
					# encontrar o predecessor mais perto da chave
					closest_pred = find_closest_pred(key_hash, finger_table, n)
					find(closest_pred, client, key)
			
		
def node_execution(n, node_id, port, finger_table):
	sock = initialize_node(port)
	
	db[node_id] = port
	
	print('\tNo {} iniciou na porta {}'.format(node_id, port))
	
	while True:
		#espera por solicitacao de conexao
		read, write, exception = select.select([sock], [], [])
		
		for req in read:
			if req == sock:  #pedido novo de conexao
				clisock, endr = sock.accept()
				
				#cria nova thread para atender o cliente
				client = Thread(target=attend_request, args=(clisock, endr, n, node_id, port, finger_table))
				client.start()
	

def main():

	nodes = {}

	print('Inicializando simulação do protocolo Chord')
	print('Digite o valor de n para o tamanho do anel (2^n): ', end='')
	n = int(input());
	
	
	# inicializacao dos nós
	for i in range(2**n):
		port = START_PORT + i
		
		finger_table = {}
		# calculo dos elementos da tabela e sua porta = offset + numero do proprio nó
		for j in range(n):
			s = (i + 2**(j)) % 2**n
			finger_table[s] = START_PORT + s
			
		node = Process(target=node_execution, args=(n, i, port, finger_table))
		nodes[i] = (HOST, port)
		node.start()
	
	while True:
		# espera por solicitacao de conexao
		read, write, exception = select.select([sys.stdin], [], [])
		
		for req in read:
			if req == sys.stdin: # entrada padrao
				cmd = input()
				if cmd == '': # ignorar comandos vazios
					continue
				elif cmd =='nodes':
					print(nodes)
	

main()

