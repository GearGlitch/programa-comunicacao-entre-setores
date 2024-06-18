import socket
import threading
import json
import os

# Funções auxiliares para manipulação do banco de dados
def carregar_usuarios():
    try:
        with open("usuarios.json", "r") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return {}

def salvar_usuarios(usuarios):
    with open("usuarios.json", "w") as arquivo:
        json.dump(usuarios, arquivo, indent=4)

usuarios_db = carregar_usuarios()
clientes_conectados = {}

def tratar_cliente(cliente_socket):
    try:
        # Autenticação do cliente
        autenticacao = cliente_socket.recv(1024).decode()
        dados_autenticacao = json.loads(autenticacao)
        nome = dados_autenticacao['nome']
        senha = dados_autenticacao['senha']
        
        if nome in usuarios_db and usuarios_db[nome]['senha'] == senha:
            cliente_socket.send("Autenticado com sucesso!".encode())
            clientes_conectados[nome] = cliente_socket
        else:
            cliente_socket.send("Falha na autenticação.".encode())
            cliente_socket.close()
            return
        
        while True:
            dados = cliente_socket.recv(1024).decode()
            if not dados:
                break
            dados = json.loads(dados)
            
            if dados['tipo'] == 'mensagem':
                nome_remetente = dados['nome_remetente']
                depto_remetente = dados['depto_remetente']
                nome_destinatario = dados['nome_destinatario']
                depto_destinatario = dados['depto_destinatario']
                msg = dados['mensagem']
                
                if nome_destinatario in usuarios_db and usuarios_db[nome_destinatario]['setor'] == depto_destinatario:
                    if nome_destinatario in clientes_conectados:
                        mensagem_encaminhada = f"De {nome_remetente} ({depto_remetente}): {msg}"
                        clientes_conectados[nome_destinatario].send(json.dumps({'tipo': 'mensagem', 'mensagem': mensagem_encaminhada}).encode())
                    else:
                        cliente_socket.send(json.dumps({'tipo': 'erro', 'mensagem': 'Usuário está no banco de dados, mas não está conectado.'}).encode())
                else:
                    cliente_socket.send(json.dumps({'tipo': 'erro', 'mensagem': 'Usuário não encontrado.'}).encode())
            
            elif dados['tipo'] == 'arquivo':
                nome_arquivo = dados['nome_arquivo']
                nome_destinatario = dados['nome_destinatario']
                
                conteudo_arquivo = cliente_socket.recv(1024*1024)
                
                if nome_destinatario in clientes_conectados:
                    mensagem_notificacao = f"Você recebeu um arquivo de {dados['nome_remetente']} ({dados['depto_remetente']}): {nome_arquivo}"
                    clientes_conectados[nome_destinatario].send(json.dumps({'tipo': 'mensagem', 'mensagem': mensagem_notificacao}).encode())
                    caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
                    with open(caminho_arquivo, 'wb') as f:
                        f.write(conteudo_arquivo)
                    clientes_conectados[nome_destinatario].send(json.dumps({'tipo': 'arquivo', 'nome_arquivo': caminho_arquivo}).encode())
                else:
                    cliente_socket.send(json.dumps({'tipo': 'erro', 'mensagem': 'Usuário está no banco de dados, mas não está conectado.'}).encode())
    except Exception as e:
        print(f"Erro ao tratar cliente: {e}")
    finally:
        if nome in clientes_conectados:
            del clientes_conectados[nome]
        cliente_socket.close()

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", 9999))
    servidor.listen(5)
    print("Servidor ouvindo na porta 9999")
    
    while True:
        cliente_socket, endereco = servidor.accept()
        print(f"Conexão aceita de {endereco}")
        
        thread_cliente = threading.Thread(target=tratar_cliente, args=(cliente_socket,))
        thread_cliente.start()

iniciar_servidor()
