import os
import json
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

# Define o caminho %appdata%/FiuzaTechnology/config.json
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'Technology')
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')

# Configurações padrão
DEFAULT_CONFIG = {
    "primeira_execucao": True,
    "tema": "Light",
    "cor": "blue",
    "senha": "",
    "imagens_bloqueio": []
}

def carregar_config():
    os.makedirs(APPDATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        salvar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return DEFAULT_CONFIG

def salvar_config(config_data):
    os.makedirs(APPDATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)