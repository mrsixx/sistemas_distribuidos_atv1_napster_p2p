import os
import socket
from threading import Thread
from typing import Dict
from dataclasses import dataclass
import command as cmd
from mysocket import receive_all, download_file
from file import list_files

@dataclass
class Client:
    def __init__(self, ip: str, port: int, path: str) -> None:
        self._ip = ip
        self._port = port
        self._path = path
        self._server_ip = '127.0.0.1'
        self._server_port = 1099
        # criação do socket para atender requisições de download e bind com ip:porta parametrizado
        self._download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    def download_socket(self) -> socket.socket:
        return self._download_socket
    # endregion

    # region funções de comunicação com o servidor
    def send_request(self, socket: socket.socket, request_cmd: Dict) -> str:
        cmd_str = cmd.serialize(request_cmd)
        socket.sendall(cmd_str.encode())
        response = receive_all(socket)
        return response
    
    def request_download(self, socket: socket.socket, download_cmd: Dict) -> None:
        file_name = download_cmd['file_name']
        cmd_str = cmd.serialize(download_cmd)
        socket.sendall(cmd_str.encode())
        download_file(self.path, file_name, socket)

    def open_server_connection(self) -> socket.socket:
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.connect((self.server_ip, self.server_port))
            return sk
        except ConnectionRefusedError:
            print('Servidor não aceitou a conexão')
    
    def open_peer_connection(self, peer_ip: str, peer_port: int) -> socket.socket:
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.connect((peer_ip, peer_port))
            return sk
        except ConnectionRefusedError:
            print(f'Peer {peer_ip}:{peer_port} não aceitou a conexão')

    def close_server_connection(self, socket: socket.socket) -> None:
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
                request_cmd = cmd.join_command(list_files(self.path), self.port)
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = cmd.deserialize(self.send_request(conn, request_cmd))
                # processa o comando de resposta
                cmd.join_ok_command_handler(response_cmd)
        finally:
            self.close_server_connection(conn)

    def search(self) -> None:
        # abre-se uma conexão com o servidor
        conn = self.open_server_connection()
        try:
            if conn is not None:
                # solicita a factory a criação de um search command
                request_cmd = cmd.search_command(input('Nome do arquivo: '))
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = cmd.deserialize(self.send_request(conn, request_cmd))
                cmd.search_result_command_handler(response_cmd)
        finally:
            self.close_server_connection(conn)

    def download(self) -> None:
        #leio a entrada dos parametros
        file_name, ip, port = input('O que deseja baixar? Digite nome_do_arquivo ip porta: ').split(' ')
        # abre-se uma conexão com o peer ip:port
        conn = self.open_peer_connection(ip, int(port))
        try:
            if conn is not None:
                # solicita a factory a criação de um download command
                request_cmd = cmd.download_command(file_name)
                # envia o command para o server e faz o download do arquivo
                self.request_download(conn, request_cmd)
        finally:
            self.close_server_connection(conn)
    
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
            while True:
                try:
                    option = int(input('1 - JOIN | 2 - SEARCH | 3 - DOWNLOAD: '))
                    if option == 1:
                        self.client.join()
                    elif option == 2:
                        self.client.search()
                    elif option == 3:
                        self.client.download()
                    else:
                        print('Opção inexistente.\n')
                except Exception as e:
                    print('\n Erro crítico', e)

    # classe aninhada para tratar as solicitações de download despachadas
    class DownloadRequestHandlerThread(Thread):
        def __init__(self, client, peer_socket: socket.socket, peer_address: str) -> None:
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
                download_cmd = cmd.deserialize(receive_all(self.peer_socket))
                # obtenho o nome do arquivo a partir do comando recebido
                file_name = cmd.download_command_handler(download_cmd)
                #TODO: validar se o arquivo existe
                #TODO: solicitar confirmação
                print(f'Enviando o arquivo {file_name} para {self.peer_address}...\n')
                # faço o upload do arquivo solicitado
                self.upload_file(file_name)
                # encerro a conexão com o peer requisitante
                self.peer_socket.close()
            except Exception as e:
                # TODO: resolver problema com arquivos grandes (1gb) (Terminated)
                print(e)

        def upload_file(self, file_name):
            with open(f'{self.client.path}/{file_name}', 'rb') as file:
                for line in file.readlines():
                    self.peer_socket.sendall(line)

def main():
    try:
        #TODO: validar
        ip = input('IP: ')
        port = int(input('Port: '))    
        #path = input('Path: ')
        path = f'./files/cli{input("Path_dev: ")}'
        if port <= 0:
            raise ValueError('Porta não especificada')
        if not os.path.isdir(path):
            raise ValueError(f'{path} não é um diretorio valido')
        
        client = Client(ip, port, path)
        client.run_iteractive_menu()
        client.listen_download_requests()
    except ValueError as error:
        print(error)
    except KeyboardInterrupt:
        print('\nsaindo...')

if __name__ == '__main__':
    main()
