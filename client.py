import os
import sys
import helpers
from typing import Dict
from threading import Thread
from dataclasses import dataclass
from socket import socket, AF_INET, SOCK_STREAM

@dataclass
class Client:
    def __init__(self, ip: str, port: int, path: str) -> None:
        self._ip = ip
        self._port = port
        self._path = path
        self._server_ip = '127.0.0.1'
        self._server_port = 1099
        # criação do socket para atender requisições de download e bind com ip:porta parametrizado
        self._download_socket = socket(AF_INET, SOCK_STREAM)
        self._download_socket.bind((self.ip, self.port))
        self._download_socket.listen(5)

    # region getters
    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port
    
    @property
    def path(self) -> str:
        return self._path
    
    @property
    def server_ip(self) -> str:
        return self._server_ip
    
    @property
    def server_port(self) -> int:
        return self._server_port
    
    @property
    def download_socket(self) -> socket:
        return self._download_socket
    # endregion

    # region funções de comunicação com o servidor
    # envia um comando sem esperar pela resposta
    def send_and_forget(self, socket: socket, request_cmd: str) -> None:
        cmd_str = helpers.json_serialize(request_cmd)
        socket.sendall(cmd_str.encode())
    # envia um comando e aguarda a resposta
    def send_request(self, socket: socket, request_cmd: Dict) -> str:
        self.send_and_forget(socket, request_cmd)
        response = helpers.socket_receive_all(socket)
        return response
    # envia a solicitação de download e caso permitida faz o download na pasta do client
    def request_download(self, socket: socket, download_cmd: Dict) -> bool:
        # envia requisição de download
        cmd_str = helpers.json_serialize(download_cmd)
        socket.sendall(cmd_str.encode())
        # aguarda confirmação com propriedades do arquivo (se existe, etc)
        file_prop_cmd = helpers.json_deserialize(helpers.socket_receive_all(socket))
        file_name, file_size = file_prop_cmd['name'], file_prop_cmd['size']
        if file_size <= 0:
            return { 'success': False, 'message': f'{file_name} não existe.\n' }
        
        # faz o download do arquivo
        download_status = helpers.download_file(self.path, file_name, file_size, socket)
        return download_status

    def open_server_connection(self) -> socket:
        try:
            sk = socket(AF_INET, SOCK_STREAM)
            sk.connect((self.server_ip, self.server_port))
            return sk
        except ConnectionRefusedError:
            print('Servidor não aceitou a conexão')
    
    def open_peer_connection(self, peer_ip: str, peer_port: int) -> socket:
        try:
            sk = socket(AF_INET, SOCK_STREAM)
            sk.connect((peer_ip, peer_port))
            return sk
        except ConnectionRefusedError:
            print(f'Peer {peer_ip}:{peer_port} não aceitou a conexão')

    def close_server_connection(self, socket: socket) -> None:
        if socket is not None:
            socket.close()
    # endregion

    # region features
    def join(self) -> None:
        # abre-se uma conexão com o servidor
        conn = self.open_server_connection()
        try:
            if conn is not None:
                # solicita a factory a criação de um join command
                request_cmd = self.join_command_factory(helpers.list_path_files(self.path), self.port)
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = helpers.json_deserialize(self.send_request(conn, request_cmd))
                # processa o comando de resposta
                self.join_ok_command_handler(response_cmd)
        finally:
            self.close_server_connection(conn)

    def search(self, file_name: str) -> None:
        # abre-se uma conexão com o servidor
        conn = self.open_server_connection()
        try:
            if conn is not None:
                # solicita a factory a criação de um search command
                request_cmd = self.search_command_factory(file_name)
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = helpers.json_deserialize(self.send_request(conn, request_cmd))
                self.search_result_command_handler(response_cmd)
        finally:
            self.close_server_connection(conn)

    def download(self, file_name: str, ip: str, port: int) -> None:
        # abre-se uma conexão com o peer ip:port
        conn = self.open_peer_connection(ip, int(port))
        try:
            if conn is not None:
                # solicita a factory a criação de um download command
                request_cmd = self.download_command_factory(file_name)
                # envia o command para o server e faz o download do arquivo
                download_status = self.request_download(conn, request_cmd)
                if not download_status['success']:
                    raise Exception(download_status['message'])
                else:
                    print(f'Arquivo {file_name} baixado com sucesso na pasta {self.path}\n')
        finally:
            self.close_server_connection(conn)
    
    def update(self, file_name: str) -> None:
        # abre-se uma conexão com o servidor
        conn = self.open_server_connection()
        try:
            if conn is not None:
                # solicita a factory a criação de um update command
                request_cmd = self.update_command_factory(file_name, self.port)
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = helpers.json_deserialize(self.send_request(conn, request_cmd))
                self.update_ok_command_handler(response_cmd)
        finally:
            self.close_server_connection(conn)
    # endregion

    # region factories
    def join_command_factory(self, files, client_port: int) -> Dict:
        return { 'name': 'JOIN', 'files': files, 'client_port': client_port }

    def search_command_factory(self, file_name: str) -> Dict:
        return { 'name': 'SEARCH', 'file_name': file_name }
    
    def download_command_factory(self, file_name: str) -> Dict:
        return { 'name': 'DOWNLOAD', 'file_name': file_name }

    def download_ok_command_factory(self, file_name: str) -> Dict:
        return { 'name': 'DOWNLOAD_OK', 'file_name': file_name }
    
    def update_command_factory(self, file_name: str, client_port: int):
        return { 'name': 'UPDATE', 'file_name': file_name, 'client_port': client_port }
    
    def file_properties_command_factory(self, file_name: str, file_size: int):
        return { 'name': 'FILE', 'name': file_name, 'size': file_size }
    # endregion
    
    # region command handlers
    # handler responsavel por tratar confirmações de join
    def join_ok_command_handler(self, join_ok_cmd: Dict) -> None:
        files, sender_address = join_ok_cmd['files'], join_ok_cmd['sender_address']
        print(f'Sou peer {sender_address} com arquivos {", ".join(files)}')

    # handler responsavel por tratar resultados de buscas
    def search_result_command_handler(self, search_result_cmd: Dict) -> None:
        results = search_result_cmd['results']
        print(f'peers com arquivo solicitado: {", ".join(results)}')

    # handler responsavel por tratar solicitações de download
    def download_command_handler(self, download_cmd: Dict) -> str:
        return download_cmd['file_name']
    
    # handler responsavel por tratar confirmações de download
    def download_ok_command_hander(self, download_ok: Dict) -> None:
        print('Arquivo [só nome do arquivo] baixado com sucesso na pasta [nome da pasta]')

    # handler responsavel por tratar confirmações de update
    def update_ok_command_handler(self, update_ok_cmd: Dict) -> None:
        print('Registro atualizado com sucesso')
        
    # endregion

    def listen_download_requests(self) -> None:
        while True:
            # aguardo um outro peer se conectar
            peer_socket, peer_address = self.download_socket.accept()
            # despacho para um thread tratar sua requisição
            handler_thread = self.DownloadRequestHandlerThread(self, peer_socket, f'{peer_address[0]}:{peer_address[1]}')
            handler_thread.start()
    
    def run_iteractive_menu(self) -> None:
        handler_thread = self.IteractiveMenuThread(self)
        handler_thread.start()


    # classe aninhada para executar o menu iterativo
    class IteractiveMenuThread(Thread):
        def __init__(self, client) -> None:
            Thread.__init__(self)
            self._client = client

        # region getters
        @property
        def client(self):
            return self._client
        
        # endregion

        # override na função run da thread para execução do menu iterativo
        def run(self):
            print('Napster P2P -- Digite HELP caso precise de ajuda.')
            while True:
                try:
                    cli_input = input('\n>>> ').split(' ')
                    main_cmd = cli_input[0].upper()
                    args = cli_input[1:]

                    if main_cmd == 'JOIN':
                        self.client.join()
                    elif main_cmd == 'SEARCH':
                        if len(args) < 1:
                            raise Exception('SEARCH espera pelo parâmetro `nome_arquivo`.\n')
                        self.client.search(file_name=args[0])
                    elif main_cmd == 'DOWNLOAD':
                        if len(args) < 3:
                            raise Exception('DOWNLOAD espera pelos parâmetros `nome_arquivo`, `ip` e `porta`.\n')

                        file_name, ip, port = args[0], args[1], args[2]
                        if not port.isdigit():
                            raise Exception('A porta especificada deve ser um valor inteiro válido.\n')

                        self.client.download(file_name, ip, int(port))
                    elif main_cmd == 'UPDATE':
                        if len(args) < 1:
                            raise Exception('UPDATE espera pelo parâmetro `nome_arquivo`.\n')
                        self.client.update(file_name=args[0])
                    elif main_cmd == 'HELP':
                        print('Os comandos disponíveis são:\n')
                        print('JOIN: Indica ao servidor o desejo de se juntar a rede.\n')
                        print('SEARCH nome_arquivo: Busca pelos peers que contém o arquivo `nome_arquivo`.\n')
                        print('DOWNLOAD nome_arquivo ip porta: Solicita ao peer no endereço ip:porta pelo arquivo `nome_arquivo`.\n')
                        print('UPDATE nome_arquivo: Envia ao servidor uma solicitação de alteração no registro para incluir `nome_arquivo`.\n')
                    else:
                        pass
                        
                except (KeyboardInterrupt, EOFError):
                    print('\nSaindo...')
                    break
                except Exception as e:
                    print('Erro:', e)
                    print('\n')
                    pass
            os._exit(os.EX_OK) 
    
    # classe aninhada para tratar as solicitações de download despachadas
    class DownloadRequestHandlerThread(Thread):
        def __init__(self, client, peer_socket: socket, peer_address: str) -> None:
            Thread.__init__(self)
            self._client = client
            self._peer_socket = peer_socket
            self._peer_address = peer_address

        # region getters
        @property
        def client(self):
            return self._client
        
        @property
        def peer_socket(self):
            return self._peer_socket
        
        @property
        def peer_address(self):
            return self._peer_address
        # endregion

        def run(self):
            try:
                # aguardo o recebimento do download command
                download_cmd = helpers.json_deserialize(helpers.socket_receive_all(self.peer_socket))
                # obtenho o nome do arquivo a partir do comando recebido
                file_name = self.client.download_command_handler(download_cmd)
                file_path = f'{self.client.path}/{file_name}'
                if os.path.isfile(file_path):
                    # se o arquivo solicitado existir, envio para o requisitante suas informações (nome, tamanho)
                    file_size = int(os.path.getsize(file_path))
                    self.client.send_and_forget(self.peer_socket, self.client.file_properties_command_factory(file_name, file_size))
                    print(f'Enviando o arquivo {file_name} para {self.peer_address}...\n')
                    # faço o upload do arquivo solicitado
                    self.upload_file(file_name)
                else:
                    self.client.send_and_forget(self.peer_socket, self.client.file_properties_command_factory(file_name, file_size=0))
                
                # encerro a conexão com o peer requisitante
                self.peer_socket.close()
            except Exception as e:
                print(e)

        def upload_file(self, file_name):
            # abro o arquivo com permissão de leitura e para cada linha do arquivo envio um pacote via TCP
            with open(f'{self.client.path}/{file_name}', 'rb') as file:
                for line in file.readlines():
                    self.peer_socket.sendall(line)

def main():
    try:
        ip = input('Seu IP (default 127.0.0.1): ') or '127.0.0.1'
        port = int(input('Sua porta: ') or '0')    
        path = input('Seu diretório: ')
        if port <= 0:
            raise ValueError('Porta não especificada')
        if not os.path.isdir(path):
            raise ValueError(f'`{path}` não é um diretorio valido')

        # instancio o client
        client = Client(ip, port, path)
        # coloco a command line interface do client para rodar
        client.run_iteractive_menu()
        # coloco o client para se tornar disponivel para responder requisições de download
        client.listen_download_requests()
    except ValueError as error:
        print(error)

if __name__ == '__main__':
    main()
