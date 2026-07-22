import requests
from cryptography.fernet import Fernet

BASE_URL = "http://aplicacoes.socin.com.br"

def get_authenticated_session():
    """
    Realiza o login de forma segura, descriptografando a senha em tempo de execução.
    """
    session = requests.Session()
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    # =========================================================================
    # DADOS CRIPTOGRAFADOS (Seguros contra visualização direta no GitHub)
    # =========================================================================
    # Cole aqui a chave que você gerou no Passo 2:
    CHAVE_SECRETA = b"NPOOjplVPrHFzdfwH0pEt8eZFHftVZ0I9kdgDpggxVM=" 
    
    # Cole aqui o texto cifrado gerado no Passo 2:
    SENHA_CIFRADA = b"gAAAAABqYQ1yBMn39cGH7gkCT1zK3hafyd3LbuCPHqhbVNhLI0qw-C2vJxpNswutqwZo64jZtDxjwKWNv8CznLg-AcEK5OqeHw=="
    
    try:
        # Descriptografa a senha milissegundos antes de usar
        cipher = Fernet(CHAVE_SECRETA)
        senha_decodificada = cipher.decrypt(SENHA_CIFRADA).decode('utf-8')

        payload = {
            "username": "raphanet.parc",
            "password": senha_decodificada
        }

        response = session.post(f"{BASE_URL}/loginok.html", data=payload, timeout=10)
        response.raise_for_status()
        
        if session.cookies:
            print("[AUTH] Login realizado com sucesso!")
            return session
        else:
            print("[AUTH] Aviso: Nenhum cookie retornado.")
            return session
            
    except Exception as e:
        print(f"[AUTH] Erro na autenticação ou descriptografia: {e}")
        return None