import os
import json

def get_config_path():
    """Retorna o caminho seguro do AppData no Windows"""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    pasta = os.path.join(appdata, 'PackFullSocin')
    
    # Cria a pasta caso não exista
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, 'config.json')

def carregar_tema():
    """Lê o arquivo config.json e retorna as preferências"""
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("modo", "Dark"), config.get("cor", "Azul")
        except Exception:
            pass
    # Padrão de fábrica se for a primeira vez abrindo o app
    return "Dark", "Azul"

def salvar_tema(modo, cor):
    """Salva a escolha do usuário no AppData"""
    path = get_config_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"modo": modo, "cor": cor}, f)
    except Exception as e:
        print(f"Erro ao salvar tema: {e}")