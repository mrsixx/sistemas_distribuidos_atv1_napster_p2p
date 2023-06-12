import socket
from dataclasses import dataclass
import command as cmd
from mysocket import receive_all

@dataclass
class Client:
    def __init__(self, ip: str, port: int) -> None:
        self._ip = ip
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))

    # region getters
    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    @property
    def socket(self):
        return self._socket
    # endregion

    def send_request(self, request: str) -> str:
        print('sending request', request)
        self.socket.sendall(request.encode())
        response = receive_all(self.socket)
        print('receiving response', response)
        return response

    def close(self):
        self.socket.close()

    def join(self) -> None:
        command = cmd.factory('JOIN', 'ablu.mp4', 'shazam.mp3')
        response = self.send_request(command)
        print(response.decode())


def main():
    client = Client('127.0.0.1', int(input('server port:')))
    client.join()
    client.close()

if __name__ == '__main__':
    main()
