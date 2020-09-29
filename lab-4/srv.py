import socket
import select
import struct
import sys
from threading import Thread, Lock
from datetime import datetime

HOST = ''
PORT = 5004

# lista de I/O sendo ouvidos
inputs = [sys.stdin]

sessions = {} # usuarios logados no sistema

lock = Lock() # lock necessario para alterar o dicionario de sessoes (zona critica)

def initialize_server():
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


def connect(sock):
	# estabelece conexao com o proximo cliente
	clisock, endr = sock.accept()

	return clisock, endr
	

def send(sock, data):
	length = len(data)
	sock.sendall(struct.pack('!I', length)) # !I = padrão de envio da internet (big-endian) e formato unsigned int
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

	
def get_online(my_username):
	users = list(sessions.keys())
	
	if my_username: #remove o proprio usuario da lista de usuarios online para evitar redundancia
		users.remove(my_username)
	
	if not users:
		return 'Não há usuários online :('
	
	users_str = '\n{:^20} ({}):\n'.format('usuário(s) online', len(users))
	
	for user in users:
		users_str += '- {:<30}\n'.format(user)
		
	return users_str
	

def now():
	return datetime.now().strftime('(%d/%m/%Y - %H:%M)')


def attend_request(clisock, endr):
	username = None

	while True:
		try:
			#recebe a requisicao em bytes
			req = recv(clisock)

			if not req: # dados vazios: cliente encerrou
				print('Encerrou conexao: ', str(endr))
				if username and username in sessions: # tem sessao aberta
					with lock:
						del sessions[username]
					username = None
				clisock.close() # encerra a conexao com o cliente
				return 

			print(str(endr) + ': ' + str(req, encoding='utf-8'))

			# converte a requisicao para string
			req = str(req, encoding='utf-8')

			if req.startswith('login'):
				if username:
					send(clisock, str.encode(now() + ' --> Já existe uma sessão ativa. Para alterar o usuário, faça logout.'))
				else:	
					username = req.split()[1] # o username passado
					
					if username in sessions:
						send(clisock, str.encode(now() + ' --> O usuário "{}" já existe. Por favor, tente outro nome'.format(username)))
						username = None
					else:
						with lock:
							sessions[username] = clisock
						send(clisock, str.encode(now() + ' --> Login realizado com sucesso.'))
			elif req == 'logout':
				if username and username in sessions:
					with lock:
						del sessions[username]
					username = None
					send(clisock, str.encode(now() + ' --> Logout realizado com sucesso.'))
				else:
					send(clisock, str.encode(now() + ' --> Não há nenhuma sessão ativa.'))
			elif req == 'online':
				send(clisock, str.encode(now() + ' --> ' + get_online(username)))
			elif req == 'me':
				if username:
					send(clisock, str.encode(now() + ' --> Usuário conectado: {}'.format(username)))
				else:
					send(clisock, str.encode(now() + ' --> Nenhum usuário logado'))
			elif req.startswith('@'): # envio de mensagem
				if not username:
					send(clisock, str.encode(now() + ' --> Faça login antes de enviar mensagens.'))
				else:
					user_to = req[1:req.index(' ')] # nome do usuario entre '@' e o primeiro espaço
					msg = req[req.index(' ')+1:] # mensagem a partir do primeiro espaço (excludente) ate o fim de req
					
					if not user_to in sessions:
						send(clisock, str.encode(now() + ' --> Usuário offline ou não encontrado.'))
					else:
						send(clisock, str.encode(now() + ' --> mensagem enviada'))
						clisend = sessions[user_to]
						send(clisend, str.encode(now() + ' {} diz: '.format(username) + msg))
			else:
				send(clisock, str.encode(now() + ' --> Comando inválido.'))
		except:
			send(clisock, str.encode(now() + ' --> Erro no comando.'))

def main():
	client_threads = []
	sock = initialize_server()
	print('Servidor de bate-papo inicializado.')
	while True:
		#espera por qualquer entrada de interesse
		read, write, exception = select.select(inputs, [], [])
		#tratar todas as entradas prontas
		for req in read:
			if req == sock:  #pedido novo de conexao
				clisock, endr = connect(sock)
				print ('Nova conexão: ', endr)									
				
				#cria nova thread para atender o cliente
				client = Thread(target=attend_request, args=(clisock,endr))
				client.start()
				client_threads.append(client) #armazena a referencia da thread para usar com join()
			elif req == sys.stdin: #entrada padrao
				cmd = input()
				if cmd == 'exit': #solicitacao de fim do servidor
					print('Finalizando conexoes...')
					for c in client_threads: #aguarda as threads terminarem
						c.join()
					print('Finalizado')
					sock.close()
					sys.exit()
				if cmd == 'list':
					print(sessions)

				else:
					print('Comando inválido :(')


main()
