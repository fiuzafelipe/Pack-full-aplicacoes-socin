import customtkinter as ctk
import tkinter as tk
import tkinter.ttk as ttk
import asyncio
import threading
from telethon import TelegramClient
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
import time
import json
import hashlib
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

# ==========================================
# IMPORTAÇÕES E SINCRONIZAÇÃO DE DIRETÓRIOS
# ==========================================
# Adiciona a pasta raiz ao sys.path para conseguirmos ler o tema do app principal
pasta_api = os.path.dirname(os.path.abspath(__file__))
pasta_raiz = os.path.dirname(pasta_api)
if pasta_raiz not in sys.path:
    sys.path.insert(0, pasta_raiz)

try:
    from core.theme import carregar_tema
except Exception:
    carregar_tema = None

from utils import obter_caminho, centralizar_janela, formatar_tamanho
from tela_bloqueio import TelaDeBloqueio

# CARREGA O .ENV COM O CAMINHO ABSOLUTO GARANTIDO
load_dotenv(obter_caminho(".env"))

class TelegramCloudApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Fiuza Technology - Telegram Cloud Sync (v1.0.6)")
        centralizar_janela(self, 720, 610, offset_y=25)
        self.resizable(False, False)

        self.cores_destaque = {
            "Verde": {"fg": "#28a745", "hover": "#218838", "text": "#FFFFFF", "light_bg": "#e9f7ef", "dark_bg": "#0f291a"},
            "Vermelho": {"fg": "#dc3545", "hover": "#c82333", "text": "#FFFFFF", "light_bg": "#fdf1f2", "dark_bg": "#2c0b0e"},
            "Azul": {"fg": "#007BFF", "hover": "#0056b3", "text": "#FFFFFF", "light_bg": "#e7f1ff", "dark_bg": "#001a35"},
            "Amarelo": {"fg": "#FFC107", "hover": "#e0a800", "text": "#000000", "light_bg": "#fff9e6", "dark_bg": "#332701"},
            "Laranja": {"fg": "#fd7e14", "hover": "#e36209", "text": "#FFFFFF", "light_bg": "#fff2e8", "dark_bg": "#331804"},
            "Roxo": {"fg": "#6f42c1", "hover": "#5a32a3", "text": "#FFFFFF", "light_bg": "#f3f0f9", "dark_bg": "#170d29"},
            "Preto": {"fg": "#343a40", "hover": "#23272b", "text": "#FFFFFF", "light_bg": "#f8f9fa", "dark_bg": "#121416"}
        }

        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')

        self.historico_arquivos = []
        self.total_arquivos_sessao = 0
        self.is_downloading = False
        self.flag_cancelar = False 
        self.uso_total_bytes = 0
        self.admin_mode = False

        self.map_ui_to_backend = {}
        self.map_backend_to_ui = {}
        
        self.pastas_expandidas = set()
        self.estado_busca_up = 0     
        self.estado_busca_down = 0   
        self.termo_busca_up = ""
        self.termo_busca_down = ""
        self.labels_tamanho_ui = []

        self.api_id = int(os.getenv("TELEGRAM_API_ID", 0))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.session_name = 'Cloud Nuvem API'
        self.client = None
        self.async_loop = None
        self.phone_number = None
        
        appdata_path = os.getenv('APPDATA')
        self.config_dir = os.path.join(appdata_path, "Technology")
        os.makedirs(self.config_dir, exist_ok=True)
        self.arquivo_config_pastas = os.path.join(self.config_dir, "save.json")
        
        self.pastas_locais, self.ordem_arquivos, self.saved_modo, self.saved_cor, self.primeiro_acesso = self.carregar_configuracoes()
        self.pastas_nuvem = {pasta: [] for pasta in self.pastas_locais} 
        self.pasta_atual_mgr = None

        # --- LÓGICA DE SINCRONIZAÇÃO DE TEMA ---
        # Se o módulo core.theme for importado com sucesso, ele pega o tema do Pack Socin (main.py)
        if carregar_tema:
            try:
                modo_main, cor_main, _ = carregar_tema()
                if modo_main and cor_main:
                    self.saved_modo = modo_main
                    self.saved_cor = cor_main
            except Exception:
                pass
        # ---------------------------------------

        if not self.api_id or not self.api_hash:
            messagebox.showerror("Erro Crítico", f"Credenciais do Telegram não encontradas!\nO arquivo .env não foi localizado.")
            self.destroy()
            sys.exit(1) # <--- Evita o erro "application has been destroyed" matando o processo na hora

        self._aplicar_icone(self)
        self.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)
        self.setup_login_ui()
        self.bloqueio_manager = TelaDeBloqueio(self)
        self.setup_senha_mestra_ui()
        self.start_async_thread()
    
    # ==========================================
    # ENCERRAMENTO SEGURO
    # ==========================================
    def fechar_aplicacao(self):
        self.flag_cancelar = True
        
        # Tenta desconectar o cliente do Telegram suavemente
        try:
            if self.async_loop and self.client:
                asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.async_loop)
                self.async_loop.call_soon_threadsafe(self.async_loop.stop)
        except Exception:
            pass
            
        self.destroy()
        os._exit(0) # Força o encerramento imediato de todas as threads e limpa o terminal

    def _aplicar_icone(self, janela):
        try:
            caminho_ico = obter_caminho("assets/cloud.ico")
            if os.path.exists(caminho_ico):
                janela.after(250, lambda: janela.iconbitmap(caminho_ico))
        except Exception: pass

    # ==========================================
    # SISTEMA DE RETORNO (VOLTAR AO MAIN.PY)
    # ==========================================
    def voltar_para_principal(self):
        try:
            if getattr(sys, 'frozen', False):
                caminho_exe = os.path.join(os.path.dirname(sys.executable), "Pack_econect.exe")
                if os.path.exists(caminho_exe):
                    subprocess.Popen([caminho_exe], cwd=os.path.dirname(sys.executable))
                else:
                    messagebox.showerror("Erro", "O módulo principal (Pack_econect.exe) não foi encontrado.")
                    return
            else:
                pasta_api_atual = os.path.dirname(os.path.abspath(__file__))
                pasta_raiz_proj = os.path.dirname(pasta_api_atual)
                
                possiveis_caminhos = [
                    os.path.join(pasta_raiz_proj, "main.py"), 
                    os.path.join(pasta_raiz_proj, "ui", "main.py"), 
                    os.path.join(os.path.dirname(pasta_raiz_proj), "main.py")
                ]
                
                caminho_script = None
                for caminho in possiveis_caminhos:
                    if os.path.exists(caminho):
                        caminho_script = caminho
                        break
                
                if caminho_script:
                    subprocess.Popen([sys.executable, caminho_script], cwd=os.path.dirname(caminho_script))
                else:
                    messagebox.showwarning("Aviso", "O sistema não encontrou o 'main.py'.\nPor favor, localize-o manualmente.")
                    caminho_script = filedialog.askopenfilename(title="Selecione o arquivo main.py", filetypes=[("Python Files", "*.py")])
                    if caminho_script:
                        subprocess.Popen([sys.executable, caminho_script], cwd=os.path.dirname(caminho_script))
                    else:
                        return 
            
            self.destroy()
            sys.exit(0)
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Não foi possível voltar: {e}")

    def construir_mapa_pastas(self):
        self.map_ui_to_backend.clear()
        self.map_backend_to_ui.clear()
        self.lista_formatada = []
        
        raizes_ordem = []
        for p in self.pastas_locais:
            if "__" not in p:
                raiz = p if p.startswith("#") else "#" + p
            else:
                raiz = p.split("__")[0]
                if not raiz.startswith("#"):
                    raiz = "#" + raiz

            if raiz not in raizes_ordem:
                raizes_ordem.append(raiz)

        arvore = {raiz: [] for raiz in raizes_ordem}
        for p in self.pastas_locais:
            if "__" in p:
                raiz = p.split("__")[0]
                if not raiz.startswith("#"):
                    raiz = "#" + raiz
                arvore[raiz].append(p)

        def get_tamanho(pasta_alvo):
            total = sum(a.get("size", 0) for a in self.pastas_nuvem.get(pasta_alvo, []))
            prefix = pasta_alvo + "__"
            for p in self.pastas_locais:
                if p.startswith(prefix):
                    total += sum(a.get("size", 0) for a in self.pastas_nuvem.get(p, []))
            return total

        for raiz in raizes_ordem:
            tamanho = get_tamanho(raiz)
            str_tam = formatar_tamanho(tamanho) if tamanho > 0 else "0 KB"
            ui_str_raiz = f"📁 {raiz.replace('#', '')}   |   {str_tam}"

            while ui_str_raiz in self.map_ui_to_backend:
                ui_str_raiz += "\u200b"

            self.map_ui_to_backend[ui_str_raiz] = raiz
            self.map_backend_to_ui[raiz] = ui_str_raiz
            self.lista_formatada.append(ui_str_raiz)

            for sub in arvore[raiz]:
                sub_limpo = sub.split("__", 1)[1]
                tamanho_sub = get_tamanho(sub)
                str_tam_sub = formatar_tamanho(tamanho_sub) if tamanho_sub > 0 else "0 KB"
                ui_str_sub = f"    ↳ 📁 {sub_limpo}   |   {str_tam_sub}"

                while ui_str_sub in self.map_ui_to_backend:
                    ui_str_sub += "\u200b"

                self.map_ui_to_backend[ui_str_sub] = sub
                self.map_backend_to_ui[sub] = ui_str_sub
                self.lista_formatada.append(ui_str_sub)

    def atualizar_dropdowns(self):
        if hasattr(self, 'combo_pasta_up') and self.combo_pasta_up.winfo_exists():
            valores_up = []
            for item in self.lista_formatada:
                backend_val = self.map_ui_to_backend[item]
                if self.estado_busca_up == 1:
                    if self.termo_busca_up:
                        if self.termo_busca_up in item.lower() or self.termo_busca_up in backend_val.lower():
                            valores_up.append(item)
                    else:
                        valores_up.append(item)
                else: 
                    if "__" not in backend_val:
                        valores_up.append(item)
                    else:
                        raiz = "#" + backend_val.split("__")[0].replace("#", "")
                        if raiz in self.pastas_expandidas:
                            valores_up.append(item)
            
            self.combo_pasta_up['values'] = valores_up
            atual_up = self.combo_pasta_up.get()
            
            if self.estado_busca_up == 1 and not self.termo_busca_up:
                self.combo_pasta_up.set("(Digite algo para buscar subpastas em toda a nuvem)")
            else:
                if atual_up not in valores_up and valores_up:
                    self.combo_pasta_up.set(valores_up[0])
                elif not valores_up:
                    self.combo_pasta_up.set("")

        if hasattr(self, 'combo_pasta_down') and self.combo_pasta_down.winfo_exists():
            valores_down = []
            for item in self.lista_formatada:
                backend_val = self.map_ui_to_backend[item]
                if self.estado_busca_down == 1:
                    if self.termo_busca_down:
                        if self.termo_busca_down in item.lower() or self.termo_busca_down in backend_val.lower():
                            valores_down.append(item)
                    else:
                        valores_down.append(item)
                else: 
                    if "__" not in backend_val:
                        valores_down.append(item)
                    else:
                        raiz = "#" + backend_val.split("__")[0].replace("#", "")
                        if raiz in self.pastas_expandidas:
                            valores_down.append(item)
            
            self.combo_pasta_down['values'] = valores_down
            atual_down = self.combo_pasta_down.get()
            
            if self.estado_busca_down == 1 and not self.termo_busca_down:
                self.combo_pasta_down.set("")
            else:
                if atual_down not in valores_down and valores_down:
                    self.combo_pasta_down.set(valores_down[0])
                elif not valores_down:
                    self.combo_pasta_down.set("")
            
            if self.estado_busca_down == 0:
                self.filtrar_arquivos_por_pasta()

    def ao_selecionar_combobox(self, aba):
        combo = self.combo_pasta_up if aba == 'up' else self.combo_pasta_down
        selecao = combo.get()
        backend_val = self.map_ui_to_backend.get(selecao)
        
        if backend_val and "__" not in backend_val:
            estava_expandida = backend_val in self.pastas_expandidas
            self.pastas_expandidas.clear() 
            
            raiz_pura = backend_val if backend_val.startswith("#") else "#" + backend_val
            tem_subpastas = any(p.startswith(raiz_pura + "__") for p in self.pastas_locais)
            
            if not estava_expandida and tem_subpastas:
                self.pastas_expandidas.add(raiz_pura)
            
            self.atualizar_dropdowns()
            combo.set(selecao)
            
            if tem_subpastas:
                self.after(10, lambda: combo.event_generate('<Down>'))

        if aba == 'down' and self.estado_busca_down == 0:
            self.filtrar_arquivos_por_pasta()

    def set_estado_busca_up(self, estado):
        self.estado_busca_up = estado
        if estado == 0:
            self.entry_busca_up.pack_forget()
            self.lbl_pasta_up.configure(text="P A S T A   D E   D E S T I N O")
            self.lbl_pasta_up.pack(side="left", expand=True, padx=(26, 0))
            self.termo_busca_up = ""
            self.entry_busca_up.delete(0, 'end')
            
            if hasattr(self, 'scroll_upload'): self.scroll_upload.pack_forget()
            self.upload_controls_frame.pack(side="top", fill="both", expand=True)
            self.atualizar_dropdowns()
            
        elif estado == 1:
            self.lbl_pasta_up.pack_forget()
            self.entry_busca_up.configure(placeholder_text="Buscar pasta/subpasta...")
            self.entry_busca_up.pack(side="left", expand=True, fill="x", padx=(0, 5))
            self.entry_busca_up.delete(0, 'end')
            self.termo_busca_up = ""
            
            if hasattr(self, 'scroll_upload'): self.scroll_upload.pack_forget()
            self.upload_controls_frame.pack(side="top", fill="both", expand=True)
            self.entry_busca_up.focus()
            self.atualizar_dropdowns()
            
        elif estado == 2:
            self.entry_busca_up.configure(placeholder_text="Buscar arquivo na nuvem...")
            self.entry_busca_up.delete(0, 'end')
            self.termo_busca_up = ""
            
            self.upload_controls_frame.pack_forget()
            self.scroll_upload.pack(side="top", fill="both", expand=True, padx=20, pady=(2, 2))
            self.entry_busca_up.focus()
            self.filtrar_arquivos_upload()

    def set_estado_busca_down(self, estado):
        self.estado_busca_down = estado
        if estado == 0:
            self.entry_busca_down.pack_forget()
            self.lbl_pasta_down.configure(text="F I L T R A R   P O R   P A S T A")
            self.lbl_pasta_down.pack(side="left", expand=True, padx=(26, 0))
            self.termo_busca_down = ""
            self.entry_busca_down.delete(0, 'end')
            
            self.scroll_download.pack_forget()
            self.frame_down.pack(side="top", fill="x", padx=20, pady=(0, 2))
            self.scroll_download.pack(side="top", fill="both", expand=True, padx=20, pady=(2, 2))
            
            self.combo_pasta_down.configure(state="readonly")
            self.atualizar_dropdowns()
            self.filtrar_arquivos_por_pasta()
            
        elif estado == 1:
            self.lbl_pasta_down.pack_forget()
            self.entry_busca_down.configure(placeholder_text="Buscar pasta/subpasta...")
            self.entry_busca_down.pack(side="left", expand=True, fill="x", padx=(0, 5))
            self.entry_busca_down.delete(0, 'end')
            self.termo_busca_down = ""
            
            self.scroll_download.pack_forget()
            self.frame_down.pack(side="top", fill="x", padx=20, pady=(0, 2))
            self.scroll_download.pack(side="top", fill="both", expand=True, padx=20, pady=(2, 2))
            
            self.combo_pasta_down.configure(state="readonly")
            self.entry_busca_down.focus()
            self.atualizar_dropdowns()
            self.filtrar_arquivos_por_pasta()
            
        elif estado == 2:
            self.entry_busca_down.configure(placeholder_text="Buscar arquivo na nuvem...")
            self.entry_busca_down.delete(0, 'end')
            self.termo_busca_down = ""
            
            self.frame_down.pack_forget()
            self.combo_pasta_down.set("") 
            self.combo_pasta_down.configure(state="disabled")
            self.entry_busca_down.focus()
            self.filtrar_arquivos_por_pasta()

    def alternar_busca(self, aba):
        if aba == 'up':
            novo_estado = (self.estado_busca_up + 1) % 3
            self.set_estado_busca_up(novo_estado)
        elif aba == 'down':
            novo_estado = (self.estado_busca_down + 1) % 3
            self.set_estado_busca_down(novo_estado)

    def ao_digitar_busca(self, aba):
        if aba == 'up':
            self.termo_busca_up = self.entry_busca_up.get().strip().lower()
            if self.estado_busca_up in [1, 2]:
                self.filtrar_arquivos_upload()
        elif aba == 'down':
            self.termo_busca_down = self.entry_busca_down.get().strip().lower()
            if self.estado_busca_down in [1, 2]:
                self.filtrar_arquivos_por_pasta()

    def selecionar_pasta_busca(self, aba, item_ui):
        if aba == 'up':
            self.set_estado_busca_up(0)
            self.combo_pasta_up.set(item_ui)
            self.ao_selecionar_combobox('up')
        elif aba == 'down':
            self.set_estado_busca_down(0)
            self.combo_pasta_down.set(item_ui)
            self.ao_selecionar_combobox('down')

    def carregar_configuracoes(self):
        if os.path.exists(self.arquivo_config_pastas):
            try:
                with open(self.arquivo_config_pastas, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list): return data, {}, "Light", "Verde", True
                    elif isinstance(data, dict): 
                        return (data.get("pastas", ["#Geral", "#Instaladores", "#Documentos", "#Projetos"]),
                                data.get("arquivos", {}),
                                data.get("modo", "Light"),
                                data.get("cor", "Verde"),
                                data.get("primeiro_acesso", True))
            except Exception: pass
        return ["#Geral", "#Instaladores", "#Documentos", "#Projetos"], {}, "Light", "Verde", True

    def salvar_configuracoes(self):
        try:
            dados = {
                "pastas": self.pastas_locais, 
                "arquivos": self.ordem_arquivos,
                "modo": self.combo_modo.get() if hasattr(self, 'combo_modo') else self.saved_modo,
                "cor": self.combo_cor.get() if hasattr(self, 'combo_cor') else self.saved_cor,
                "primeiro_acesso": self.primeiro_acesso
            }
            with open(self.arquivo_config_pastas, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            self.construir_mapa_pastas()
        except Exception as e:
            self.log(f"[ERRO] Falha ao salvar no APPDATA: {str(e)}")

    def mudar_configuracoes_tema(self, *args):
        self.aplicar_tema()
        self.salvar_configuracoes()

    def mostrar_assinatura(self, event=None):
        popup = ctk.CTkToplevel(self)
        popup.title("Fiuza Technology")
        centralizar_janela(popup, 400, 180)
        popup.resizable(False, False)
        popup.transient(self)
        popup.attributes('-topmost', True)
        popup.after(200, popup.grab_set)
        popup.after(250, lambda: popup.focus_force())
        popup.after(300, lambda: popup.attributes('-topmost', False))
        self._aplicar_icone(popup)

        lbl_msg = ctk.CTkLabel(popup, text="Aplicação desenvolvida por Felipe Fiuza\n\nFiuza Technology - Development & Software Solutions", font=("Segoe UI", 14), justify="center")
        lbl_msg.pack(pady=(35, 25), padx=20)

        paleta = self.cores_destaque[self.combo_cor.get() if hasattr(self, 'combo_cor') else self.saved_cor]
        btn_ok = ctk.CTkButton(popup, text="OK", width=120, height=35, command=popup.destroy, fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"], corner_radius=8)
        btn_ok.pack()
        popup.bind("<Return>", lambda e: popup.destroy())

    def mostrar_popup_armazenamento(self, event=None):
        popup = ctk.CTkToplevel(self)
        popup.title("Estatísticas da Nuvem")
        centralizar_janela(popup, 380, 180)
        popup.resizable(False, False)
        popup.transient(self)
        popup.attributes('-topmost', True)
        popup.after(200, popup.grab_set)
        popup.after(250, lambda: popup.focus_force())
        popup.after(300, lambda: popup.attributes('-topmost', False))
        self._aplicar_icone(popup)

        texto = f"Há um espaço de {formatar_tamanho(self.uso_total_bytes)} em uso.\n\nCapacidade Total: Ilimitada ☁️"
        lbl_msg = ctk.CTkLabel(popup, text=texto, font=("Segoe UI", 14, "bold"), justify="center")
        lbl_msg.pack(pady=(35, 25), padx=20)

        paleta = self.cores_destaque[self.combo_cor.get()]
        btn_ok = ctk.CTkButton(popup, text="OK", width=120, height=35, command=popup.destroy, fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"], corner_radius=8)
        btn_ok.pack()
        popup.bind("<Return>", lambda e: popup.destroy())

    def atualizar_textos_armazenamento(self):
        texto_uso = f"☁️ Nuvem em uso: {formatar_tamanho(self.uso_total_bytes)}"
        if hasattr(self, 'btn_armazenamento') and self.btn_armazenamento.winfo_exists():
            self.btn_armazenamento.configure(text=texto_uso)
        
        if hasattr(self, 'gerenciador_manager') and hasattr(self.gerenciador_manager, 'btn_armazenamento_mgr') and self.gerenciador_manager.btn_armazenamento_mgr.winfo_exists():
            self.gerenciador_manager.btn_armazenamento_mgr.configure(text=texto_uso)

    def abrir_modal_alternar_modo(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Configurações de Acesso")
        centralizar_janela(modal, 400, 240)
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()
        self._aplicar_icone(modal)

        paleta = self.cores_destaque[self.combo_cor.get()]
        
        lbl_title = ctk.CTkLabel(modal, text="ALTERNAR MODO", font=("Segoe UI Black", 14))
        lbl_title.pack(pady=(15, 5))
        
        status_txt = "Desenvolvedor (Full)" if self.admin_mode else "Usuário (Leitura)"
        status_cor = "#28a745" if self.admin_mode else "#6c757d"
        lbl_status = ctk.CTkLabel(modal, text=f"Modo Atual: {status_txt}", font=("Segoe UI", 12, "bold"), text_color=status_cor)
        lbl_status.pack(pady=(0, 15))

        def set_modo_user():
            if not self.admin_mode: return
            self.admin_mode = False
            modal.destroy()
            self.recarregar_interface_modo()

        def prompt_modo_dev():
            if self.admin_mode: return
            for w in modal.winfo_children(): w.destroy()
            
            ctk.CTkLabel(modal, text="🔑 Acesso Restrito", font=("Segoe UI Black", 14)).pack(pady=(20, 10))
            entry_pw = ctk.CTkEntry(modal, placeholder_text="Senha Mestra", show="*", width=250, height=35)
            entry_pw.pack(pady=10)
            entry_pw.focus()
            
            def verify(e=None):
                pw = entry_pw.get()
                if hashlib.sha256(pw.encode()).hexdigest() == hashlib.sha256("admin@123!".encode()).hexdigest():
                    self.admin_mode = True
                    modal.destroy()
                    self.recarregar_interface_modo()
                else:
                    messagebox.showerror("Erro", "Senha incorreta!", parent=modal)
                    entry_pw.delete(0, 'end')
            
            btn_conf = ctk.CTkButton(modal, text="Confirmar", height=35, command=verify, fg_color=paleta["fg"], hover_color=paleta["hover"], corner_radius=8)
            btn_conf.pack(pady=5)
            modal.bind("<Return>", verify)

        btn_dev = ctk.CTkButton(modal, text="👨‍💻 Ativar Modo Desenvolvedor", height=35, corner_radius=8, command=prompt_modo_dev, fg_color=paleta["fg"] if not self.admin_mode else "gray", state="normal" if not self.admin_mode else "disabled")
        btn_dev.pack(pady=5, fill="x", padx=40)

        btn_user = ctk.CTkButton(modal, text="👤 Ativar Modo Usuário", height=35, corner_radius=8, command=set_modo_user, fg_color="#6c757d" if self.admin_mode else "gray", state="normal" if self.admin_mode else "disabled")
        btn_user.pack(pady=5, fill="x", padx=40)

    def recarregar_interface_modo(self):
        self.saved_modo = self.combo_modo.get()
        self.saved_cor = self.combo_cor.get()
        
        self.main_frame.destroy()
        self.setup_main_ui()
        self.aplicar_tema()
        self.main_frame.pack(fill="both", expand=True)
        self.refresh_files()

    # ==========================================
    # INTERFACE DE LOGIN E SENHA (DESIGN PREMIUM)
    # ==========================================
    def setup_login_ui(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.login_inner = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        self.login_inner.place(relx=0.5, rely=0.5, anchor="center")
        
        paleta = self.cores_destaque[self.saved_cor if hasattr(self, 'saved_cor') else "Azul"]
        
        self.login_card = ctk.CTkFrame(self.login_inner, corner_radius=20, border_width=2, border_color=paleta["fg"])
        self.login_card.pack(padx=20, pady=20, ipadx=20, ipady=15)
        
        try:
            img_path = obter_caminho("assets/nuvem.png")
            img_original = Image.open(img_path)
            self.img_logo_login = ctk.CTkImage(light_image=img_original, dark_image=img_original, size=(130, 56))
            lbl_logo = ctk.CTkLabel(self.login_card, image=self.img_logo_login, text="")
            lbl_logo.pack(pady=(15, 5))
        except Exception:
            lbl_icon = ctk.CTkLabel(self.login_card, text="☁️", font=("Segoe UI", 45))
            lbl_icon.pack(pady=(15, 5))

        lbl_login_title = ctk.CTkLabel(self.login_card, text="INTEGRAÇÃO NUVEM", font=("Segoe UI Black", 18), text_color=paleta["fg"])
        lbl_login_title.pack(pady=(0, 0))
        
        lbl_sub = ctk.CTkLabel(self.login_card, text="Autentique-se para acessar o Cloud Ilimitado", font=("Segoe UI", 11), text_color=("gray50", "gray70"))
        lbl_sub.pack(pady=(0, 20))

        form_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=30)

        lbl_tel = ctk.CTkLabel(form_frame, text="Número do Telegram", font=("Segoe UI", 11, "bold"))
        lbl_tel.pack(anchor="w", padx=4)
        
        self.entry_phone = ctk.CTkEntry(form_frame, placeholder_text="Ex: +5511999999999", width=280, height=40, corner_radius=8, font=("Segoe UI", 14))
        self.entry_phone.pack(pady=(0, 10))
        self.entry_phone.insert(0, "+5521997003910")
        self.entry_phone.bind("<Return>", lambda e: self.request_code_ui())

        self.btn_send_code = ctk.CTkButton(form_frame, text="📨 Solicitar Código", command=self.request_code_ui, width=280, height=40, corner_radius=8, font=("Segoe UI", 13, "bold"), fg_color=paleta["fg"], hover_color=paleta["hover"])
        self.btn_send_code.pack(pady=(0, 15))

        div = ctk.CTkFrame(form_frame, height=2, fg_color=("#E5E5E5", "#333333"))
        div.pack(fill="x", pady=(5, 15), padx=10)

        lbl_cod = ctk.CTkLabel(form_frame, text="Código de Verificação", font=("Segoe UI", 11, "bold"))
        lbl_cod.pack(anchor="w", padx=4)

        self.entry_code = ctk.CTkEntry(form_frame, placeholder_text="---", width=280, height=40, state="disabled", corner_radius=8, font=("Segoe UI", 16, "bold"), justify="center")
        self.entry_code.pack(pady=(0, 10))
        self.entry_code.bind("<Return>", lambda e: self.confirm_code_ui())

        self.btn_confirm_code = ctk.CTkButton(form_frame, text="✅ Confirmar Acesso", command=self.confirm_code_ui, state="disabled", width=280, height=40, corner_radius=8, font=("Segoe UI", 13, "bold"), fg_color="#28a745", hover_color="#218838")
        self.btn_confirm_code.pack(pady=(0, 15))

        self.lbl_login_status = ctk.CTkLabel(self.login_card, text="Aguardando ação...", font=("Segoe UI", 11), text_color=("gray50", "gray70"))
        self.lbl_login_status.pack(pady=(0, 15))

        self.btn_voltar_login = ctk.CTkButton(self.login_card, text="⬅️ Voltar ao App Principal", command=self.voltar_para_principal, width=280, height=35, corner_radius=8, fg_color="transparent", border_width=1, text_color=("gray40", "gray80"), border_color=("#CCCCCC", "#555555"), hover_color=("#F0F0F0", "#333333"))
        self.btn_voltar_login.pack(pady=(0, 20), padx=30)

    def setup_senha_mestra_ui(self):
        self.senha_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lbl_fundo_acesso = ctk.CTkLabel(self.senha_frame, text="", fg_color="#000000")
        self.lbl_fundo_acesso.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.senha_inner = ctk.CTkFrame(self.senha_frame, fg_color="transparent")
        self.senha_inner.pack(expand=True)
        self.senha_card = ctk.CTkFrame(self.senha_inner, corner_radius=15, border_width=1, border_color="#333333")
        self.senha_card.pack(padx=20, pady=20, ipadx=40, ipady=30)
        lbl_icon = ctk.CTkLabel(self.senha_card, text="🔒", font=("Segoe UI", 40))
        lbl_icon.pack(pady=(0, 10))
        lbl_title = ctk.CTkLabel(self.senha_card, text="MODO DE ACESSO", font=("Segoe UI Black", 18))
        lbl_title.pack(pady=(0, 20))
        self.btn_inserir_senha = ctk.CTkButton(self.senha_card, text="🔑 Inserir Senha Mestra", width=260, height=40, corner_radius=8, command=self.mostrar_campo_senha)
        self.btn_inserir_senha.pack(pady=8)
        self.btn_pular_senha = ctk.CTkButton(self.senha_card, text="⏭️ Pular (Apenas Download)", width=260, height=40, corner_radius=8, fg_color="#6c757d", hover_color="#5a6268", command=self.acesso_leitura)
        self.btn_pular_senha.pack(pady=8)
        self.senha_entry_frame = ctk.CTkFrame(self.senha_card, fg_color="transparent")
        self.entry_senha = ctk.CTkEntry(self.senha_entry_frame, placeholder_text="Digite a senha mestra", show="*", width=260, height=40, corner_radius=8)
        self.entry_senha.pack(pady=(10, 5))
        frame_botoes_senha = ctk.CTkFrame(self.senha_entry_frame, fg_color="transparent")
        frame_botoes_senha.pack(pady=5)
        self.btn_voltar_senha = ctk.CTkButton(frame_botoes_senha, text="⬅️ Voltar", width=125, height=40, corner_radius=8, fg_color="#6c757d", hover_color="#5a6268", command=self.ocultar_campo_senha)
        self.btn_voltar_senha.pack(side="left", padx=(0, 5))
        self.btn_confirmar_senha = ctk.CTkButton(frame_botoes_senha, text="✅ Confirmar", width=125, height=40, corner_radius=8, command=self.verificar_senha)
        self.btn_confirmar_senha.pack(side="left", padx=(5, 0))
        self.entry_senha.bind("<Return>", lambda e: self.verificar_senha())

    def mostrar_tela_senha_mestra(self):
        if hasattr(self, 'login_frame'):
            self.login_frame.pack_forget()
        self.senha_frame.pack(fill="both", expand=True)
        self.bloqueio_manager.iniciar_apresentacao(self.lbl_fundo_acesso)

    def mostrar_campo_senha(self):
        self.btn_inserir_senha.pack_forget()
        self.btn_pular_senha.pack_forget()
        self.senha_entry_frame.pack(pady=10)
        self.entry_senha.focus()

    def ocultar_campo_senha(self):
        self.senha_entry_frame.pack_forget()
        self.entry_senha.delete(0, 'end')
        self.btn_inserir_senha.pack(pady=8)
        self.btn_pular_senha.pack(pady=8)

    def acesso_leitura(self):
        self.admin_mode = False
        self.primeiro_acesso = False 
        self.salvar_configuracoes()
        self.iniciar_tela_principal()

    def verificar_senha(self):
        senha_digitada = self.entry_senha.get()
        hash_digitado = hashlib.sha256(senha_digitada.encode()).hexdigest()
        hash_correto = hashlib.sha256("admin@123!".encode()).hexdigest()
        if hash_digitado == hash_correto:
            self.admin_mode = True
            self.primeiro_acesso = False 
            self.salvar_configuracoes()
            self.iniciar_tela_principal()
        else:
            messagebox.showerror("Erro", "Senha Mestra incorreta!")
            self.entry_senha.delete(0, 'end')

    def iniciar_tela_principal(self):
        if hasattr(self, 'senha_frame'):
            self.bloqueio_manager.parar_apresentacao()
            self.senha_frame.pack_forget()
        if hasattr(self, 'login_frame'):
            self.login_frame.pack_forget()
        self.setup_main_ui()
        self.aplicar_tema()
        self.main_frame.pack(fill="both", expand=True)
        self.update() 
        modo_txt = "Desenvolvedor (Full)" if self.admin_mode else "Usuário (Leitura)"
        self.log(f"[SISTEMA] Autenticação concluída com sucesso.")
        self.log(f"[SISTEMA] Modo de Acesso: {modo_txt}")
        self.log("[SISTEMA] Sincronizando com a Nuvem...")
        self.refresh_files()

    # ==========================================
    # INTERFACE PRINCIPAL (LUPA & BUSCA GERAL)
    # ==========================================
    def setup_main_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=24)
        self.top_bar.pack(fill="x", padx=15, pady=(2, 0))
        
        # --- NOVO BOTÃO VOLTAR NA INTERFACE PRINCIPAL ---
        self.btn_voltar_main = ctk.CTkButton(self.top_bar, text="⬅️ Voltar ao Pack Socin", width=150, height=28, fg_color="transparent", hover_color="#cccccc", text_color=("black", "white"), font=("Segoe UI", 12, "bold"), command=self.voltar_para_principal)
        self.btn_voltar_main.pack(side="left")
        
        self.btn_engrenagem = ctk.CTkButton(self.top_bar, text="⚙️", width=28, height=28, fg_color="transparent", hover_color="#cccccc", text_color=("black", "white"), font=("Segoe UI", 15), command=self.abrir_modal_alternar_modo)
        self.btn_engrenagem.pack(side="right")

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(0, 0))
        
        self.logo_top_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.logo_top_frame.pack(fill="x")
        
        try:
            img_path = obter_caminho("assets/nuvem.png")
            img_original = Image.open(img_path)
            img_brilhante = ImageEnhance.Brightness(img_original).enhance(1.6)
            self.img_normal = ctk.CTkImage(light_image=img_original, dark_image=img_original, size=(90, 38))
            self.img_glow = ctk.CTkImage(light_image=img_brilhante, dark_image=img_brilhante, size=(90, 38))
            
            self.frame_logo = ctk.CTkFrame(self.logo_top_frame, border_width=1, corner_radius=8)
            self.frame_logo.pack(side="top", anchor="center") 
            self.lbl_logo = ctk.CTkLabel(self.frame_logo, image=self.img_normal, text="", cursor="hand2")
            self.lbl_logo.pack(padx=10, pady=2)
            self.lbl_logo.bind("<Enter>", lambda e: self.lbl_logo.configure(image=self.img_glow))
            self.lbl_logo.bind("<Leave>", lambda e: self.lbl_logo.configure(image=self.img_normal))
            self.lbl_logo.bind("<Button-1>", self.mostrar_assinatura)
        except Exception:
            self.frame_logo = None

        self.controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", pady=(2, 0))
        
        left_ctrl = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        left_ctrl.pack(side="left")
        ctk.CTkLabel(left_ctrl, text="Modo Visual:", font=("Segoe UI", 10, "bold"), text_color="gray").pack(anchor="w", pady=(0, 1))
        self.combo_modo = ctk.CTkComboBox(left_ctrl, values=["Light", "Dark"], width=90, height=26, command=self.mudar_configuracoes_tema, font=("Segoe UI", 11, "bold"))
        self.combo_modo.pack()
        self.combo_modo.set(self.saved_modo)

        right_ctrl = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        right_ctrl.pack(side="right")
        ctk.CTkLabel(right_ctrl, text="Cor de Destaque:", font=("Segoe UI", 10, "bold"), text_color="gray").pack(anchor="e", pady=(0, 1))
        self.combo_cor = ctk.CTkComboBox(right_ctrl, values=list(self.cores_destaque.keys()), width=105, height=26, command=self.mudar_configuracoes_tema, font=("Segoe UI", 11, "bold"))
        self.combo_cor.pack()
        self.combo_cor.set(self.saved_cor)

        self.lbl_titulo_app = ctk.CTkLabel(self.controls_frame, text="TELEGRAM CLOUD", font=("Segoe UI Black", 17))
        self.lbl_titulo_app.place(relx=0.5, rely=0.5, anchor="center")

        self.frame_central = ctk.CTkFrame(self.main_frame, corner_radius=12, border_width=1)
        self.frame_central.pack(padx=20, pady=(4, 6), fill="both", expand=True)

        self.bottom_fixed_frame = ctk.CTkFrame(self.frame_central, fg_color="transparent")
        self.bottom_fixed_frame.pack(side="bottom", fill="x", padx=15, pady=(2, 6))

        self.action_frame = ctk.CTkFrame(self.bottom_fixed_frame, fg_color="transparent")
        self.action_frame.pack(side="bottom", fill="x")

        if self.admin_mode:
            self.btn_abrir_gerenciador = ctk.CTkButton(self.action_frame, text="⚙️ Gerenciamento da Nuvem (Pastas e Arquivos)", font=("Segoe UI", 11, "bold"), height=26, fg_color="transparent", border_width=1, corner_radius=8, command=self.abrir_gerenciador_nuvem)
            self.btn_abrir_gerenciador.pack(side="bottom", fill="x", pady=(2, 0))

        self.btn_armazenamento = ctk.CTkButton(self.action_frame, text="☁️ Calculando espaço...", font=("Segoe UI", 12, "bold"), corner_radius=8, command=self.mostrar_popup_armazenamento, height=26)
        self.btn_armazenamento.pack(side="bottom", fill="x", pady=2)

        self.lbl_status = ctk.CTkButton(self.action_frame, text="⏳ Pronto para iniciar", height=26, state="disabled", corner_radius=8, font=("Segoe UI", 12, "bold"))
        self.lbl_status.pack(side="bottom", fill="x", pady=2)

        self.terminal_wrapper = ctk.CTkFrame(self.bottom_fixed_frame, corner_radius=8, border_width=1)
        self.terminal_wrapper.pack(side="bottom", fill="x", pady=(0, 2))
        
        terminal_header = ctk.CTkFrame(self.terminal_wrapper, fg_color="transparent", height=18)
        terminal_header.pack(fill="x", padx=8, pady=(2, 0))
        ctk.CTkLabel(terminal_header, text=">_ Terminal de Eventos", font=("Segoe UI", 9, "bold"), text_color="gray").pack(side="left")
        
        self.logs = ctk.CTkTextbox(self.terminal_wrapper, height=44, corner_radius=6, border_width=0, font=("Cascadia Code", 10) if os.name == 'nt' else ("Courier New", 10))
        self.logs.pack(padx=8, pady=(0, 3), fill="x")
        self.logs.configure(state="disabled")

        self.progresso_frame = ctk.CTkFrame(self.bottom_fixed_frame, fg_color="transparent")
        self.lbl_action_status = ctk.CTkLabel(self.progresso_frame, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_action_status.pack(pady=(0, 1))
        
        frame_bar_btn = ctk.CTkFrame(self.progresso_frame, fg_color="transparent")
        frame_bar_btn.pack(fill="x")
        self.progressbar = ctk.CTkProgressBar(frame_bar_btn, height=10, corner_radius=5, mode="determinate")
        self.progressbar.set(0)
        self.progressbar.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.btn_cancelar = ctk.CTkButton(frame_bar_btn, text="❌ CANCELAR", font=("Segoe UI", 10, "bold"), width=100, height=26, fg_color="#dc3545", hover_color="#c82333", corner_radius=6, command=self.acionar_cancelamento)
        self.btn_cancelar.pack(side="right")
        self.lbl_metrics = ctk.CTkLabel(self.progresso_frame, text="", font=("Segoe UI", 9, "bold"), text_color="gray")
        self.lbl_metrics.pack(pady=(1, 0))

        # -----------------------------------------------
        # TABVIEW ELÁSTICA SUPERIOR
        # -----------------------------------------------
        self.tabview = ctk.CTkTabview(self.frame_central, corner_radius=10) 
        self.tabview.pack(side="top", fill="both", expand=True, padx=15, pady=(2, 2))
        
        if self.admin_mode:
            self.tabview.add("Upload")
            
            self.tab_up_top = ctk.CTkFrame(self.tabview.tab("Upload"), fg_color="transparent")
            self.tab_up_top.pack(side="top", fill="x")

            self.header_up_frame = ctk.CTkFrame(self.tab_up_top, fg_color="transparent")
            self.header_up_frame.pack(side="top", fill="x", padx=50, pady=(8, 2))

            self.lbl_pasta_up = ctk.CTkLabel(self.header_up_frame, text="P A S T A   D E   D E S T I N O", font=("Segoe UI", 11, "bold"), text_color="gray")
            self.lbl_pasta_up.pack(side="left", expand=True, padx=(26, 0))

            self.entry_busca_up = ctk.CTkEntry(self.header_up_frame, placeholder_text="Buscar pasta/subpasta...", height=26, font=("Segoe UI", 11))
            self.entry_busca_up.bind("<KeyRelease>", lambda e: self.ao_digitar_busca('up'))

            self.btn_lupa_up = ctk.CTkButton(self.header_up_frame, text="🔍", width=26, height=26, fg_color="transparent", hover_color="#cccccc", text_color=("black", "white"), font=("Segoe UI", 14), command=lambda: self.alternar_busca('up'))
            self.btn_lupa_up.pack(side="right")

            self.upload_controls_frame = ctk.CTkFrame(self.tab_up_top, fg_color="transparent")
            self.upload_controls_frame.pack(side="top", fill="both", expand=True)

            frame_up = ctk.CTkFrame(self.upload_controls_frame, height=26, fg_color="transparent")
            frame_up.pack_propagate(False)
            frame_up.pack(side="top", fill="x", padx=50, pady=(0, 10))
            self.combo_pasta_up = ttk.Combobox(frame_up, values=[], height=10, state="readonly", cursor="hand2")
            self.combo_pasta_up.pack(fill="both", expand=True)
            self.combo_pasta_up.bind("<<ComboboxSelected>>", lambda e: self.ao_selecionar_combobox('up'))
            
            self.btn_select = ctk.CTkButton(self.upload_controls_frame, text="📂 SELECIONAR ARQUIVOS MÚLTIPLOS", font=("Segoe UI", 12, "bold"), command=self.select_file, height=36, corner_radius=8)
            self.btn_select.pack(side="top", fill="x", padx=50, pady=5)
            self.lbl_file = ctk.CTkLabel(self.upload_controls_frame, text="0 arquivo(s) selecionado(s)", text_color="gray", font=("Segoe UI", 11, "bold"))
            self.lbl_file.pack(side="top", pady=2)

            self.scroll_upload = ctk.CTkScrollableFrame(self.tabview.tab("Upload"), corner_radius=6)

        self.tabview.add("Download")
        
        self.frame_botoes_down = ctk.CTkFrame(self.tabview.tab("Download"), fg_color="transparent")
        self.frame_botoes_down.pack(side="bottom", pady=(1, 5))
        
        self.btn_refresh = ctk.CTkButton(self.frame_botoes_down, text="🔍 BUSCAR", font=("Segoe UI", 11, "bold"), command=self.refresh_files, width=90, height=28, corner_radius=8)
        self.btn_refresh.pack(side="left", padx=4)
        self.btn_select_all = ctk.CTkButton(self.frame_botoes_down, text="✅ TUDO", font=("Segoe UI", 11, "bold"), command=self.selecionar_tudo_download, width=75, height=28, corner_radius=8)
        self.btn_select_all.pack(side="left", padx=4)
        self.btn_download = ctk.CTkButton(self.frame_botoes_down, text="⬇️ BAIXAR", font=("Segoe UI", 12, "bold"), command=self.start_download, width=110, height=28, corner_radius=8)
        self.btn_download.pack(side="left", padx=4)

        self.lbl_down_count = ctk.CTkLabel(self.tabview.tab("Download"), text="0 arquivo(s) selecionado(s)", text_color="gray", font=("Segoe UI", 11, "bold"))
        self.lbl_down_count.pack(side="bottom", pady=(2, 2))

        self.tab_down_top = ctk.CTkFrame(self.tabview.tab("Download"), fg_color="transparent")
        self.tab_down_top.pack(side="top", fill="x")

        self.header_down_frame = ctk.CTkFrame(self.tab_down_top, fg_color="transparent")
        self.header_down_frame.pack(side="top", fill="x", padx=20, pady=(2, 0))

        self.lbl_pasta_down = ctk.CTkLabel(self.header_down_frame, text="F I L T R A R   P O R   P A S T A", font=("Segoe UI", 11, "bold"), text_color="gray")
        self.lbl_pasta_down.pack(side="left", expand=True, padx=(26, 0))

        self.entry_busca_down = ctk.CTkEntry(self.header_down_frame, placeholder_text="Buscar pasta/subpasta...", height=26, font=("Segoe UI", 11))
        self.entry_busca_down.bind("<KeyRelease>", lambda e: self.ao_digitar_busca('down'))

        self.btn_lupa_down = ctk.CTkButton(self.header_down_frame, text="🔍", width=26, height=26, fg_color="transparent", hover_color="#cccccc", text_color=("black", "white"), font=("Segoe UI", 14), command=lambda: self.alternar_busca('down'))
        self.btn_lupa_down.pack(side="right")
        
        self.frame_down = ctk.CTkFrame(self.tab_down_top, height=26, fg_color="transparent")
        self.frame_down.pack_propagate(False)
        self.frame_down.pack(side="top", fill="x", padx=20, pady=(0, 2))
        self.combo_pasta_down = ttk.Combobox(self.frame_down, values=[], height=10, state="readonly", cursor="hand2")
        self.combo_pasta_down.pack(fill="both", expand=True)
        self.combo_pasta_down.bind("<<ComboboxSelected>>", lambda e: self.ao_selecionar_combobox('down'))

        self.scroll_download = ctk.CTkScrollableFrame(self.tabview.tab("Download"), corner_radius=6)
        self.scroll_download.pack(side="top", fill="both", expand=True, padx=20, pady=(2, 2))
        self.download_checkboxes = []

        self.construir_mapa_pastas()
        self.atualizar_dropdowns()

    def aplicar_tema(self, *args):
        modo = self.combo_modo.get() if hasattr(self, 'combo_modo') else self.saved_modo
        cor = self.combo_cor.get() if hasattr(self, 'combo_cor') else self.saved_cor
        ctk.set_appearance_mode(modo)
        paleta = self.cores_destaque[cor]

        try:
            if hasattr(self, 'labels_tamanho_ui'):
                for lbl in self.labels_tamanho_ui:
                    if lbl.winfo_exists():
                        lbl.configure(text_color=paleta["fg"])
        except: pass

        try:
            if modo == "Light":
                self.configure(fg_color="#E8ECEF")
                if hasattr(self, 'login_card') and self.login_card.winfo_exists(): self.login_card.configure(fg_color="#FFFFFF", border_color=paleta["fg"], border_width=2)
                if hasattr(self, 'senha_card') and self.senha_card.winfo_exists(): self.senha_card.configure(fg_color="#FFFFFF", border_color="#D1D1D1", border_width=1)
                if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                    self.tabview.configure(border_color="#D1D1D1")
                    self.terminal_wrapper.configure(fg_color="#FFFFFF", border_color="#D1D1D1")
                    self.logs.configure(fg_color="#F4F5F7", text_color="#121212")
                    self.scroll_download.configure(fg_color="#F4F5F7", border_width=1, border_color="#D1D1D1")
                    if hasattr(self, 'scroll_upload') and self.scroll_upload.winfo_exists(): self.scroll_upload.configure(fg_color="#F4F5F7", border_width=1, border_color="#D1D1D1")
                    self.frame_central.configure(fg_color="#FFFFFF", border_color="#D1D1D1")
                    if hasattr(self, 'frame_logo') and self.frame_logo: self.frame_logo.configure(fg_color="#FFFFFF", border_color="#D1D1D1")
                
                if hasattr(self, 'lbl_login_status'): self.lbl_login_status.configure(text_color="gray50")
                bg_status, fg_status = "#F8F9FA", "#888888" 
                
                self.style.configure("TCombobox", fieldbackground="#FFFFFF", background="#E8ECEF", foreground="#000000", bordercolor="#D1D1D1", arrowcolor="#000000")
                self.option_add('*TCombobox*Listbox.background', '#FFFFFF')
                self.option_add('*TCombobox*Listbox.foreground', '#000000')
                self.option_add('*TCombobox*Listbox.selectBackground', paleta["fg"])
                self.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')
                self.option_add('*TCombobox*Listbox.font', ("Segoe UI", 11))
            else:
                self.configure(fg_color="#0F0F0F")
                if hasattr(self, 'login_card') and self.login_card.winfo_exists(): self.login_card.configure(fg_color="#1A1A1A", border_color=paleta["fg"], border_width=2)
                if hasattr(self, 'senha_card') and self.senha_card.winfo_exists(): self.senha_card.configure(fg_color="#1A1A1A", border_color="#333333", border_width=1)
                if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
                    self.tabview.configure(border_color="#333333")
                    self.terminal_wrapper.configure(fg_color="#1A1A1A", border_color="#333333")
                    self.logs.configure(fg_color="#121212", text_color="#FFFFFF")
                    self.scroll_download.configure(fg_color="#141414", border_width=1, border_color="#333333")
                    if hasattr(self, 'scroll_upload') and self.scroll_upload.winfo_exists(): self.scroll_upload.configure(fg_color="#141414", border_width=1, border_color="#333333")
                    self.frame_central.configure(fg_color="#1E1E1E", border_color="#333333")
                    if hasattr(self, 'frame_logo') and self.frame_logo: self.frame_logo.configure(fg_color="#1E1E1E", border_color="#333333")
                
                if hasattr(self, 'lbl_login_status'): self.lbl_login_status.configure(text_color="gray70")
                bg_status, fg_status = "#252525", "#AAAAAA"
                
                self.style.configure("TCombobox", fieldbackground="#1A1A1A", background="#0F0F0F", foreground="#FFFFFF", bordercolor="#333333", arrowcolor="#FFFFFF")
                self.option_add('*TCombobox*Listbox.background', '#1A1A1A')
                self.option_add('*TCombobox*Listbox.foreground', '#FFFFFF')
                self.option_add('*TCombobox*Listbox.selectBackground', paleta["fg"])
                self.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')
                self.option_add('*TCombobox*Listbox.font', ("Segoe UI", 11))
        except: pass

        botoes = []
        if hasattr(self, 'btn_send_code'): botoes.append(self.btn_send_code)
        if hasattr(self, 'btn_confirm_code'): botoes.append(self.btn_confirm_code)
        if hasattr(self, 'btn_inserir_senha'): botoes.append(self.btn_inserir_senha)
        if hasattr(self, 'btn_confirmar_senha'): botoes.append(self.btn_confirmar_senha)
        
        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
            if hasattr(self, 'btn_select') and self.btn_select.winfo_exists(): botoes.append(self.btn_select)
            if hasattr(self, 'btn_refresh'): botoes.extend([self.btn_refresh, self.btn_download, self.btn_select_all])
            
        for btn in botoes: 
            if hasattr(btn, 'configure') and btn.winfo_exists() and btn.cget("text") not in ["✅ Confirmar Acesso", "⬅️ Voltar ao App Principal"]: 
                btn.configure(fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            
        combos = []
        if hasattr(self, 'combo_modo'): combos.extend([self.combo_modo, self.combo_cor])
        for cb in combos: cb.configure(border_color=paleta["fg"], button_color=paleta["fg"], button_hover_color=paleta["hover"])
        
        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
            self.progressbar.configure(progress_color=paleta["fg"])
            self.btn_armazenamento.configure(fg_color=paleta["light_bg"] if modo == "Light" else paleta["dark_bg"], border_width=1, border_color=paleta["fg"], text_color=paleta["fg"], hover_color=paleta["light_bg"] if modo == "Light" else paleta["dark_bg"])
            if hasattr(self, 'btn_abrir_gerenciador') and self.btn_abrir_gerenciador.winfo_exists():
                self.btn_abrir_gerenciador.configure(fg_color=paleta["light_bg"] if modo == "Light" else paleta["dark_bg"], border_width=1, border_color=paleta["fg"], text_color=paleta["fg"], hover_color=paleta["light_bg"] if modo == "Light" else paleta["dark_bg"])
            
            self.btn_engrenagem.configure(hover_color="#e0e0e0" if modo == "Light" else "#333333", text_color="black" if modo == "Light" else "white")
            if hasattr(self, 'btn_voltar_main') and self.btn_voltar_main.winfo_exists():
                self.btn_voltar_main.configure(hover_color="#e0e0e0" if modo == "Light" else "#333333", text_color="black" if modo == "Light" else "white")
                
            if hasattr(self, 'btn_lupa_up') and self.btn_lupa_up.winfo_exists():
                self.btn_lupa_up.configure(hover_color="#e0e0e0" if modo == "Light" else "#333333", text_color="black" if modo == "Light" else "white")
                self.entry_busca_up.configure(fg_color="#FFFFFF" if modo == "Light" else "#1A1A1A", border_color=paleta["fg"])
            if hasattr(self, 'btn_lupa_down') and self.btn_lupa_down.winfo_exists():
                self.btn_lupa_down.configure(hover_color="#e0e0e0" if modo == "Light" else "#333333", text_color="black" if modo == "Light" else "white")
                self.entry_busca_down.configure(fg_color="#FFFFFF" if modo == "Light" else "#1A1A1A", border_color=paleta["fg"])

            if self.lbl_status.cget("text") == "⏳ Pronto para iniciar": 
                self.mudar_status("⏳ Pronto para iniciar", bg_status, fg_status)
            
            if hasattr(self, 'download_checkboxes'):
                for var, cb_widget, arq_obj, pasta_arq in self.download_checkboxes:
                    cb_widget.configure(fg_color=paleta["fg"], hover_color=paleta["hover"])
            self.atualizar_contador_download()

    def mudar_status(self, mensagem, cor_fundo, cor_texto): self.after(0, lambda: self.lbl_status.configure(text=mensagem, fg_color=cor_fundo, text_color=cor_texto))
    def log(self, mensagem): self.after(0, lambda: self._inserir_log(mensagem))
    def _inserir_log(self, mensagem):
        if hasattr(self, 'logs') and self.logs.winfo_exists():
            self.logs.configure(state="normal")
            self.logs.insert("end", f"{mensagem}\n")
            self.logs.see("end")
            self.logs.configure(state="disabled")

    # ==========================================
    # LÓGICA DE CANCELAMENTO E PROGRESSO
    # ==========================================
    def acionar_cancelamento(self):
        self.flag_cancelar = True
        self.btn_cancelar.configure(state="disabled", text="CANCELANDO...")
        self.mudar_status("⚠️ Cancelamento solicitado. Interrompendo...", "#ffc107", "#000000")
        self.log("[SISTEMA] Interrompendo comunicação com o servidor...")

    def get_progress_callback(self, action_name, filename):
        start_time = time.time()
        def progress_callback(current, total):
            if self.flag_cancelar: raise Exception("CANCELADO_PELO_USUARIO")

            now = time.time()
            elapsed = now - start_time
            if elapsed == 0: elapsed = 0.001
            speed_bytes = current / elapsed
            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            speed_str = f"{speed_bytes / (1024 * 1024):.1f} MB/s" if speed_bytes >= 1024 * 1024 else f"{speed_bytes / 1024:.1f} KB/s"
            
            eta_seconds = int((total - current) / speed_bytes if speed_bytes > 0 else 0)
            if eta_seconds >= 60:
                m = eta_seconds // 60
                s = eta_seconds % 60
                eta_str = f"{m}m {s}s restantes"
            else:
                eta_str = f"{eta_seconds}s restantes"
                
            progress_float = current / total
            self.after(0, lambda p=progress_float: self.update_metrics_ui(p))
            metrics_txt = f"{speed_str} - {current_mb:.1f} MB de {total_mb:.1f} MB, {eta_str}"
            self.after(0, lambda m=metrics_txt: self.lbl_metrics.configure(text=m))
            
            lock_stats_txt = f"{speed_str} - {current_mb:.1f}MB / {total_mb:.1f}MB, {eta_str}"
            self.after(0, lambda n=filename, p=progress_float, m=lock_stats_txt: self.bloqueio_manager.atualizar_status(n, p, m))
        return progress_callback

    def update_metrics_ui(self, progress_float):
        if hasattr(self, 'progressbar') and self.progressbar.winfo_exists():
            self.progressbar.set(progress_float)

    # ==========================================
    # LÓGICA DE LOGIN & ASYNCIO
    # ==========================================
    def request_code_ui(self):
        self.phone_number = self.entry_phone.get().strip()
        if not self.phone_number: return
        self.btn_send_code.configure(state="disabled")
        asyncio.run_coroutine_threadsafe(self.send_code_async(), self.async_loop)

    def confirm_code_ui(self):
        code = self.entry_code.get().strip()
        if not code: return
        self.btn_confirm_code.configure(state="disabled")
        asyncio.run_coroutine_threadsafe(self.sign_in_async(code), self.async_loop)

    def start_async_thread(self):
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()

    def run_async_loop(self):
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self.async_loop.create_task(self.check_auth_status())
        self.async_loop.run_forever()

    async def check_auth_status(self):
        await self.client.connect()
        if await self.client.is_user_authorized():
            if self.primeiro_acesso:
                self.after(0, self.mostrar_tela_senha_mestra)
            else:
                self.admin_mode = False 
                self.after(0, self.iniciar_tela_principal)
        else:
            self.after(0, lambda: self.login_frame.pack(fill="both", expand=True, padx=20, pady=20))

    async def send_code_async(self):
        try:
            await self.client.send_code_request(self.phone_number)
            self.after(0, lambda: self.entry_code.configure(state="normal"))
            self.after(0, lambda: self.btn_confirm_code.configure(state="normal"))
            self.after(0, lambda: self.lbl_login_status.configure(text="Código enviado! Verifique seu app."))
        except Exception as e:
            self.after(0, lambda: self.lbl_login_status.configure(text=f"Erro: {str(e)}"))
            self.after(0, lambda: self.btn_send_code.configure(state="normal"))

    async def sign_in_async(self, code):
        try:
            await self.client.sign_in(self.phone_number, code)
            self.after(0, self.mostrar_tela_senha_mestra)
        except Exception as e:
            self.after(0, lambda: self.lbl_login_status.configure(text=f"Erro: {str(e)}"))
            self.after(0, lambda: self.btn_confirm_code.configure(state="normal"))

    # ==========================================
    # LÓGICA DE UPLOAD MÚLTIPLO
    # ==========================================
    def select_file(self):
        filepaths = filedialog.askopenfilenames(title="Selecione um ou mais arquivos")
        if not filepaths: return
        texto_lbl = f"{len(filepaths)} arquivo(s) selecionado(s) para Upload" if len(filepaths) > 1 else f"1 arquivo selecionado para Upload"
        self.lbl_file.configure(text=texto_lbl, text_color=self.cores_destaque[self.combo_cor.get()]["fg"])
        if self.async_loop: asyncio.run_coroutine_threadsafe(self.perform_multiple_uploads(filepaths), self.async_loop)

    async def perform_multiple_uploads(self, filepaths):
        pasta_backend = self.map_ui_to_backend.get(self.combo_pasta_up.get())
        if not pasta_backend: return

        self.flag_cancelar = False
        self.after(0, lambda: self.btn_select.configure(state="disabled"))
        
        self.after(0, lambda: self.progresso_frame.pack(side="bottom", fill="x", padx=15, pady=(2, 2), before=self.terminal_wrapper))
        self.after(0, lambda: self.btn_cancelar.configure(state="normal", text="❌ CANCELAR"))
        
        self.is_downloading = True
        self.historico_arquivos.clear()
        self.total_arquivos_sessao = len(filepaths)
        self.after(0, lambda: self.bloqueio_manager.sincronizar_painel_topo())
        
        cor_tema = self.cores_destaque[self.combo_cor.get()]["fg"]
        self.mudar_status("⬆️ Realizando Uploads...", cor_tema, "#FFFFFF")
        
        try:
            for idx, filepath in enumerate(filepaths, 1):
                if self.flag_cancelar: break
                filename = os.path.basename(filepath)
                self.historico_arquivos.append(filename)
                
                self.after(0, lambda f=filename, i=idx: self.lbl_action_status.configure(text=f"Enviando ({i}/{len(filepaths)}): {f}"))
                self.log(f"[UPLOAD] [{idx}/{len(filepaths)}] Enviando '{filename}'")
                self.after(0, lambda n=filename: self.bloqueio_manager.adicionar_arquivo_painel(n, concluido=False))
                self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa(f"Enviando: {filename}"))
                
                try:
                    await self.client.send_file(
                        'me', filepath, caption=f"{pasta_backend} \nEnviado via Fiuza Cloud", 
                        progress_callback=self.get_progress_callback("Upload", filename)
                    )
                    self.after(0, lambda n=filename: self.bloqueio_manager.adicionar_arquivo_painel(n, concluido=True))
                    self.log(f"[UPLOAD] [{idx}/{len(filepaths)}] Sucesso!")
                except Exception as e:
                    if "CANCELADO_PELO_USUARIO" in str(e):
                        self.log(f"[SISTEMA] Upload de '{filename}' interrompido pelo usuário.")
                        break 
                    else: raise e 
                        
            if self.flag_cancelar: self.mudar_status("❌ Operação Cancelada!", "#dc3545", "#FFFFFF")
            else: self.mudar_status("✅ Uploads concluídos com sucesso!", cor_tema, "#FFFFFF")
                
            self.after(0, lambda: self.bloqueio_manager.finalizar_painel_topo())
            self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa("Operação finalizada! 🚀", esconder_barra=True))
            await self.fetch_cloud_files()
        except Exception as e:
            self.log(f"[ERRO] Falha no upload: {str(e)}")
            self.mudar_status("❌ Erro no upload", "#dc3545", "#FFFFFF")
        finally:
            self.is_downloading = False
            if hasattr(self, 'btn_select') and self.btn_select.winfo_exists():
                self.after(0, lambda: self.btn_select.configure(state="normal"))
                self.after(0, lambda: self.lbl_file.configure(text="0 arquivo(s) selecionado(s)", text_color="gray"))
            self.after(0, lambda: self.progresso_frame.pack_forget())

    # ==========================================
    # LÓGICA DE DOWNLOAD & BUSCA GERAL
    # ==========================================
    def refresh_files(self):
        if self.async_loop: asyncio.run_coroutine_threadsafe(self.fetch_cloud_files(), self.async_loop)

    async def fetch_cloud_files(self):
        if hasattr(self, 'btn_refresh') and self.btn_refresh.winfo_exists():
            self.after(0, lambda: self.btn_refresh.configure(state="disabled"))
        try:
            temp_pastas = {pasta: [] for pasta in self.pastas_locais}
            houve_alteracao = False
            total_size_bytes = 0
            
            async for msg in self.client.iter_messages('me', limit=500):
                if msg.file:
                    total_size_bytes += msg.file.size
                    nome = msg.file.name or f"arquivo_{msg.id}{msg.file.ext}"
                    pasta_detectada = "#Geral"
                    if msg.text and '#' in msg.text:
                        tags = [t for t in msg.text.split() if t.startswith('#')]
                        if tags: pasta_detectada = tags[0]
                    
                    if pasta_detectada not in temp_pastas:
                        temp_pastas[pasta_detectada] = []
                        if pasta_detectada not in self.pastas_locais: 
                            self.pastas_locais.append(pasta_detectada)
                            houve_alteracao = True
                    
                    size_file = getattr(msg.file, 'size', 0) if msg.file else 0
                    temp_pastas[pasta_detectada].append({"nome": nome, "msg": msg, "size": size_file})

            for pasta in temp_pastas:
                ordem_salva = self.ordem_arquivos.get(pasta, [])
                def get_sort_key(arq_dict):
                    try: return ordem_salva.index(arq_dict["nome"])
                    except ValueError: return 999999
                temp_pastas[pasta].sort(key=get_sort_key)
                self.ordem_arquivos[pasta] = [a["nome"] for a in temp_pastas[pasta]]

            self.pastas_nuvem = temp_pastas
            self.uso_total_bytes = total_size_bytes
            self.after(0, self.atualizar_textos_armazenamento)
            
            if houve_alteracao or True:
                self.salvar_configuracoes()
            
            self.after(0, self.atualizar_dropdowns)
            cor_tema = self.cores_destaque[self.combo_cor.get()]["fg"]
            self.mudar_status("✅ Nuvem sincronizada", cor_tema, "#FFFFFF")
            
            from gerenciador import GerenciadorNuvem
            if hasattr(self, 'gerenciador_manager') and hasattr(self.gerenciador_manager, 'popup_mgr') and self.gerenciador_manager.popup_mgr.winfo_exists():
                self.after(0, self.gerenciador_manager.atualizar_listas_gerenciador)
        except Exception as e:
            self.log(f"[ERRO] Falha na sincronização: {str(e)}")
            self.mudar_status("❌ Erro de Sincronização", "#dc3545", "#FFFFFF")
        finally:
            if hasattr(self, 'btn_refresh') and self.btn_refresh.winfo_exists():
                self.after(0, lambda: self.btn_refresh.configure(state="normal"))

    def filtrar_arquivos_upload(self):
        if not hasattr(self, 'scroll_upload') or not self.scroll_upload.winfo_exists(): return
        for widget in self.scroll_upload.winfo_children(): widget.destroy()
        
        self.labels_tamanho_ui = [lbl for lbl in self.labels_tamanho_ui if lbl.winfo_exists()]
        paleta = self.cores_destaque[self.combo_cor.get() if hasattr(self, 'combo_cor') else self.saved_cor]
        termo = self.termo_busca_up
        
        if self.estado_busca_up == 1:
            if not termo:
                ctk.CTkLabel(self.scroll_upload, text="(Digite algo para buscar pastas ou subpastas em toda a nuvem)", text_color="gray").pack(pady=10)
            else:
                pastas_encontradas = []
                for item in self.lista_formatada:
                    backend_val = self.map_ui_to_backend[item]
                    if termo in item.lower() or termo in backend_val.lower():
                        pastas_encontradas.append(item)
                
                if not pastas_encontradas:
                    ctk.CTkLabel(self.scroll_upload, text="(Nenhuma pasta ou subpasta encontrada com esse nome)", text_color="gray").pack(pady=10)
                else:
                    for item in pastas_encontradas:
                        btn = ctk.CTkButton(self.scroll_upload, text=item, anchor="w", fg_color="transparent", text_color=("black", "white"), hover_color=paleta["hover"], command=lambda i=item: self.selecionar_pasta_busca('up', i))
                        btn.pack(fill="x", pady=2, padx=5)

        elif self.estado_busca_up == 2:
            if not termo:
                ctk.CTkLabel(self.scroll_upload, text="(Digite algo para buscar arquivos em toda a nuvem)", text_color="gray").pack(pady=10)
            else:
                arquivos_encontrados = []
                for pasta, arquivos in self.pastas_nuvem.items():
                    for arq in arquivos:
                        if termo in arq["nome"].lower():
                            arquivos_encontrados.append((pasta, arq))
                
                if not arquivos_encontrados:
                    ctk.CTkLabel(self.scroll_upload, text="(Nenhum arquivo encontrado com esse nome)", text_color="gray").pack(pady=10)
                else:
                    for pasta, arq in arquivos_encontrados:
                        raiz = pasta.split("__")[0].replace("#", "")
                        
                        frame_linha = ctk.CTkFrame(self.scroll_upload, fg_color="transparent")
                        frame_linha.pack(fill="x", pady=2, padx=5)
                        
                        nome_exibicao = f"📄 {arq['nome']}   (em {raiz})"
                        lbl_nome = ctk.CTkLabel(frame_linha, text=nome_exibicao, anchor="w")
                        lbl_nome.pack(side="left")
                        
                        tam = arq.get("size", 0)
                        size_str = formatar_tamanho(tam) if tam > 0 else "0 KB"
                        lbl_size = ctk.CTkLabel(frame_linha, text=size_str, font=("Segoe UI", 11, "bold"), text_color=paleta["fg"])
                        lbl_size.pack(side="right", padx=(5, 10))
                        
                        self.labels_tamanho_ui.append(lbl_size)

    def filtrar_arquivos_por_pasta(self, *args):
        if not hasattr(self, 'scroll_download') or not self.scroll_download.winfo_exists(): return
        for widget in self.scroll_download.winfo_children(): widget.destroy()
        
        self.download_checkboxes.clear()
        self.labels_tamanho_ui = [lbl for lbl in getattr(self, 'labels_tamanho_ui', []) if lbl.winfo_exists()]
        paleta = self.cores_destaque[self.combo_cor.get()]
        
        if getattr(self, 'estado_busca_down', 0) == 1:
            termo = self.termo_busca_down
            if not termo:
                ctk.CTkLabel(self.scroll_download, text="(Digite algo para buscar pastas ou subpastas em toda a nuvem)", text_color="gray").pack(pady=10)
            else:
                pastas_encontradas = []
                for item in self.lista_formatada:
                    backend_val = self.map_ui_to_backend[item]
                    if termo in item.lower() or termo in backend_val.lower():
                        pastas_encontradas.append(item)
                
                if not pastas_encontradas:
                    ctk.CTkLabel(self.scroll_download, text="(Nenhuma pasta ou subpasta encontrada com esse nome)", text_color="gray").pack(pady=10)
                else:
                    for item in pastas_encontradas:
                        btn = ctk.CTkButton(self.scroll_download, text=item, anchor="w", fg_color="transparent", text_color=("black", "white"), hover_color=paleta["hover"], command=lambda i=item: self.selecionar_pasta_busca('down', i))
                        btn.pack(fill="x", pady=2, padx=5)

        elif getattr(self, 'estado_busca_down', 0) == 2:
            termo = self.termo_busca_down
            if not termo:
                ctk.CTkLabel(self.scroll_download, text="(Digite algo para buscar arquivos em toda a nuvem)", text_color="gray").pack(pady=10)
            else:
                arquivos_encontrados = []
                for pasta, arquivos in self.pastas_nuvem.items():
                    for arq in arquivos:
                        if termo in arq["nome"].lower():
                            arquivos_encontrados.append((pasta, arq))
                
                if not arquivos_encontrados:
                    ctk.CTkLabel(self.scroll_download, text="(Nenhum arquivo encontrado com esse nome)", text_color="gray").pack(pady=10)
                else:
                    for pasta, arq in arquivos_encontrados:
                        raiz = pasta.split("__")[0].replace("#", "")
                        var = tk.BooleanVar(value=False)
                        
                        frame_linha = ctk.CTkFrame(self.scroll_download, fg_color="transparent")
                        frame_linha.pack(fill="x", pady=2, padx=5)
                        
                        nome_exibicao = f"{arq['nome']}   (em {raiz})"
                        cb = ctk.CTkCheckBox(frame_linha, text=nome_exibicao, variable=var, fg_color=paleta["fg"], hover_color=paleta["hover"], command=self.atualizar_contador_download)
                        cb.pack(side="left")
                        
                        tam = arq.get("size", 0)
                        size_str = formatar_tamanho(tam) if tam > 0 else "0 KB"
                        lbl_size = ctk.CTkLabel(frame_linha, text=size_str, font=("Segoe UI", 11, "bold"), text_color=paleta["fg"])
                        lbl_size.pack(side="right", padx=(5, 10))
                        
                        self.labels_tamanho_ui.append(lbl_size)
                        self.download_checkboxes.append((var, cb, arq, pasta))
        else:
            if not hasattr(self, 'combo_pasta_down') or not self.combo_pasta_down.winfo_exists(): return
            pasta_selecionada = self.map_ui_to_backend.get(self.combo_pasta_down.get())
            
            if not pasta_selecionada:
                return
            
            arquivos = self.pastas_nuvem.get(pasta_selecionada, [])
            if not arquivos:
                ctk.CTkLabel(self.scroll_download, text="(Nenhum arquivo nesta pasta)", text_color="gray").pack(pady=10)
            else:
                for arq in arquivos:
                    var = tk.BooleanVar(value=False)
                    
                    frame_linha = ctk.CTkFrame(self.scroll_download, fg_color="transparent")
                    frame_linha.pack(fill="x", pady=2, padx=5)
                    
                    cb = ctk.CTkCheckBox(frame_linha, text=arq["nome"], variable=var, fg_color=paleta["fg"], hover_color=paleta["hover"], command=self.atualizar_contador_download)
                    cb.pack(side="left")
                    
                    tam = arq.get("size", 0)
                    size_str = formatar_tamanho(tam) if tam > 0 else "0 KB"
                    lbl_size = ctk.CTkLabel(frame_linha, text=size_str, font=("Segoe UI", 11, "bold"), text_color=paleta["fg"])
                    lbl_size.pack(side="right", padx=(5, 10))
                    
                    self.labels_tamanho_ui.append(lbl_size)
                    self.download_checkboxes.append((var, cb, arq, pasta_selecionada))
        
        self.atualizar_contador_download()

    def atualizar_contador_download(self):
        qtd = sum(1 for var, cb, arq, pasta in self.download_checkboxes if var.get())
        if hasattr(self, 'lbl_down_count') and self.lbl_down_count.winfo_exists():
            self.lbl_down_count.configure(text=f"{qtd} arquivo(s) selecionado(s)", text_color=self.cores_destaque[self.combo_cor.get()]["fg"] if qtd > 0 else "gray")

    def selecionar_tudo_download(self):
        todas_marcadas = all(var.get() for var, cb, arq, pasta in self.download_checkboxes)
        for var, cb, arq, pasta in self.download_checkboxes: var.set(not todas_marcadas)
        self.atualizar_contador_download()

    def start_download(self):
        selecionados_objs = [arq for var, cb, arq, pasta in self.download_checkboxes if var.get()]
        
        if not selecionados_objs:
            messagebox.showinfo("Aviso", "Selecione pelo menos um arquivo marcando a caixinha.")
            return
        
        save_dir = filedialog.askdirectory(title="Selecione a pasta para salvar os arquivos")
        if save_dir and self.async_loop:
            asyncio.run_coroutine_threadsafe(self.perform_multiple_downloads(selecionados_objs, save_dir), self.async_loop)

    async def perform_multiple_downloads(self, arquivos_objs, save_dir):
        self.flag_cancelar = False
        self.after(0, lambda: self.btn_download.configure(state="disabled"))
        
        self.after(0, lambda: self.progresso_frame.pack(side="bottom", fill="x", padx=15, pady=(2, 2), before=self.terminal_wrapper))
        self.after(0, lambda: self.btn_cancelar.configure(state="normal", text="❌ CANCELAR"))
        
        self.is_downloading = True
        self.historico_arquivos.clear()
        self.total_arquivos_sessao = len(arquivos_objs)
        self.after(0, lambda: self.bloqueio_manager.sincronizar_painel_topo())
        
        cor_tema = self.cores_destaque[self.combo_cor.get()]["fg"]
        self.mudar_status("⬇️ Realizando Downloads...", cor_tema, "#FFFFFF")
        
        try:
            for idx, arq in enumerate(arquivos_objs, 1):
                if self.flag_cancelar: break
                filename = arq["nome"]
                msg_obj = arq["msg"]
                self.historico_arquivos.append(filename)
                save_path = os.path.join(save_dir, filename)
                
                self.after(0, lambda f=filename, i=idx: self.lbl_action_status.configure(text=f"Baixando ({i}/{len(arquivos_objs)}): {f}"))
                self.log(f"[DOWNLOAD] [{idx}/{len(arquivos_objs)}] Baixando: '{filename}'")
                self.after(0, lambda n=filename: self.bloqueio_manager.adicionar_arquivo_painel(n, concluido=False))
                self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa(f"Baixando: {filename}"))
                
                try:
                    await self.client.download_media(
                        msg_obj, file=save_path, progress_callback=self.get_progress_callback("Download", filename)
                    )
                    self.after(0, lambda n=filename: self.bloqueio_manager.adicionar_arquivo_painel(n, concluido=True))
                    self.log(f"[DOWNLOAD] [{idx}/{len(arquivos_objs)}] Concluído: {save_path}")
                except Exception as e:
                    if "CANCELADO_PELO_USUARIO" in str(e):
                        self.log(f"[SISTEMA] Download de '{filename}' interrompido pelo usuário.")
                        if os.path.exists(save_path): os.remove(save_path)
                        break 
                    else: raise e

            if self.flag_cancelar: self.mudar_status("❌ Operação Cancelada!", "#dc3545", "#FFFFFF")
            else: self.mudar_status("✅ Downloads concluídos com sucesso!", cor_tema, "#FFFFFF")
                
            self.after(0, lambda: self.bloqueio_manager.finalizar_painel_topo())
            self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa("Operação finalizada! 🚀", esconder_barra=True))
        except Exception as e:
            self.log(f"[ERRO] Falha no download: {str(e)}")
            self.mudar_status("❌ Erro no download", "#dc3545", "#FFFFFF")
        finally:
            self.is_downloading = False
            if hasattr(self, 'btn_download') and self.btn_download.winfo_exists():
                self.after(0, lambda: self.btn_download.configure(state="normal"))
            for var, cb, arq, pasta in self.download_checkboxes: var.set(False)
            self.after(0, self.atualizar_contador_download)
            self.after(0, lambda: self.progresso_frame.pack_forget())

    def abrir_gerenciador_nuvem(self):
        from gerenciador import GerenciadorNuvem
        self.gerenciador_manager = GerenciadorNuvem(self)
        self.gerenciador_manager.abrir()

if __name__ == "__main__":
    app = TelegramCloudApp()
    app.mainloop()