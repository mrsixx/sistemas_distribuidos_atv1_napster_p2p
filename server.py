import socket
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Server:
    def __init__(self, ip: str, port: int) -> None:
        self._ip = ip
        self._port = port

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port
    
    def listen(self) -> None:
        s = socket.socket()
        s.bind((self.ip, self.port))
        print('socket binded to %s' %(self.port))
        s.listen(5)
        print('socket is listening')
        while True:
            c, addr = s.accept()
            print('Got connection from', addr)
            content = ''.join(['x'* i for i in range(0,100)]) + 'a' 
            c.send(content.encode())
            c.close()
            break


def main():
    server = Server('', 12345)
    print(server)
    server.listen()

if __name__ == '__main__':
    main()