import os
from tqdm import tqdm
from typing import Dict

def receive_all(socket) -> bytes:
    buffer_size = 1024
    content = b""
    while True:
        temp = socket.recv(buffer_size)
        content += temp
        if len(temp) < buffer_size:
            break
    return content

def download_file(path: str, file_name: str, socket) -> Dict:
    try:
        buffer_size = 4096
        # recebo do peer provider o tamanho do arquivo
        server_file_size = int(socket.recv(buffer_size).decode())
        local_file_path = f'{path}/{file_name}'
        if not os.path.isdir(path):
            raise Exception('Diretorio destino não existe')

        # crio uma barra de progresso para o download
        bar = tqdm(range(server_file_size), f"Baixando {file_name}", unit="B", unit_scale=True, unit_divisor=buffer_size/2)
        # crio o arquivo com permissão de escrita
        with open(local_file_path, 'wb') as file:
            while True:
                # enquanto houver, recebo um pacote e escrevo no arquivo
                temp = socket.recv(buffer_size)
                # se não houver mais conteudo, o download acabou
                if not temp:
                    break
                file.write(temp)
                bar.update(len(temp))
        print('\n\n')                
        # o download foi bem sucedido se o arquivo criado tiver o mesmo tamanho do original
        local_file_size = os.path.getsize(local_file_path)
        return { 'success': local_file_size == server_file_size, 'message': '' }
    except Exception as e:
        return { 'success': False, 'message': e }
