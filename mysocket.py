def receive_all(socket) -> bytes:
    buffer_size = 1024
    content = b""
    while True:
        temp = socket.recv(buffer_size)
        content += temp
        if len(temp) < buffer_size:
            break
    return content

def download_file(path: str, file_name: str, socket) -> None:
    buffer_size = 1024
    #TODO: validar se diretorio existe
    with open(f'{path}/{file_name}', 'wb') as file:
        while True:
            temp = socket.recv(buffer_size)
            if not temp:
                break
            file.write(temp)
