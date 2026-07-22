import os
import json

def get_config_path():
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    pasta = os.path.join(appdata, 'PackFullSocin')
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, 'config.json')

def carregar_tema():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("modo", "Dark"), config.get("cor", "Azul"), config.get("auto_update", True)
        except Exception:
            pass
    return "Dark", "Azul", True

def salvar_tema(modo, cor, auto_update):
    path = get_config_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"modo": modo, "cor": cor, "auto_update": auto_update}, f)
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")