# Napster P2P 🎵📡

## 💡 Sobre o Projeto

Olá, seja bem-vindo ao projeto Napster P2P! Esse é um trabalho desenvolvido para a disciplina de sistemas distribuídos do curso de Ciência da Computação na UFABC. Aqui, iremos recriar o espírito do famoso Napster, um dos primeiros sistemas peer-to-peer (P2P) criado por Shawn Fanning quando ele tinha apenas 18 anos.

O objetivo desse projeto é construir um sistema P2P que permita a transferência de arquivos de vídeo gigantes (mais de 1 GB) entre os peers, usando o TCP como protocolo de comunicação. Vamos criar uma rede de compartilhamento de arquivos, onde os peers poderão enviar e receber arquivos de outros peers, intermediados por um servidor centralizado.

### 📽️ Demonstração (clique para ver o vídeo) 

[![Veja o vídeo de demonstração](https://img.youtube.com/vi/oNyjzk0ND20/maxresdefault.jpg)](https://youtu.be/oNyjzk0ND20)

## 📋 Funcionalidades

O Napster P2P possui as seguintes funcionalidades:

### Servidor Centralizado 🖥️

- Receber e responder requisições dos peers.
- Requisição JOIN: quando um peer deseja entrar na rede, ele envia uma requisição ao servidor informando suas informações, como os nomes dos arquivos que possui. O servidor armazena essas informações para consultas futuras e responde com a mensagem "JOIN_OK".
- Requisição SEARCH: quando um peer procura por um arquivo, ele envia uma requisição ao servidor com o nome do arquivo desejado. O servidor responde com uma lista de peers que possuem o arquivo.
- Requisição UPDATE: quando um peer baixa um arquivo, ele envia uma requisição ao servidor informando o nome do arquivo baixado. O servidor atualiza suas informações e responde com a mensagem "UPDATE_OK".
- Inicialização do servidor: o servidor captura inicialmente o IP e a porta do registry. O IP utilizado é 127.0.0.1 se estiver executando o projeto na mesma máquina. A porta default para conexão dos peers é 1099.

### Peer 🧑‍🤝‍🧑

- Receber e responder requisições do servidor e de outros peers.
- Enviar uma requisição de JOIN ao servidor e aguardar a resposta "JOIN_OK".
- Enviar uma requisição de UPDATE ao servidor após baixar um arquivo e aguardar a resposta "UPDATE_OK".
- Enviar uma requisição de SEARCH ao servidor para procurar por um arquivo. O servidor responde com uma lista de peers que possuem o arquivo.
- Enviar uma requisição de DOWNLOAD a outro peer para baixar um arquivo.
- Receber requisições de DOWNLOAD de outros peers e enviar o arquivo solicitado, se possuir.
- Armazenar os arquivos baixados em uma pasta específica do peer.

## 🚀 Como Executar o Projeto

1. Clone o repositório em sua máquina local.
2. Certifique-se de ter o Python 3.8 (ou superior) instalado em seu sistema.
3. Execute a partir da raiz do projeto o comando `python -m pip install -r requirements.txt`
4. Execute o servidor executando o arquivo `server.py`.
5. Execute os peers executando o arquivo `client.py`.
6. Siga as instruções apresentadas na console para realizar ações como JOIN, SEARCH, DOWNLOAD e UPDATE.

## 📜 Licença

Este projeto está sob a licença MIT. Para mais informações, consulte o arquivo `LICENSE`.
