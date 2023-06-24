import os
from tqdm import tqdm

def receive_all(socket) -> bytes:
    buffer_size = 1024
    content = b""
    while True:
        temp = socket.recv(buffer_size)
        content += temp
        if len(temp) < buffer_size:
            break
    return content

def download_file(path: str, file_name: str, socket) -> bool:
    try:
        buffer_size = 4096
        # recebo do peer provider o tamanho do arquivo
        file_size = int(socket.recv(buffer_size).decode())
        local_file_path = f'{path}/{file_name}'
        #TODO: validar se diretorio existe
        # crio uma barra de progresso para o download
        bar = tqdm(range(file_size), f"Baixando {file_name}", unit="B", unit_scale=True, unit_divisor=buffer_size/2)
        # crio o arquivo com permissão de escrita
        with open(local_file_path, 'wb') as file:
            while True:
                # enquanto houver, recebo um pacote e escrevo no arquivo
                temp = socket.recv(buffer_size)
                # se não houver mais conteudo, o download acabou
                # o download foi bem sucedido se o arquivo criado tiver o mesmo tamanho do original
                #### O ERRO ESTA ACONTECENDO AQUI, AO FINAL DO DOWNLOAD NÂO ESTA CAINDO NO BREAK
                
                if not temp:
                    break
                file.write(temp)
                bar.update(len(temp))
            return os.path.getsize(local_file_path) == file_size
    except Exception as e:
        print(e)
        return False
        
