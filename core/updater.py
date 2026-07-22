import requests
import os
import sys
import subprocess
import customtkinter as ctk

def checar_atualizacao(versao_atual, log_callback, app_instance):
    """Verifica a última release lançada no seu GitHub"""
    url_api = "https://api.github.com/repos/fiuzafelipe/Pack-full-aplicacoes-socin/releases/latest"
    
    try:
        response = requests.get(url_api, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            versao_recente = dados.get("tag_name", "")
            
            # Se a versão for diferente, ativa a atualização
            if versao_recente and versao_recente != versao_atual:
                log_callback(f"[GitHub] Nova versão detectada: {versao_recente}!")
                
                # Procura o link do arquivo update.zip
                zip_url = None
                for asset in dados.get("assets", []):
                    if asset["name"] == "update.zip":
                        zip_url = asset["browser_download_url"]
                        break
                
                if zip_url:
                    # Exibe a janela perguntando se quer atualizar
                    app_instance.after(0, lambda: exibir_popup_atualizacao(app_instance, versao_atual, versao_recente, zip_url))
                else:
                    log_callback("[GitHub] O arquivo 'update.zip' não foi encontrado na release online.")
            else:
                log_callback("[GitHub] Seu sistema já está na versão mais recente.")
                
        else:
            log_callback(f"[GitHub] Nenhuma release encontrada (Status {response.status_code}).")
            
    except Exception as e:
        log_callback(f"[GitHub] Aviso: Falha ao checar atualizações ({e}).")

def exibir_popup_atualizacao(app, versao_atual, versao_recente, zip_url):
    popup = ctk.CTkToplevel(app)
    popup.title("Atualização Disponível")
    
    largura, altura = 400, 200
    x = app.winfo_rootx() + (app.winfo_width() // 2) - (largura // 2)
    y = app.winfo_rooty() + (app.winfo_height() // 2) - (altura // 2)
    popup.geometry(f"{largura}x{altura}+{x}+{y}")
    popup.resizable(False, False)
    popup.transient(app)
    popup.grab_set()
    popup.focus_force()

    lbl = ctk.CTkLabel(popup, text=f"Uma nova versão ({versao_recente}) está disponível!\n\nSua versão atual: {versao_atual}\n\nDeseja atualizar agora?", font=("Segoe UI", 14))
    lbl.pack(pady=25)

    def iniciar_update():
        # Tenta encontrar o updater.exe na pasta instalada
        pasta_base = os.path.dirname(sys.executable)
        updater_exe = os.path.join(pasta_base, "updater.exe")
        
        if os.path.exists(updater_exe):
            # Aciona o atualizador enviando o link de download e fecha o app
            subprocess.Popen([updater_exe, zip_url])
            app.destroy()
            sys.exit(0)
        else:
            app.log("[Erro] updater.exe não encontrado! Instale a versão via instalador (.exe).")
            popup.destroy()

    frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
    frame_btns.pack(fill="x", padx=40)

    btn_sim = ctk.CTkButton(frame_btns, text="Sim, Atualizar", fg_color="#28a745", hover_color="#218838", command=iniciar_update)
    btn_sim.pack(side="left")
    
    btn_nao = ctk.CTkButton(frame_btns, text="Mais tarde", fg_color="#6c757d", hover_color="#5a6268", command=popup.destroy)
    btn_nao.pack(side="right")
    
    app._aplicar_icone(popup)