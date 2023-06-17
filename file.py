import os
from typing import List

def list_files(path: str) -> List[str]:
    files = []
    for _, _, arquivos in os.walk(path):
        for arquivo in arquivos:
            files.append(arquivo)
    return files