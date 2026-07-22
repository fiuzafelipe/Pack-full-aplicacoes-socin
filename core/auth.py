import requests

BASE_URL = "http://aplicacoes.socin.com.br"

def get_authenticated_session():
    """
    Realiza o login e retorna a sessão autenticada.
    """
    session = requests.Session()
    
    # Camuflar o script como um navegador real (evita bloqueios de segurança)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    payload = {
        "username": "raphanet.parc",
        "password": "TTF6DRTFb9"
    }

    try:
        response = session.post(f"{BASE_URL}/loginok.html", data=payload, timeout=10)
        response.raise_for_status() # Levanta erro se for 404, 500, etc.
        
        # DICA: Verifique a string do response.text para garantir que logou.
        # Ex: if "Senha incorreta" in response.text: return None
        
        # Se tem cookies, é um bom sinal de que a sessão foi estabelecida
        if session.cookies:
            print("[AUTH] Login realizado ou sessão iniciada!")
            return session
        else:
            print("[AUTH] Aviso: Nenhum cookie retornado. O login pode ter falhado.")
            return session
            
    except requests.exceptions.RequestException as e:
        print(f"[AUTH] Erro ao tentar conectar: {e}")
        return None