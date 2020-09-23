import socket
import select
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
	
	
def get_online(my_username):
	users = list(sessions.keys())
	
	if my_username: #remove o proprio usuario da lista de usuarios online para evitar redundancia
		users.remove(my_username)
	
	if not users:
		return 'Não há usuários online :('
	
	users_str = '\n{:^20} ({}):\n'.format('Usuários online', len(users))
	
	for user in users:
		users_str += '- {:<30}\n'.format(user)
		
	return users_str
	

def now():
	return datetime.now().strftime('(%d/%m/%Y - %H:%M)')


def attend_request(clisock, endr):
	username = None

	while True:
		#recebe a requisicao em bytes
		req = clisock.recv(1024)

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
			try:
				if username:
					clisock.send(str.encode(now() + ' --> Já existe uma sessão ativa. Para alterar o usuário, faça logout.'))
				else:	
					username = req.split()[1] # o username passado
					
					if username in sessions:
						clisock.send(str.encode(now() + ' --> O usuário "{}" já existe. Por favor, tente outro nome'.format(username)))
						username = None
					else:
						with lock:
							sessions[username] = clisock
						clisock.send(str.encode(now() + ' --> Login realizado com sucesso.'))
			except:
				clisock.send(str.encode(now() + ' --> Erro no comando.'))
		elif req == 'logout':
			if username and username in sessions:
				with lock:
					del sessions[username]
				username = None
				clisock.send(str.encode(now() + ' --> Logout realizado com sucesso.'))
			else:
				clisock.send(str.encode(now() + ' --> Não há nenhuma sessão ativa.'))
		elif req == 'online':
			clisock.send(str.encode(now() + ' --> ' + get_online(username)))
		elif req.startswith('@'): # envio de mensagem
			if not username:
				clisock.send(str.encode(now() + ' --> Faça login antes de enviar mensagens.'))
			else:
				user_to = req[1:req.index(' ')] # nome do usuario entre '@' e o primeiro espaço
				msg = req[req.index(' ')+1:] # mensagem a partir do primeiro espaço (excludente) ate o fim de req
				
				if not user_to in sessions:
					clisock.send(str.encode(now() + ' --> Usuário offline ou não encontrado.'))
				else:
					clisock.send(str.encode(now() + ' --> mensagem enviada'))
					clisend = sessions[user_to]
					clisend.send(str.encode(now() + ' {} diz: '.format(username) + msg))
		else:
			clisock.send(str.encode(now() + ' --> Comando inválido.'))

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
					sock.close()
					sys.exit()
				if cmd == 'list':
					print(sessions)

				else:
					print('Comando inválido :(')


main()
