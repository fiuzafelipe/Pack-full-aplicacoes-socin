import xml.etree.ElementTree as ET

from core.auth import session

BASE_URL = "http://aplicacoes.socin.com.br"


def mudar_diretorio(diretorio):

    response = session.post(
        f"{BASE_URL}/chdir.html",
        data={
            "dir": diretorio
        }
    )

    return response.status_code == 200


def listar_diretorios():

    response = session.post(
        f"{BASE_URL}/dir.html"
    )

    root = ET.fromstring(response.text)

    diretorios = []

    for row in root.findall(".//rowdata"):

        nome = row.find("name").text
        tipo = row.find("dir").text

        # dir == 1 significa pasta
        if tipo == "1":
            diretorios.append(nome)

    return diretorios


def get_versions():

    mudar_diretorio("/aplicativos")

    return listar_diretorios()


def get_paths(versao):

    mudar_diretorio(f"/aplicativos/{versao}")

    return listar_diretorios()