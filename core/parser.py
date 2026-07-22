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
        print("Erro: O servidor não retornou um XML válido.")
        return []

def get_versions():
    session = get_authenticated_session()
    if not session:
        return []

    mudar_diretorio(session, "/aplicativos")
    pastas_brutas = listar_diretorios(session)
    
    # ==========================================
    # FILTRAGEM INTELIGENTE DE PASTAS
    # ==========================================
    versoes_filtradas = []
    for pasta in pastas_brutas:
        pasta = pasta.strip()
        # Mantém apenas se começar com número (versões ex: 15, 16) 
        # OU se for exatamente uma das pastas especiais solicitadas
        if pasta and (pasta[0].isdigit() or pasta in ["instaladores", "sistema_operacional"]):
            versoes_filtradas.append(pasta)
            
    return versoes_filtradas

def get_paths(versao):
    session = get_authenticated_session()
    if not session:
        return ["Selecione"]

    # Se selecionou uma das pastas especiais, não existem sub-paths numéricos
    if versao in ["instaladores", "sistema_operacional"]:
        return ["Não se aplica"]

    mudar_diretorio(session, f"/aplicativos/{versao}")
    paths = listar_diretorios(session)
    
    return paths if paths else ["Selecione"]