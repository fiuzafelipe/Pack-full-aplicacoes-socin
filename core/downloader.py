import os

from core.auth import session
from core.file_builder import gerar_arquivos

BASE_URL = "http://aplicacoes.socin.com.br"


def baixar_arquivos(versao, path):

    arquivos = gerar_arquivos(versao, path)

    pasta_temp = f"temp/{versao}_{path}"

    os.makedirs(pasta_temp, exist_ok=True)

    for arquivo in arquivos:

        download_url = f"{BASE_URL}/download&filename={arquivo}"

        response = session.get(download_url)

        caminho_arquivo = os.path.join(pasta_temp, arquivo)

        with open(caminho_arquivo, "wb") as f:
            f.write(response.content)

        print(f"Baixado: {arquivo}")

    print("Todos os arquivos foram baixados!")