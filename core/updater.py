import requests
import os
import sys
import subprocess
import customtkinter as ctk

def checar_atualizacao(versao_atual, log_callback, app_instance):
    """Verifica a última release lançada no seu GitHub"""
    url_api = "https://api.github.com/repos/fiuzafelipe/Pack-full-aplicacoes-socin/releases"
    
    try:
        response = requests.get(url_api, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            
            if not dados:
                log_callback("[GitHub] Nenhuma release encontrada na lista.")
                return

            # Pega a primeira release da lista (a mais recente, seja ela pre-release ou não)
            release_mais_recente = dados[0]
            versao_recente = release_mais_recente.get("tag_name", "")
            
            # Normaliza as versões removendo a letra "v" (maiúscula ou minúscula) e os espaços.
            # Assim, "1.0.3" e "v1.0.3" se tornam exatamente iguais: "1.0.3"
            v_recente_num = versao_recente.lower().replace("v", "").strip()
            v_atual_num = versao_atual.lower().replace("v", "").strip()
            
            # Compara apenas os números
            if v_recente_num and v_recente_num != v_atual_num:
                log_callback(f"[GitHub] Nova versão detectada: {versao_recente}!")
                
                # Procura o link do arquivo update.zip
                zip_url = None
                for asset in release_mais_recente.get("assets", []):
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
            log_callback(f"[GitHub] Falha ao consultar API (Status {response.status_code}).")
            
    except Exception as e:
        log_callback(f"[GitHub] Aviso: Falha ao checar atualizações ({e}).")

# (A função exibir_popup_atualizacao continua exatamente igual a anterior)
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
        import sys, os, ctypes
        
        # Tenta encontrar o updater.exe na pasta instalada
        pasta_base = os.path.dirname(sys.executable)
        updater_exe = os.path.abspath(os.path.join(pasta_base, "updater.exe"))
        
        # Truque: Se você estiver testando direto da pasta 'dist', o updater fica na 'dist_updater'
        if not os.path.exists(updater_exe):
            updater_exe = os.path.abspath(os.path.join(pasta_base, "..", "dist_updater", "updater.exe"))

        if os.path.exists(updater_exe):
            try:
                # O "runas" avisa o Windows que precisamos da tela de Permissão de Administrador (UAC)
                ctypes.windll.shell32.ShellExecuteW(None, "runas", updater_exe, zip_url, None, 1)
                
                # Se o comando acima deu certo, fecha o app principal
                app.destroy()
                sys.exit(0)
            except Exception as e:
                app.log(f"[Erro] Falha ao acionar permissão de administrador: {e}")
                popup.destroy()
        else:
            app.log("[Erro] O arquivo updater.exe não foi encontrado! Verifique a sua instalação.")
            popup.destroy()

    frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
    frame_btns.pack(fill="x", padx=40)

    btn_sim = ctk.CTkButton(frame_btns, text="Sim, Atualizar", fg_color="#28a745", hover_color="#218838", command=iniciar_update)
    btn_sim.pack(side="left")
    
    btn_nao = ctk.CTkButton(frame_btns, text="Mais tarde", fg_color="#6c757d", hover_color="#5a6268", command=popup.destroy)
    btn_nao.pack(side="right")
    
    app._aplicar_icone(popup)