import xml.etree.ElementTree as ET
from core.auth import get_authenticated_session

BASE_URL = "http://aplicacoes.socin.com.br"

def mudar_diretorio(session, diretorio):
    response = session.post(
        f"{BASE_URL}/chdir.html",
        data={
            "dir": diretorio
        }
    )
    return response.status_code == 200

def listar_diretorios(session):
    response = session.post(
        f"{BASE_URL}/dir.html"
    )
    
    try:
        root = ET.fromstring(response.text)
        diretorios = []

        for row in root.findall(".//rowdata"):
            nome = row.find("name").text
            tipo = row.find("dir").text

            # dir == 1 significa pasta
            if tipo == "1":
                diretorios.append(nome)

        return diretorios
        
    except ET.ParseError:
        # Se cair aqui, a sessão pode ter expirado e o site retornou HTML em vez de XML
        print("Erro: O servidor não retornou um XML válido.")
        return []

def get_versions():
    # 1. Pega a sessão autenticada
    session = get_authenticated_session()
    if not session:
        return []

    # 2. Usa a MESMA sessão para navegar e listar
    mudar_diretorio(session, "/aplicativos")
    return listar_diretorios(session)

def get_paths(versao):
    # 1. Pega a sessão autenticada
    session = get_authenticated_session()
    if not session:
        return ["Selecione"]

    # 2. Usa a MESMA sessão para navegar e listar
    mudar_diretorio(session, f"/aplicativos/{versao}")
    paths = listar_diretorios(session)
    
    # Retorna os paths, ou a opção padrão caso venha vazio
    return paths if paths else ["Selecione"]