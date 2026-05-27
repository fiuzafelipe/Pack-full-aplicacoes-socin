# =========================================================
# AUTENTICACAO DE USUARIO
# =========================================================

import requests

BASE_URL = "http://aplicacoes.socin.com.br"

session = requests.Session()

payload = {
    "username": "raphanet.parc",
    "password": "TTF6DRTFb9"
}

response = session.post(
    f"{BASE_URL}/loginok.html",
    data=payload
)

if response.status_code == 200:
    print("Login realizado com sucesso!")
    print(session.cookies.get_dict())
else:
    print("Erro no login.")