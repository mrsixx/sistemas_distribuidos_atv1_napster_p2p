from socket import socket, AF_INET, SOCK_STREAM
from dataclasses import dataclass
from threading import Thread
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
            handler_thread = self.RequestHandlerThread(client_socket, client_address)
            handler_thread.start()

    # classe aninhada para fazermos o dispatch da requisição para outras threads
    class RequestHandlerThread(Thread):
        def __init__(self, client_socket, client_address) -> None:
            Thread.__init__(self)
            self._client_socket = client_socket
            self._client_address = client_address
      
        # region getters
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
            response = self.process_request(request)
            if response != '':
                self.client_socket.sendall(response.encode())
            self.client_socket.close()

        # aciona o command handler para dar o tratamento adequado de acordo com o comando recebido
        def process_request(self, request: bytes) -> str:
            return cmd.handle(request.decode())

def main():
    try:
        ip = input('IP (default 127.0.0.1): ')
        port = input('Port (default 1099): ')
        ip = ip if ip != '' else '127.0.0.1'
        port = int(port) if port != '' else 1099
        server = Server(ip, port)

        server.listen()
    finally:
        server.close()

if __name__ == '__main__':
    main()