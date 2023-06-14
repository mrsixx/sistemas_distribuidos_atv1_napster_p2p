import socket
from dataclasses import dataclass
import command as cmd
from threading import Thread
from mysocket import receive_all
from time import sleep

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
    def send_request(self, socket: socket.socket, request: str) -> str:
        socket.sendall(request.encode())
        response = receive_all(socket)
        return response
    
    def open_server_connection(self) -> socket.socket:
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.connect((self.server_ip, self.server_port))
        return sk

    def close_server_connection(self, socket: socket.socket) -> None:
        socket.close()
    # endregion

    # region features
    def join(self) -> None:
        try:
            # abre-se uma conexão com o servidor
            conn = self.open_server_connection()
            #TODO: obter nome pasta e buscar nome dos arquivos disponiveis
            command = cmd.join_command('ablu.mp4', 'shazam.mp3')
            response = self.send_request(conn, command)
            if response != '':
                cmd.join_ok_command_handler()
        finally:
            self.close_server_connection(conn)

    def search(self) -> None:
        print('search feature')

    def download(self) -> None:
        print('download feature')
    
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
                option = int(input('1 - JOIN | 2 - SEARCH | 3 - DOWNLOAD: '))
                if option == 1:
                    self.client.join()
                elif option == 2:
                    self.client.search()
                elif option == 3:
                    self.client.download()
                else:
                    print('Opção inexistente.\n')

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
            print(f'Enviando o arquivo xxxxx para {self.peer_address}...')


def main(dev_enviroment = False):
    #TODO: validar
    ip = input('IP: ')
    if dev_enviroment:
        ip = ip if ip != '' else '127.0.0.1'
    
    port = int(input('Port: '))    
    path = input('Path: ')
    
    client = Client(ip, port, path)
    client.run_iteractive_menu()
    client.listen_download_requests()

if __name__ == '__main__':
    main()
