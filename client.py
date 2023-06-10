import socket
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Client:
    def __init__(self, ip: str, port: int) -> None:
        self._ip = ip
        self._port = port

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    def join(self) -> None:
        s = socket.socket()
        s.connect((self.ip, self.port))
        content = b''
        while True:
            temp_content = s.recv(1024)
            if not temp_content:
                break
            content += temp_content
        s.close()
        print(content.decode())


def main():
    client = Client('127.0.0.1', 12345)
    client.join()

if __name__ == '__main__':
    main()