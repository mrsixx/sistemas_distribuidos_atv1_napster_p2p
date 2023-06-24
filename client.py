import os
import sys
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
    def send_and_forget(self, socket: socket.socket, request_cmd: str) -> None:
        cmd_str = cmd.serialize(request_cmd)
        socket.sendall(cmd_str.encode())

    def send_request(self, socket: socket.socket, request_cmd: Dict) -> str:
        self.send_and_forget(socket, request_cmd)
        response = receive_all(socket)
        return response
    
    def request_download(self, socket: socket.socket, download_cmd: Dict) -> bool:
        # envia requisição de download
        cmd_str = cmd.serialize(download_cmd)
        socket.sendall(cmd_str.encode())
        # aguarda confirmação com propriedades do arquivo (se existe, etc)
        file_prop_cmd = cmd.deserialize(receive_all(socket))
        file_name, file_size = file_prop_cmd['name'], file_prop_cmd['size']
        if file_size <= 0:
            return { 'success': False, 'message': f'{file_name} não existe.\n' }
        
        # faz o download do arquivo
        download_status = download_file(self.path, file_name, file_size, socket)
        return download_status

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
                request_cmd = self.join_command_factory(list_files(self.path), self.port)
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = cmd.deserialize(self.send_request(conn, request_cmd))
                # processa o comando de resposta
                self.join_ok_command_handler(response_cmd)
        finally:
            self.close_server_connection(conn)

    def search(self) -> None:
        # abre-se uma conexão com o servidor
        conn = self.open_server_connection()
        try:
            if conn is not None:
                # solicita a factory a criação de um search command
                request_cmd = self.search_command_factory(input('Nome do arquivo: '))
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = cmd.deserialize(self.send_request(conn, request_cmd))
                self.search_result_command_handler(response_cmd)
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
                request_cmd = self.download_command_factory(file_name)
                # envia o command para o server e faz o download do arquivo
                download_status = self.request_download(conn, request_cmd)
                if not download_status['success']:
                    raise Exception(download_status['message'])
                else:
                    print(f'Arquivo {file_name} baixado com sucesso na pasta {self.path}\n')
        finally:
            self.close_server_connection(conn)
    
    def update(self) -> None:
        # abre-se uma conexão com o servidor
        conn = self.open_server_connection()
        try:
            if conn is not None:
                # solicita a factory a criação de um search command
                request_cmd = self.update_command_factory(input('Nome do arquivo: '), self.port)
                # envia o command ao server e aguarda o comando de resposta
                response_cmd = cmd.deserialize(self.send_request(conn, request_cmd))
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
    def join_ok_command_handler(self, join_ok_cmd: Dict) -> None:
        files, sender_address = join_ok_cmd['files'], join_ok_cmd['sender_address']
        print(f'Sou peer {sender_address} com arquivos {", ".join(files)}')

    def search_result_command_handler(self, search_result_cmd: Dict) -> None:
        results = search_result_cmd['results']
        print(f'peers com arquivo solicitado: {", ".join(results)}')

    def download_command_handler(self, download_cmd: Dict) -> str:
        return download_cmd['file_name']
    
    def download_ok_command_hander(self, download_ok: Dict) -> None:
        print('Arquivo [só nome do arquivo] baixado com sucesso na pasta [nome da pasta]')

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
            while True:
                try:
                    option = int(input('1 - JOIN | 2 - SEARCH | 3 - DOWNLOAD | 4 - UPDATE: '))
                    if option == 1:
                        self.client.join()
                    elif option == 2:
                        self.client.search()
                    elif option == 3:
                        self.client.download()
                    elif option == 4:
                        self.client.update()
                    else:
                        print('Opção inexistente.\n')
                        
                except (KeyboardInterrupt, EOFError):
                    print('saindo...\n')
                    break
                except Exception as e:
                    print('Erro ao concluir a operação:', e)
                    pass
            os._exit(os.EX_OK) 
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
                file_name = self.client.download_command_handler(download_cmd)
                file_path = f'{self.client.path}/{file_name}'
                
                if os.path.isfile(file_path):
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

if __name__ == '__main__':
    main()
