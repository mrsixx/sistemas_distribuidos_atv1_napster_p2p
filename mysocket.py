def receive_all(socket) -> bytes:
    buffer_size = 1024
    content = b""
    while True:
        temp = socket.recv(buffer_size)
        content += temp
        if len(temp) < buffer_size:
            break
    return content

def download_file(file_name, socket) -> None:
    buffer_size = 1024
    with open(file_name, 'wb') as file:
        while True:
            temp = socket.recv(buffer_size)
            if not temp:
                break
            file.write(temp)
