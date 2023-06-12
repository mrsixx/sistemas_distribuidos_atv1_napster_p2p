import socket
from dataclasses import dataclass
from mysocket import receive_all
import command as cmd

@dataclass
class Server:
    def __init__(self, ip: str, port: int) -> None:
        self._ip = ip
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(5)

    #region getters
    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    @property
    def socket(self):
        return self._socket
    #endregion
    def close(self) -> None:
        self.socket.close()

    def listen(self) -> None:
        print(f"Servidor iniciado em {self.ip}:{self.port}")
        while True:
            client_socket, client_address = self.socket.accept()
            print(f"Got connection from: {client_address[0]}:{client_address[1]}")
            self.handle_request(client_socket)

    def handle_request(self, client_socket) -> None:
        request = receive_all(client_socket)
        print('receiving request')
        response = self.process_request(request)
        print('sending response', response)
        if response != '':
            client_socket.sendall(response.encode())
        client_socket.close()
    
    def process_request(self, request: bytes) -> str:
        return cmd.handle(request.decode())


def main():
    server = Server('127.0.0.1', int(input('port:')))
    try: 
        server.listen()
    finally:
        server.close()

if __name__ == '__main__':
    main()