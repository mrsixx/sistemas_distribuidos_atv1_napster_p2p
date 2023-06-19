from socket import socket, AF_INET, SOCK_STREAM
from dataclasses import dataclass
from threading import Thread, Lock
from typing import Dict, List
from mysocket import receive_all
import command as cmd

@dataclass
class Server:
    # construtor da classe server que recebe a parametrizacao do endereço ip:porta vinculado a instancia em execução
    def __init__(self, ip: str, port: int) -> None:
        self._ip = ip
        self._port = port
        # criação do socket de conexão e bind no ip:porta parametrizado
        self._server_socket = socket(AF_INET, SOCK_STREAM)
        self._server_socket.bind((self.ip, self.port))
        self._server_socket.listen(5)
        # estrutura de dados para armazenamento dos usuarios registrados
        self._files = dict()
        self._lock = Lock()

    #region getters
    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    @property
    def server_socket(self):
        return self._server_socket
    #endregion

    def close(self) -> None:
        self.server_socket.close()

    def listen(self) -> None:
        while True:
            # aguardo um client se conectar
            client_socket, client_address = self.server_socket.accept()
            # despacho para um thread tratar sua requisição
            handler_thread = self.RequestHandlerThread(self, client_socket, client_address)
            handler_thread.start()

    def get_file_providers(self, file_name) -> List[str]:
        formatted_file_name = file_name.upper()
        with self._lock:
            file_providers = self._files.get(formatted_file_name)
            if file_providers is None:
                return []

            format_providers = lambda d: [f'{ip}:{port}' for ip, ports in d.items() for port in ports.keys()]
            return format_providers(file_providers)

    # registra um client provedor de arquivos em um dicionario tridimensional para otimizar a busca
    def set_file_provider(self, file_name: str, ip: str, port: int) -> None:
        formatted_file_name = file_name.upper()
        with self._lock:
            if formatted_file_name not in self._files:
                self._files[formatted_file_name] = dict()
            if ip not in self._files[formatted_file_name]:
                self._files[formatted_file_name][ip] = dict()
            
            self._files[formatted_file_name][ip][port] = 1

    # classe aninhada para fazermos o dispatch da requisição para outras threads
    class RequestHandlerThread(Thread):
        def __init__(self, server, client_socket, client_address) -> None:
            Thread.__init__(self)
            self._server = server
            self._client_socket = client_socket
            self._client_address = client_address
      
        # region getters
        @property
        def server(self):
            return self._server
        
        @property
        def client_socket(self):
            return self._client_socket
        
        @property
        def client_address(self):
            return self._client_address
        # endregion

        # sobrescrevendo a função run
        def run(self):
            request = receive_all(self.client_socket)
            response_cmd = self.process_request(request)
            if response_cmd is not None:
                self.client_socket.sendall(cmd.serialize(response_cmd).encode())
            self.client_socket.close()

        # aciona o command handler para dar o tratamento adequado de acordo com o comando recebido
        def process_request(self, request: bytes) -> Dict:
            command = cmd.deserialize(request.decode())
            command['sender'] = {'ip': self.client_address[0], 'port': self.client_address[1]}
            return cmd.server_handle(self.server, command)

def main():
    try:
        ip = input('IP (default 127.0.0.1): ')
        port = input('Port (default 1099): ')
        ip = ip if ip != '' else '127.0.0.1'
        port = int(port) if port != '' else 1099
        server = Server(ip, port)
        try:
            server.listen()
        finally:
            server.close()
    except Exception as e:
        print('Erro durante a execução: ', e)

if __name__ == '__main__':
    main()