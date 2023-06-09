import helpers
from socket import socket, AF_INET, SOCK_STREAM
from dataclasses import dataclass
from threading import Thread, Lock
from typing import Dict, List

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

    # region factories
    def join_ok_command_factory(self, files, sender_address) -> Dict:
        return { 'name': 'JOIN_OK', 'files': files, 'sender_address': sender_address }

    def search_result_command_factory(self, results: List[str]) -> Dict:
        return { 'name': 'SEARCH_RESULT', 'results': results }
    
    def update_ok_command_factory(self) -> Dict:
        return { 'name': 'UPDATE_OK' }
    # endregion

    # region command handlers
    def server_handle(self, command: Dict) -> Dict:
        cmd_name = command['name'].upper() if command['name'] is not None else ''
        if cmd_name == 'JOIN':
            return self.join_command_handler(command)
        if cmd_name == 'SEARCH':
            return self.search_command_handler(command)
        if cmd_name == 'UPDATE':
            return self.update_command_handler(command)
        return ''

    def join_command_handler(self, join_cmd: Dict) -> Dict:
        files, ip, port = join_cmd['files'], join_cmd['sender']['ip'], join_cmd['client_port']
        sender_address = f'{ip}:{port}'
        for file in files:
            self.set_file_provider(file, ip, port)
        print(f'Peer {sender_address} adicionado com arquivos {", ".join(files)}')
        return self.join_ok_command_factory(files, sender_address)

    def search_command_handler(self, search_cmd: Dict) -> Dict:
        file_name, sender = search_cmd['file_name'], search_cmd['sender']
        print(f'Peer {sender["ip"]}:{sender["port"]} está procurando pelo arquivo {file_name}')
        search_result = self.get_file_providers(file_name)
        return self.search_result_command_factory(search_result)

    def update_command_handler(self, update_cmd: Dict) -> Dict:
        file_name, ip, port = update_cmd['file_name'], update_cmd['sender']['ip'], update_cmd['client_port']
        self.set_file_provider(file_name, ip, port)
        return self.update_ok_command_factory()
    # endregion

    def close(self) -> None:
        self.server_socket.close()

    def listen(self) -> None:
        while True:
            try:
                # aguardo um client se conectar
                client_socket, client_address = self.server_socket.accept()
                # despacho para um thread tratar sua requisição
                handler_thread = self.RequestHandlerThread(self, client_socket, client_address)
                handler_thread.start()
            except:
                pass

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
            request = helpers.socket_receive_all(self.client_socket)
            response_cmd = self.process_request(request)
            if response_cmd is not None:
                self.client_socket.sendall(helpers.json_serialize(response_cmd).encode())
            self.client_socket.close()

        # aciona o command handler para dar o tratamento adequado de acordo com o comando recebido
        def process_request(self, request: bytes) -> Dict:
            command = helpers.json_deserialize(request.decode())
            command['sender'] = {'ip': self.client_address[0], 'port': self.client_address[1]}
            return self.server.server_handle(command)

def main():
    try:
        ip = input('IP (default 127.0.0.1): ') or '127.0.0.1'
        port = int(input('Port (default 1099): ') or '1099')
        server = Server(ip, port)
        try:
            server.listen()
        finally:
            server.close()
    except Exception as e:
        print('Erro durante a execução: ', e)

if __name__ == '__main__':
    main()