import socket  # Importa o módulo de socket para comunicação de rede
import json  # Importa o módulo json para trabalhar com dados JSON
import threading  # Importa o módulo threading para lidar com várias conexões simultâneas
import os  # Importa o módulo os para operações do sistema operacional
from tkinter import *  # Importa o módulo tkinter para construção da interface gráfica
from tkinter import filedialog, messagebox  # Importa classes específicas do tkinter

# Função para enviar uma mensagem ao servidor
def enviar_mensagem():
    # Obtém os dados dos campos de entrada na interface gráfica
    nome_remetente = entrada_nome.get()
    depto_remetente = entrada_depto.get()
    nome_destinatario = entrada_nome_destinatario.get()
    depto_destinatario = entrada_depto_destinatario.get()
    mensagem = texto_mensagem.get("1.0", END)  # Obtém a mensagem do campo de texto
    
    # Cria um dicionário com os dados da mensagem
    dados = {
        "tipo": "mensagem",
        "nome_remetente": nome_remetente,
        "depto_remetente": depto_remetente,
        "nome_destinatario": nome_destinatario,
        "depto_destinatario": depto_destinatario,
        "mensagem": mensagem
    }
    
    try:
        cliente_socket.send(json.dumps(dados).encode())  # Envia os dados ao servidor
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao enviar mensagem: {e}")  # Exibe uma mensagem de erro em caso de falha

# Função para receber mensagens do servidor
def receber_mensagens():
    while True:
        try:
            mensagem = cliente_socket.recv(1024).decode()  # Recebe uma mensagem do servidor
            if mensagem:
                dados = json.loads(mensagem)  # Converte a mensagem de JSON para um dicionário Python
                # Exibe uma mensagem ou realiza ação com base no tipo de mensagem recebida
                if dados['tipo'] == 'mensagem':
                    messagebox.showinfo("Nova Mensagem", dados['mensagem'])  # Exibe uma nova mensagem em uma janela de diálogo
                elif dados['tipo'] == 'arquivo':
                    # Exibe uma janela de confirmação para baixar o arquivo
                    nome_arquivo = dados['nome_arquivo']
                    if messagebox.askyesno("Arquivo Recebido", f"Você recebeu o arquivo '{nome_arquivo}'. Deseja baixá-lo?"):
                        conteudo_arquivo = cliente_socket.recv(1024*1024)  # Recebe o conteúdo do arquivo
                        salvar_arquivo(nome_arquivo, conteudo_arquivo)  # Chama a função para salvar o arquivo
                elif dados['tipo'] == 'erro':
                    messagebox.showerror("Erro", dados['mensagem'])  # Exibe uma mensagem de erro em uma janela de diálogo
        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
            cliente_socket.close()  # Fecha a conexão com o servidor em caso de erro
            break

# Função para conectar ao servidor
def conectar_ao_servidor():
    global cliente_socket  # Define a variável cliente_socket como global para ser acessível em outras funções
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP/IP
    try:
        cliente_socket.connect(("127.0.0.1", 9999))  # Conecta ao servidor na porta especificada
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao conectar ao servidor: {e}")  # Exibe uma mensagem de erro em caso de falha
        return
    
    # Realiza a autenticação do cliente enviando o nome e senha ao servidor
    nome = auth_nome.get()
    senha = auth_senha.get()
    dados_autenticacao = {
        "nome": nome,
        "senha": senha
    }
    cliente_socket.send(json.dumps(dados_autenticacao).encode())  # Envia os dados de autenticação ao servidor
    
    resposta = cliente_socket.recv(1024).decode()  # Recebe a resposta do servidor
    if resposta == "Autenticado com sucesso!":
        threading.Thread(target=receber_mensagens).start()  # Inicia uma nova thread para receber mensagens do servidor
        messagebox.showinfo("Sucesso", resposta)  # Exibe uma mensagem de sucesso em uma janela de diálogo
        janela_autenticacao.destroy()  # Fecha a janela de autenticação
        root.deiconify()  # Exibe a janela principal do programa
    else:
        messagebox.showerror("Erro", resposta)  # Exibe uma mensagem de erro em uma janela de diálogo
        cliente_socket.close()  # Fecha a conexão com o servidor em caso de falha na autenticação

# Função para selecionar um arquivo
def selecionar_arquivo():
    caminho_arquivo = filedialog.askopenfilename()  # Abre uma janela para selecionar um arquivo
    entrada_caminho_arquivo.config(state=NORMAL)  # Habilita a entrada de texto
    entrada_caminho_arquivo.delete(0, END)  # Limpa o conteúdo da entrada de texto
    entrada_caminho_arquivo.insert(0, caminho_arquivo)  # Insere o caminho do arquivo na entrada de texto
    entrada_caminho_arquivo.config(state=DISABLED)  # Desabilita a entrada de texto

