import socket
import select
import sys
import multiprocessing
import server_process

HOST = ''
PORT = 5003

# lista de I/O sendo ouvidos
inputs = [sys.stdin]

# historico de clientes
connections = {}

def initializeServer():
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

	# registra a nova conexao
	connections[clisock] = endr 

	return clisock, endr

def attendRequest(clisock, endr):

	while True:
		#recebe o nome do arquivo em bytes
		filename_bytes = clisock.recv(1024)

		if not filename_bytes: # dados vazios: cliente encerrou
			print(str(endr) + '-> encerrou')
			clisock.close() # encerra a conexao com o cliente
			return 

		print(str(endr) + ': ' + str(filename_bytes, encoding='utf-8'))

		# converte o nome do arquivo para string
		filename = str(filename_bytes, encoding='utf-8')

		word_counter = server_process.get(filename)

		if word_counter:
			clisock.send(str.encode(str(word_counter)))
		else:
			clisock.send(str.encode('null'))

def main():
	clients=[] #armazena os processos criados para fazer join
	sock = initializeServer()
	print("Pronto para receber conexoes...")
	while True:
		#espera por qualquer entrada de interesse
		read, write, exception = select.select(inputs, [], [])
		#tratar todas as entradas prontas
		for req in read:
			if req == sock:  #pedido novo de conexao
				clisock, endr = connect(sock)
				print ('Conectado com: ', endr)
				#cria novo processo para atender o cliente
				client = multiprocessing.Process(target=attendRequest, args=(clisock,endr))
				client.start()
				clients.append(client) #armazena a referencia do processo para usar com join()
			elif req == sys.stdin: #entrada padrao
				cmd = input()
				if cmd == 'exit': #solicitacao de finalizacao do servidor
					for c in clients: #aguarda todos os processos terminarem
						c.join()
					sock.close()
					sys.exit()
				elif cmd == 'hist': #historico de clientes conectados
					print(str(connections.items()))
				else:
					print('Comando inválido :(')


main()