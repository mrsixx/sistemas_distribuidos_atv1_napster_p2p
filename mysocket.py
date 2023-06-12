def receive_all(socket_cliente) -> bytes:
    buffer_size = 1024
    content = b""
    while True:
        temp = socket_cliente.recv(buffer_size)
        content += temp
        if len(temp) < buffer_size:
            break
    return content