# Função para enviar um arquivo ao servidor
def enviar_arquivo():
    caminho_arquivo = entrada_caminho_arquivo.get()  # Obtém o caminho do arquivo da entrada de texto
    if not caminho_arquivo:
        messagebox.showwarning("Aviso", "Selecione um arquivo primeiro.")  # Exibe uma mensagem de aviso se nenhum arquivo foi selecionado
        return
    
    nome_remetente = entrada_nome.get()  # Obtém o nome do remetente
    depto_remetente = entrada_depto.get()  # Obtém o departamento do remetente
    nome_destinatario = entrada_nome_destinatario.get()  # Obtém o nome do destinatário
    depto_destinatario = entrada_depto_destinatario.get()  # Obtém o departamento do destinatário
    nome_arquivo = os.path.basename(caminho_arquivo)  # Obtém o nome do arquivo
    
    with open(caminho_arquivo, 'rb') as f:
        conteudo_arquivo = f.read()  # Lê o conteúdo do arquivo em modo binário
    
    # Cria um dicionário com os dados do arquivo
    dados = {
        "tipo": "arquivo",
        "nome_remetente": nome_remetente,
        "depto_remetente": depto_remetente,
        "nome_destinatario": nome_destinatario,
        "depto_destinatario": depto_destinatario,
        "nome_arquivo": nome_arquivo
    }
    
    try:
        cliente_socket.send(json.dumps(dados).encode())  # Envia os dados do arquivo ao servidor
        cliente_socket.send(conteudo_arquivo)  # Envia o conteúdo do arquivo ao servidor
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao enviar arquivo: {e}")  # Exibe uma mensagem de erro em caso de falha

# Função para salvar um arquivo recebido
def salvar_arquivo(nome_arquivo, conteudo_arquivo):
    caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)  # Obtém o caminho completo do arquivo
    with open(caminho_arquivo, "wb") as f:
        f.write(conteudo_arquivo)  # Escreve o conteúdo do arquivo no disco em modo binário
    messagebox.showinfo("Arquivo Recebido", f"Arquivo {nome_arquivo} recebido e salvo na pasta do servidor.")  # Exibe uma mensagem de sucesso em uma janela de diálogo

# Função para criar a janela de autenticação
def janela_autenticacao():
    global auth_nome, auth_senha, janela_autenticacao
    janela_autenticacao = Toplevel(root)  # Cria uma nova janela
    janela_autenticacao.title("Autenticação")  # Define o título da janela
    
    # Adiciona campos de entrada para o nome e senha
    Label(janela_autenticacao, text="Nome:").grid(row=0, column=0)
    auth_nome = Entry(janela_autenticacao)
    auth_nome.grid(row=0, column=1)
    
    Label(janela_autenticacao, text="Senha:").grid(row=1, column=0)
    auth_senha = Entry(janela_autenticacao, show="*")
    auth_senha.grid(row=1, column=1)
    
    # Adiciona um botão para conectar ao servidor
    Button(janela_autenticacao, text="Conectar", command=conectar_ao_servidor).grid(row=2, columnspan=2)

# Cria a janela principal do programa
root = Tk()
root.withdraw()  # Oculta a janela principal temporariamente
janela_autenticacao()  # Chama a função para exibir a janela de autenticação

# Define o título da janela principal
root.title("Sistema de Comunicação Corporativa")

# Adiciona campos de entrada para o nome, setor e destinatário
Label(root, text="Seu Nome:").grid(row=0, column=0)
entrada_nome = Entry(root)
entrada_nome.grid(row=0, column=1)

Label(root, text="Seu Setor:").grid(row=1, column=0)
entrada_depto = Entry(root)
entrada_depto.grid(row=1, column=1)

Label(root, text="Nome do Destinatário:").grid(row=2, column=0)
entrada_nome_destinatario = Entry(root)
entrada_nome_destinatario.grid(row=2, column=1)

Label(root, text="Setor do Destinatário:").grid(row=3, column=0)
entrada_depto_destinatario = Entry(root)
entrada_depto_destinatario.grid(row=3, column=1)

# Adiciona um campo de texto para a mensagem
Label(root, text="Mensagem:").grid(row=4, column=0)
texto_mensagem = Text(root, height=10, width=30)
texto_mensagem.grid(row=4, column=1)

# Adiciona um botão para enviar a mensagem
Button(root, text="Enviar Mensagem", command=enviar_mensagem).grid(row=6, column=1)

# Adiciona um campo de entrada para o arquivo e botões para selecionar e enviar o arquivo
Label(root, text="Arquivo:").grid(row=7, column=0)
entrada_caminho_arquivo = Entry(root, state=DISABLED, width=30)
entrada_caminho_arquivo.grid(row=7, column=1)

Button(root, text="Selecionar Arquivo", command=selecionar_arquivo).grid(row=8, column=0)
Button(root, text="Enviar Arquivo", command=enviar_arquivo).grid(row=8, column=1)

root.mainloop()  # Inicia o loop principal da interface gráfica
