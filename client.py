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
        self.socket.sendall(request.encode())
        response = receive_all(self.socket)
        return response

    def close(self):
        self.socket.close()

    def join(self) -> None:
        #TODO: obter nome pasta e buscar nome dos arquivos disponiveis
        command = cmd.join_command('ablu.mp4', 'shazam.mp3')
        response = self.send_request(command)
        if response != '':
            cmd.join_ok_command_handler()

    def search(self) -> None:
        print('search feature')

    def download(self) -> None:
        print('download feature')

def main():
    client = Client('127.0.0.1', int(input('server port:')))
    try:
        while True:
            option = int(input('1 - JOIN | 2 - SEARCH | 3 - DOWNLOAD: '))
            if option == 1:
                client.join()
            elif option == 2:
                client.search()
            elif option == 3:
                client.download()
    finally:
        client.close()

if __name__ == '__main__':
    main()
