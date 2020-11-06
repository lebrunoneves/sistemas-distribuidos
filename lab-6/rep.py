import sys
import socket
import struct
from select import select
from threading import Thread, Lock

HOST = 'localhost'
PORT = 5000 # offset da porta

lock = Lock() 

inputs = [sys.stdin]

help_list = {
	'read' : 'Faz a leitura do valor atual de x',
	'write <value>': 'Atualiza o valor de x',
	'hist': 'Exibe o histórico de atualizações de x',
	'exit': 'Desliga a réplica'
}

hist = [] # historico de mudancas de valor

x = 0

is_primary = False # booleano para verificar se é a replica primaria

new_value = None # houve mudanca na variavel x

my_id = 0 # id da replica

def help():
	menu = '\n'
	menu += '{:^20} {:^40}\n'.format('COMANDO', 'DESCRICAO')
	
	for k, v in help_list.items():
		menu += '{:20} {:40}\n'.format(k, v)
	
	return menu
	
	
def print_hist():
	
	if not hist:
		print('\tvazio')
	else:	
		for (replica, value) in hist:
			print('\tid {} => {}'.format(replica, value))
	

def initialize_replica(id):
	# cria o socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Internet( IPv4 + TCP) 

	# vincula a localizacao do servidor
	sock.bind((HOST, PORT+id))

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

	
def broadcast_get_primary(my_id):
	for i in [1, 2, 3, 4]:
		if i != my_id:
			# estabelece conexao com replica
			sock = socket.socket()
			sock.connect((HOST, PORT + i))
			
			msg = str.encode('get primary {}'.format(my_id));
			send(sock, msg)
			
			sock.close()
			
def broadcast_new_value(new_value, my_id):
	for i in [1, 2, 3, 4]:
		if i != my_id:
			# estabelece conexao com replica
			sock = socket.socket()
			sock.connect((HOST, PORT + i))
			
			msg = str.encode('att {} {}'.format(new_value, my_id))
			send(sock, msg)
			
			sock.close()			
			

def attend_request(clisock, endr):

	global is_primary, my_id, x, new_value

	while True:
		#recebe a requisicao em bytes
		req = recv(clisock)
		
		if not req: # dados vazios: cliente encerrou
			clisock.close() # encerra a conexao com o cliente
			return
			
		req = str(req, encoding='utf-8')
		
		if req.startswith('get primary'):
			with lock:
				if is_primary:
					if new_value: # precisa atualizar demais replicas antes de liberar
						broadcast_new_value(new_value, my_id)
						new_value = None
					else: # bastar passar a copia primaria
						response_id = int(req.split()[2])
						response = socket.socket()
						response.connect((HOST, PORT + response_id))
						
						msg = str.encode('ok primary')
						send(response, msg)
					
					is_primary = False
	
				
		elif req.startswith('att'):
			with lock:
				new_x = req.split()[1]
				from_id = req.split()[2]
				
				hist.append((int(from_id), int(new_x)))
				x = new_x
		

# ========================  MAIN =========================== #

print('ID da réplica: ', end='')

my_id = int(input())

if my_id == 1:
	is_primary = True
	print(help())

sock = initialize_replica(my_id)

while True:
	threads = []
	try:
		read, write, exception = select(inputs, [], [])
		
		for req in read:
			if req == sys.stdin: #entrada padrao
				cmd = input()
				if cmd == '': #ignorar comandos vazios
					continue
				if cmd == 'exit':
					raise SystemExit()		
				elif cmd == 'read':
					print('\tx = {}'.format(x))
				elif cmd == 'hist':
					print_hist()
				elif cmd.startswith('write'):
					new_value = cmd.split()[1]
					
					while not is_primary:
						broadcast_get_primary(my_id)
						
						try:
							# recebe a mensagem da copia primaria atual 'passando o chapeu'
							sock.setblocking(True)
							primary_sock, endr = sock.accept()
							primary_msg = str(recv(primary_sock), encoding='utf-8')
							sock.setblocking(False)
							
							with lock:
								# se a copia prima alterou o valor de x
								if primary_msg.startswith('att'):
									new_x = primary_msg.split()[1]
									from_id = primary_msg.split()[2]
									
									hist.append((int(from_id), int(new_x)))
									x = new_x
								
								is_primary = True
						except:
							continue
					
					with lock:
						hist.append((my_id, int(new_value)))
						x = new_value
						print('\tx = {}'.format(x))
				else:
					print('\t comando inválido :(')
			elif req == sock: #pedido de conexao
				newsock, endr = sock.accept()
				
				client = Thread(target=attend_request, args=(newsock, endr))
				threads.append(client)
				client.start()
				
	except IndexError:
		print('\tErro no comando')
	except ConnectionRefusedError:
		print('\tRéplica desativada ou inexistente')	
	except (KeyboardInterrupt, SystemExit, EOFError):
		for t in threads:
			t.join()
		print('\n\tTerminou')		
		sys.exit()	
			
			
			
			
			
			
