import threading
import os
import sys
import shutil
import cv2 
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageEnhance

from core.downloader import baixar_arquivos
from core.zip_manager import criar_zip
from core.parser import get_versions, get_paths
from core.file_builder import gerar_arquivos
from core.theme import carregar_tema, salvar_tema
from core.updater import checar_atualizacao
from core.config import carregar_config, salvar_config

# ==========================================
# TELA DE BLOQUEIO (MODO APRESENTAÇÃO)
# ==========================================
class TelaDeBloqueio:
    def __init__(self, app):
        self.app = app
        self.lock_frame = None
        self.lbl_fundo = None
        
        self.midias = []
        self.idx_midia = 0
        
        self.timer_id = None
        self.video_after_id = None
        self.video_cap = None
        self.arquivos_vistos = set()
        
        self.app.bind_all("<Button-3>", self.mostrar_menu_contexto)
        self.app.bind_all("<Return>", self.sair_bloqueio_tecla)

    def mostrar_menu_contexto(self, event):
        try:
            if self.lock_frame is not None:
                return

            if event.widget.winfo_toplevel() != self.app:
                return

            menu = tk.Menu(self.app, tearoff=0, font=("Segoe UI", 10))
            menu.add_command(label="🔒 Plano de Bloqueio", command=self.ativar_bloqueio)
            menu.post(event.x_root, event.y_root)
        except Exception:
            pass

    def ativar_bloqueio(self):
        pasta_assets = os.path.abspath(os.path.join(os.getcwd(), "assets", "wallpaper"))
        os.makedirs(pasta_assets, exist_ok=True)
        
        extensoes_suportadas = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv')
        self.midias = [os.path.join(pasta_assets, f) for f in os.listdir(pasta_assets) if f.lower().endswith(extensoes_suportadas)]

        if not self.midias:
            messagebox.showinfo("Plano de Bloqueio", f"Nenhuma imagem ou vídeo encontrado.\nPor favor, adicione arquivos na pasta:\n{pasta_assets}")
            return

        self.lock_frame = ctk.CTkFrame(self.app, corner_radius=0, fg_color="#000000")
        self.lock_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.lbl_fundo = ctk.CTkLabel(self.lock_frame, text="", fg_color="#000000")
        self.lbl_fundo.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        
        # --- PAINEL TOPO ---
        self.frame_topo_concluido = ctk.CTkFrame(self.lock_frame, width=520, height=90, fg_color="#0A0A0A", 
                                                 border_width=2, border_color=paleta["fg"], corner_radius=0)
        self.frame_topo_concluido.pack_propagate(False)
        
        frame_header = ctk.CTkFrame(self.frame_topo_concluido, fg_color="transparent")
        frame_header.pack(fill="x", padx=15, pady=(5, 0))
        
        self.lbl_contador_atual = ctk.CTkLabel(frame_header, text="0", font=("Segoe UI Black", 14), text_color=paleta["fg"])
        self.lbl_contador_atual.pack(side="left")
        
        self.lbl_titulo_topo = ctk.CTkLabel(frame_header, text="DOWNLOADS EM ANDAMENTO", font=("Segoe UI Black", 12), text_color=paleta["fg"])
        self.lbl_titulo_topo.pack(side="left", expand=True)
        
        self.lbl_contador_total = ctk.CTkLabel(frame_header, text="0", font=("Segoe UI Black", 14), text_color=paleta["fg"])
        self.lbl_contador_total.pack(side="right")
        
        self.scroll_files = ctk.CTkScrollableFrame(self.frame_topo_concluido, orientation="horizontal", height=32, fg_color="transparent")
        self.scroll_files.pack(fill="both", expand=True, padx=5, pady=(0, 2))
        
        self.progressbar_topo = ctk.CTkProgressBar(self.frame_topo_concluido, mode="determinate", height=4, corner_radius=0)
        self.progressbar_topo.set(0)
        self.progressbar_topo.configure(progress_color=paleta["fg"])
        self.progressbar_topo.pack(fill="x", padx=20, pady=(0, 6))
        
        # --- PAINEL CENTRAL ---
        self.frame_central = ctk.CTkFrame(self.lock_frame, width=350, height=80, corner_radius=0, 
                                          fg_color="#0A0A0A", border_width=2, border_color=paleta["fg"])
        self.frame_central.place(relx=0.5, rely=0.45, anchor="center")
        lbl_msg = ctk.CTkLabel(self.frame_central, text="Modo Apresentação Ativo\nClique ou aperte ENTER para retornar", 
                               font=("Segoe UI", 16, "bold"), text_color="#FFFFFF")
        lbl_msg.pack(pady=20, padx=30)

        # --- PAINEL INFERIOR ---
        self.frame_bottom = ctk.CTkFrame(self.lock_frame, corner_radius=0, 
                                         fg_color="#0A0A0A", border_width=2, border_color=paleta["fg"])
        self.frame_bottom.place(relx=0.5, rely=0.88, anchor="center", relwidth=0.8)

        self.lbl_bloqueio_arquivo = ctk.CTkLabel(self.frame_bottom, text="Download pendente...", font=("Segoe UI", 16, "bold"), text_color="#FFFFFF", anchor="center", justify="center")
        self.lbl_bloqueio_arquivo.pack(pady=(15, 5), fill="x")

        self.bloqueio_progressbar = ctk.CTkProgressBar(self.frame_bottom, mode="determinate", height=12, corner_radius=0)
        self.bloqueio_progressbar.set(0)
        self.bloqueio_progressbar.configure(progress_color=paleta["fg"])
        self.bloqueio_progressbar.pack(fill="x", padx=30, pady=5)

        self.lbl_bloqueio_stats = ctk.CTkLabel(self.frame_bottom, text="", font=("Segoe UI", 14, "bold"), text_color="#FFFFFF", anchor="center", justify="center")
        self.lbl_bloqueio_stats.pack(pady=(5, 15), fill="x")

        if getattr(self.app, 'is_downloading', False):
            self.lbl_bloqueio_arquivo.configure(text="Sincronizando com o download...")
        else:
            self.bloqueio_progressbar.pack_forget()

        self.lbl_fundo.bind("<Button-1>", self.sair_bloqueio)
        self.frame_central.bind("<Button-1>", self.sair_bloqueio)
        lbl_msg.bind("<Button-1>", self.sair_bloqueio)
        self.frame_bottom.bind("<Button-1>", self.sair_bloqueio)
        self.frame_topo_concluido.bind("<Button-1>", self.sair_bloqueio)

        self.idx_midia = 0
        self.transicionar_midia()
        self.sincronizar_painel_topo()

    def sincronizar_painel_topo(self):
        if not self.lock_frame: return
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        self.arquivos_vistos.clear()
        
        for widget in self.scroll_files.winfo_children():
            widget.destroy()

        if self.app.is_downloading or self.app.historico_arquivos:
            self.frame_topo_concluido.place(relx=0.5, rely=0.03, anchor="n")
            self.frame_topo_concluido.lift() 
        else:
            self.frame_topo_concluido.place_forget()
            return

        if self.app.is_downloading:
            self.lbl_titulo_topo.configure(text="DOWNLOADS EM ANDAMENTO", text_color=paleta["fg"])
            for arq in self.app.historico_arquivos:
                self.adicionar_arquivo_painel(arq, concluido=False)
        elif self.app.historico_arquivos:
            self.lbl_titulo_topo.configure(text="CONCLUÍDO", text_color=paleta["fg"])
            self.progressbar_topo.set(1.0)
            for arq in self.app.historico_arquivos:
                self.adicionar_arquivo_painel(arq, concluido=True)

    def adicionar_arquivo_painel(self, nome_arquivo, concluido=False):
        if not self.lock_frame: return
        if not nome_arquivo or nome_arquivo in self.arquivos_vistos: return
        
        if not self.frame_topo_concluido.winfo_ismapped():
            self.frame_topo_concluido.place(relx=0.5, rely=0.03, anchor="n")
            self.frame_topo_concluido.lift()

        self.arquivos_vistos.add(nome_arquivo)
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        icone = "✅" if concluido else "⏳"
        
        item_frame = ctk.CTkFrame(self.scroll_files, fg_color="#181818", corner_radius=4, border_width=1, border_color=paleta["fg"])
        item_frame.pack(side="left", padx=4, fill="y", pady=0)
        
        lbl_icone = ctk.CTkLabel(item_frame, text=icone, font=("Segoe UI", 11))
        lbl_icone.pack(side="left", padx=(6, 4), pady=2)
        
        lbl_arq = ctk.CTkLabel(item_frame, text=nome_arquivo, font=("Segoe UI", 10, "bold"), text_color="#EEEEEE", anchor="w")
        lbl_arq.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=2)
        
        atual = len(self.app.historico_arquivos)
        total = max(self.app.total_arquivos_sessao, atual)
        
        self.lbl_contador_atual.configure(text=str(atual))
        self.lbl_contador_total.configure(text=str(total))
        
        progresso = atual / total if total > 0 else 0
        self.progressbar_topo.set(progresso)
        
        try:
            self.scroll_files._parent_canvas.xview_moveto(1.0)
        except: pass

    def finalizar_painel_topo(self):
        if not self.lock_frame: return
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        self.lbl_titulo_topo.configure(text="CONCLUÍDO", text_color=paleta["fg"])
        self.progressbar_topo.set(1.0)
        
        for frame in self.scroll_files.winfo_children():
            for child in frame.winfo_children():
                if child.cget("text") == "⏳":
                    child.configure(text="✅")

    def transicionar_midia(self):
        if not self.lock_frame or not self.midias:
            return

        caminho_midia = self.midias[self.idx_midia]
        extensao = os.path.splitext(caminho_midia)[1].lower()

        if extensao in ['.mp4', '.avi', '.mov', '.mkv']:
            self.reproduzir_video(caminho_midia)
        else:
            self.mostrar_imagem(caminho_midia)

    def mostrar_imagem(self, caminho_img):
        try:
            pil_img = Image.open(caminho_img)
            w, h = self._obter_dimensoes_tela()
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
            self.lbl_fundo.configure(image=ctk_img)
        except Exception:
            pass

        self.idx_midia = (self.idx_midia + 1) % len(self.midias)
        self.timer_id = self.app.after(15000, self.transicionar_midia)

    def reproduzir_video(self, caminho_video):
        self.video_cap = cv2.VideoCapture(caminho_video)
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps != fps: 
            fps = 30
        self.delay_frame = int(1000 / fps)
        self._tocar_frame()

    def _tocar_frame(self):
        if not self.lock_frame or not self.video_cap:
            return

        ret, frame = self.video_cap.read()
        if ret:
            w, h = self._obter_dimensoes_tela()
            frame_resized = cv2.resize(frame, (w, h))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            ctk_img = ctk.CTkImage(light_image=pil_img, size=(w, h))
            self.lbl_fundo.configure(image=ctk_img)
            self.video_after_id = self.app.after(self.delay_frame, self._tocar_frame)
        else:
            self.video_cap.release()
            self.video_cap = None
            self.idx_midia = (self.idx_midia + 1) % len(self.midias)
            self.transicionar_midia()

    def _obter_dimensoes_tela(self):
        w = self.app.winfo_width()
        h = self.app.winfo_height()
        return 720 if w < 10 else w, 560 if h < 10 else h

    def atualizar_status(self, arquivo, progresso, stats):
        if self.lock_frame:
            if not self.bloqueio_progressbar.winfo_ismapped():
                self.bloqueio_progressbar.pack(fill="x", padx=30, pady=5, before=self.lbl_bloqueio_stats)
            self.lbl_bloqueio_arquivo.configure(text=f"Baixando: {arquivo}")
            self.bloqueio_progressbar.set(progresso)
            self.lbl_bloqueio_stats.configure(text=stats)

    def definir_mensagem_fixa(self, mensagem, esconder_barra=False):
        if self.lock_frame:
            self.lbl_bloqueio_arquivo.configure(text=mensagem)
            self.lbl_bloqueio_stats.configure(text="")
            if esconder_barra:
                self.bloqueio_progressbar.pack_forget()
            else:
                self.bloqueio_progressbar.set(1.0 if "concluído" in mensagem.lower() else 0)

    def sair_bloqueio_tecla(self, event):
        self.sair_bloqueio(None)

    def sair_bloqueio(self, event):
        if self.timer_id:
            self.app.after_cancel(self.timer_id)
            self.timer_id = None
        if getattr(self, 'video_after_id', None):
            self.app.after_cancel(self.video_after_id)
            self.video_after_id = None
        if getattr(self, 'video_cap', None):
            self.video_cap.release()
            self.video_cap = None
        if self.lock_frame:
            self.lock_frame.destroy()
            self.lock_frame = None


def obter_caminho(caminho_relativo):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, caminho_relativo)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.VERSAO_PROGRAMA = "v1.0.7"
        self.title(f"Fiuza Technology - Pack Full Aplicação Socin ({self.VERSAO_PROGRAMA})")
        self._aplicar_icone(self)
        
        app_width, app_height = 720, 560 
        x = (self.winfo_screenwidth() // 2) - (app_width // 2)
        y = (self.winfo_screenheight() // 2) - (app_height // 2)
        self.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.resizable(False, False)
        
        self.flag_cancelar = False
        self.is_downloading = False 
        self.pasta_concluida = None
        self.historico_arquivos = []
        self.total_arquivos_sessao = 0
        self.versoes = get_versions()

        self.cores_destaque = {
            "Amarelo": {"fg": "#FFD700", "hover": "#CCAC00", "text": "#000000"},
            "Azul": {"fg": "#007BFF", "hover": "#0056b3", "text": "#FFFFFF"},
            "Azul-bebê": {"fg": "#89CFF0", "hover": "#5B9BCC", "text": "#000000"},
            "Azul-marinho": {"fg": "#000080", "hover": "#000050", "text": "#FFFFFF"},
            "Azul-turquesa": {"fg": "#40E0D0", "hover": "#30C0B0", "text": "#000000"},
            "Bege": {"fg": "#F5F5DC", "hover": "#D5D5BC", "text": "#000000"},
            "Bordô": {"fg": "#800000", "hover": "#500000", "text": "#FFFFFF"},
            "Branco": {"fg": "#FFFFFF", "hover": "#CCCCCC", "text": "#000000"},
            "Caramelo": {"fg": "#C68E17", "hover": "#9A6A0C", "text": "#FFFFFF"},
            "Cáqui": {"fg": "#F0E68C", "hover": "#C0B65C", "text": "#000000"},
            "Castanho": {"fg": "#8B4513", "hover": "#5B2503", "text": "#FFFFFF"},
            "Cinza": {"fg": "#808080", "hover": "#505050", "text": "#FFFFFF"},
            "Creme": {"fg": "#FFFDD0", "hover": "#CCCBA0", "text": "#000000"},
            "Laranja": {"fg": "#FFA500", "hover": "#CC8500", "text": "#000000"},
            "Lilás": {"fg": "#C8A2C8", "hover": "#987298", "text": "#000000"},
            "Marrom": {"fg": "#964B00", "hover": "#663300", "text": "#FFFFFF"},
            "Mostarda": {"fg": "#FFDB58", "hover": "#CCAB28", "text": "#000000"},
            "Preto": {"fg": "#000000", "hover": "#333333", "text": "#FFFFFF"},
            "Rosa": {"fg": "#FFC0CB", "hover": "#CC909B", "text": "#000000"},
            "Rosa-bebê": {"fg": "#F4C2C2", "hover": "#C49292", "text": "#000000"},
            "Rosa-choque": {"fg": "#FF1493", "hover": "#CC1073", "text": "#FFFFFF"},
            "Roxo": {"fg": "#800080", "hover": "#500050", "text": "#FFFFFF"},
            "Salmão": {"fg": "#FA8072", "hover": "#CA5042", "text": "#000000"},
            "Verde": {"fg": "#28a745", "hover": "#218838", "text": "#FFFFFF"},
            "Verde-água": {"fg": "#7FFFD4", "hover": "#4FCCA4", "text": "#000000"},
            "Vermelho": {"fg": "#dc3545", "hover": "#c82333", "text": "#FFFFFF"},
            "Vinho": {"fg": "#722F37", "hover": "#420F17", "text": "#FFFFFF"},
            "Violeta": {"fg": "#EE82EE", "hover": "#BE52BE", "text": "#000000"}
        }

        self.criar_widgets()
        self.aplicar_tema_inicial()
        self.bloqueio_manager = TelaDeBloqueio(self)

        # Verificação automática de pós-atualização para exibir o Changelog da v1.0.5
        config = carregar_config()
        ultima_versao_vista = config.get("ultima_versao_vista", "")
        if ultima_versao_vista != self.VERSAO_PROGRAMA:
            self.after(600, self.mostrar_changelog)
            config["ultima_versao_vista"] = self.VERSAO_PROGRAMA
            salvar_config(config)

        if self.auto_update:
            threading.Thread(target=lambda: checar_atualizacao(self.VERSAO_PROGRAMA, self.log, self)).start()

    def _aplicar_icone(self, janela):
        try:
            caminho_ico = obter_caminho("assets/icon.ico")
            if os.path.exists(caminho_ico):
                janela.after(250, lambda: janela.iconbitmap(caminho_ico))
        except Exception:
            pass

    def mostrar_changelog(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Atualização Concluída!")
        largura, altura = 460, 410
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        modal.geometry(f"{largura}x{altura}+{x}+{y}")
        modal.resizable(False, False)
        modal.transient(self)
        
        modal.attributes('-topmost', True)
        modal.after(200, modal.grab_set)
        modal.after(250, lambda: modal.focus_force())
        modal.after(300, lambda: modal.attributes('-topmost', False))

        paleta = self.cores_destaque[self.combo_cor.get()]

        lbl_titulo = ctk.CTkLabel(modal, text="🚀 Releases 1.0.7", font=("Segoe UI Black", 18), text_color=paleta["fg"])
        lbl_titulo.pack(pady=(20, 5))

        lbl_sub = ctk.CTkLabel(modal, text="O sistema foi atualizado com sucesso! Veja as novidades:", font=("Segoe UI", 12), text_color="gray")
        lbl_sub.pack(pady=(0, 10))

        # Texto formatado com as melhorias solicitadas
        mudancas = (
            "• Recurso Cloud Telegram sem Limite de GB.\n"
            "• Planos de Fundo em Alta Resolucao.\n"
            "• Melhorias e aprimoramentos.\n"
        )

        txt_box = ctk.CTkTextbox(modal, width=400, height=170, corner_radius=8, font=("Segoe UI", 12))
        txt_box.pack(pady=5)
        txt_box.insert("0.1", mudancas)
        txt_box.configure(state="disabled")

        btn_ok = ctk.CTkButton(modal, text="OK", width=140, height=35, command=modal.destroy,
                               fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
        btn_ok.pack(pady=15)
        
        modal.bind("<Return>", lambda e: modal.destroy())
        self._aplicar_icone(modal)

    def criar_widgets(self):
        self.btn_config = ctk.CTkButton(
            self, text="⚙️", width=32, height=32, font=("Segoe UI", 16), 
            fg_color="transparent", command=self.abrir_configuracoes
        )
        self.btn_config.place(x=672, y=8)

        img_path = obter_caminho("assets/logo.png")
        img_original = Image.open(img_path)
        img_brilhante = ImageEnhance.Brightness(img_original).enhance(1.6)

        self.img_normal = ctk.CTkImage(light_image=img_original, size=(110, 48))
        self.img_glow = ctk.CTkImage(light_image=img_brilhante, size=(110, 48))
        
        self.frame_logo = ctk.CTkFrame(self, fg_color="transparent", border_width=2, corner_radius=12)
        self.frame_logo.pack(pady=(15, 5))
        
        self.lbl_logo = ctk.CTkLabel(self.frame_logo, image=self.img_normal, text="")
        self.lbl_logo.pack(padx=15, pady=8)
        self.lbl_logo.bind("<Enter>", lambda e: self.lbl_logo.configure(image=self.img_glow))
        self.lbl_logo.bind("<Leave>", lambda e: self.lbl_logo.configure(image=self.img_normal))
        self.lbl_logo.bind("<Button-1>", self.mostrar_assinatura)

        frame_temas = ctk.CTkFrame(self, fg_color="transparent", height=40)
        frame_temas.pack(pady=(5, 5), fill="x", padx=30)
        frame_temas.pack_propagate(False) 
        
        lbl_modo = ctk.CTkLabel(frame_temas, text="Modo Visual:", font=("Segoe UI", 11))
        lbl_modo.pack(side="left", padx=(0, 8))
        self.combo_modo = ctk.CTkComboBox(frame_temas, values=["Light", "Dark"], width=110, height=28, command=self.mudar_tema)
        self.combo_modo.pack(side="left")

        self.combo_cor = ctk.CTkComboBox(frame_temas, values=list(self.cores_destaque.keys()), width=110, height=28, command=self.mudar_tema)
        self.combo_cor.pack(side="right")
        lbl_cor = ctk.CTkLabel(frame_temas, text="Cor de Destaque:", font=("Segoe UI", 11))
        lbl_cor.pack(side="right", padx=(0, 8))

        self.lbl_titulo_app = ctk.CTkLabel(frame_temas, text="PACK FULL SOCIN", font=("Segoe UI Black", 24))
        self.lbl_titulo_app.place(relx=0.5, rely=0.5, anchor="center")

        self.frame_principal = ctk.CTkFrame(self, corner_radius=12, border_width=1)
        self.frame_principal.pack(padx=25, pady=4, fill="both", expand=True)

        self.lbl_versao = ctk.CTkLabel(self.frame_principal, text="V E R S Ã O", font=("Segoe UI", 10, "bold"), text_color="gray")
        self.lbl_versao.pack(pady=(8, 1))
        self.combo_versao = ctk.CTkComboBox(self.frame_principal, values=self.versoes, command=self.carregar_paths, width=300, height=28)
        self.combo_versao.set("Selecione aqui a versao desejada")
        self.combo_versao.pack()

        self.lbl_path = ctk.CTkLabel(self.frame_principal, text="P A T H", font=("Segoe UI", 10, "bold"), text_color="gray")
        self.lbl_path.pack(pady=(6, 1))
        self.combo_path = ctk.CTkComboBox(self.frame_principal, values=["Selecione aqui o path desejado"], width=300, height=28)
        self.combo_path.set("Selecione aqui o path desejado")
        self.combo_path.pack()

        self.lbl_arquivo = ctk.CTkLabel(self.frame_principal, text="", font=("Segoe UI", 11))
        self.progressbar = ctk.CTkProgressBar(self.frame_principal, width=300, mode="determinate", height=10)
        self.progressbar.set(0)
        self.lbl_porcentagem = ctk.CTkLabel(self.frame_principal, text="0%", font=("Segoe UI", 12, "bold"))

        self.btn_cancelar = ctk.CTkButton(self.frame_principal, text="CANCELAR", width=220, height=34, command=self.acionar_cancelamento)
        self.btn_gerar = ctk.CTkButton(self.frame_principal, text="GERAR PACK", width=220, height=34, command=self.abrir_modal_opcoes)
        self.btn_gerar.pack(pady=8)

        self.frame_pos_download = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        self.btn_apagar = ctk.CTkButton(self.frame_pos_download, text="🗑️ Apagar Pasta", width=100, height=32, fg_color="#dc3545", hover_color="#c82333", command=self.acao_apagar_pasta)
        self.btn_apagar.pack(side="left", padx=4)
        self.btn_abrir = ctk.CTkButton(self.frame_pos_download, text="📁 Abrir Pasta", width=100, height=32, fg_color="#17a2b8", hover_color="#138496", command=self.acao_abrir_pasta)
        self.btn_abrir.pack(side="left", padx=4)
        self.btn_gerenciar = ctk.CTkButton(self.frame_pos_download, text="⚙️ Gerenciar", width=100, height=32, fg_color="#6c757d", hover_color="#5a6268", command=self.abrir_gerenciador)
        self.btn_gerenciar.pack(side="left", padx=4)
        self.btn_novo = ctk.CTkButton(self.frame_pos_download, text="🔄 Novo", width=80, height=32, command=self.acao_novo_download)
        self.btn_novo.pack(side="left", padx=4)

        self.logs = ctk.CTkTextbox(self.frame_principal, width=600, height=115, corner_radius=8)
        self.logs.pack(pady=2)
        
        self.lbl_status = ctk.CTkButton(
            self.frame_principal, text="⏳ Pronto para iniciar", width=600, height=28, 
            state="disabled", fg_color="#333333", text_color="#FFFFFF", corner_radius=6
        )
        self.lbl_status.pack(pady=(2, 2))

        self.btn_abrir_gerenciador_main = ctk.CTkButton(
            self, text="Gerenciamento de Pastas e Arquivos", width=670, height=30,
            fg_color="transparent", border_width=2, corner_radius=6, command=self.abrir_gerenciador
        )
        self.btn_abrir_gerenciador_main.pack(pady=(5, 10))

        self.log("Sistema iniciado.")

    def acao_apagar_pasta(self):
        if self.pasta_concluida and os.path.exists(self.pasta_concluida):
            if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja apagar permanentemente:\n{self.pasta_concluida}?"):
                try:
                    if os.path.isdir(self.pasta_concluida): shutil.rmtree(self.pasta_concluida)
                    else: os.remove(self.pasta_concluida)
                    self.log(f"Pasta/Arquivo apagado: {self.pasta_concluida}")
                    messagebox.showinfo("Sucesso", "Item apagado com sucesso!")
                    self.acao_novo_download()
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível apagar: {e}")

    def acao_abrir_pasta(self):
        if self.pasta_concluida and os.path.exists(self.pasta_concluida):
            alvo = self.pasta_concluida if os.path.isdir(self.pasta_concluida) else os.path.dirname(self.pasta_concluida)
            os.startfile(os.path.abspath(alvo))

    def acao_novo_download(self):
        self.pasta_concluida = None
        self.frame_pos_download.pack_forget()
        self.btn_gerar.pack(pady=8, before=self.logs)
        self.mudar_status("⏳ Pronto para iniciar", "#E0E0E0" if self.combo_modo.get() == "Light" else "#333333", 
                          "#000000" if self.combo_modo.get() == "Light" else "#FFFFFF")

    def abrir_gerenciador(self):
        self.janela_gerenciador = ctk.CTkToplevel(self)
        self.janela_gerenciador.title("Gerenciador de Pastas (Temp / Output)")
        self._aplicar_icone(self.janela_gerenciador)
        
        largura, altura = 600, 450
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        self.janela_gerenciador.geometry(f"{largura}x{altura}+{x}+{y}")
        self.janela_gerenciador.transient(self)
        self.janela_gerenciador.grab_set()

        self.caminho_atual_gerenciador = None 
        self.itens_selecionados = set()
        self.ultimo_indice_clicado = None
        self.widgets_lista = []
        
        frame_topo = ctk.CTkFrame(self.janela_gerenciador, fg_color="transparent")
        frame_topo.pack(fill="x", padx=20, pady=(15, 5))
        
        self.lbl_caminho_gerenciador = ctk.CTkLabel(frame_topo, text="Raiz (Selecione uma pasta)", font=("Segoe UI", 14, "bold"))
        self.lbl_caminho_gerenciador.pack(side="left")

        paleta = self.cores_destaque[self.combo_cor.get()]
        
        self.btn_nova_pasta = ctk.CTkButton(frame_topo, text="📁 Nova Pasta", width=100, height=28, fg_color=paleta["fg"], hover_color=paleta["hover"], command=lambda: self.acao_gerenciador_criar_pasta(self.caminho_atual_gerenciador))
        self.btn_nova_pasta.pack(side="right")

        self.frame_lista_gerenciador = ctk.CTkScrollableFrame(self.janela_gerenciador, width=550, height=350, border_width=1, border_color=paleta["fg"])
        self.frame_lista_gerenciador.pack(padx=20, pady=5, fill="both", expand=True)
        
        self.atualizar_lista_gerenciador()

    def _limpar_frame_seguro(self):
        filhos = self.frame_lista_gerenciador.winfo_children()
        for widget in filhos:
            widget.pack_forget()
        self.after(50, lambda w=filhos: [child.destroy() for child in w])
        self.widgets_lista.clear()
        self.itens_selecionados.clear()
        self.ultimo_indice_clicado = None

    def atualizar_lista_gerenciador(self):
        self._limpar_frame_seguro()

        if self.caminho_atual_gerenciador is None:
            self.lbl_caminho_gerenciador.configure(text="Raiz (temp / output)")
            self.btn_nova_pasta.configure(state="disabled") 
            pastas_base = ["temp", "output"]
            for pasta in pastas_base:
                if os.path.exists(pasta):
                    self._criar_item_gerenciador(pasta, os.path.abspath(pasta), eh_pasta=True)
        else:
            self.lbl_caminho_gerenciador.configure(text=f"Explorando: {self.caminho_atual_gerenciador}")
            self.btn_nova_pasta.configure(state="normal")
            
            btn_voltar = ctk.CTkButton(self.frame_lista_gerenciador, text="⬅️ Voltar", fg_color="#6c757d", hover_color="#5a6268", anchor="w", 
                                       command=lambda: self.navegar_gerenciador(os.path.dirname(self.caminho_atual_gerenciador) if self.caminho_atual_gerenciador not in [os.path.abspath("temp"), os.path.abspath("output")] else None))
            btn_voltar.pack(fill="x", pady=2)

            if os.path.exists(self.caminho_atual_gerenciador):
                itens = os.listdir(self.caminho_atual_gerenciador)
                if not itens:
                    ctk.CTkLabel(self.frame_lista_gerenciador, text="(Pasta Vazia)", text_color="gray").pack(pady=10)
                else:
                    for item in itens:
                        caminho_completo = os.path.join(self.caminho_atual_gerenciador, item)
                        eh_pasta = os.path.isdir(caminho_completo)
                        self._criar_item_gerenciador(item, caminho_completo, eh_pasta)

    def _criar_item_gerenciador(self, nome, caminho_completo, eh_pasta):
        icone = "📁" if eh_pasta else "📄"
        idx = len(self.widgets_lista)
        
        linha = ctk.CTkFrame(self.frame_lista_gerenciador, fg_color="transparent")
        linha.pack(fill="x", pady=2, padx=5)
        lbl_item = ctk.CTkLabel(linha, text=f"{icone} {nome}", font=("Segoe UI", 13), cursor="hand2", anchor="w")
        lbl_item.pack(side="left", fill="x", expand=True)

        info = {'caminho': caminho_completo, 'frame': linha, 'lbl': lbl_item, 'eh_pasta': eh_pasta, 'idx': idx}
        self.widgets_lista.append(info)

        if eh_pasta:
            lbl_item.bind("<Button-1>", lambda e, path=caminho_completo: self.navegar_gerenciador(path))
            linha.bind("<Button-1>", lambda e, path=caminho_completo: self.navegar_gerenciador(path))
        else:
            lbl_item.bind("<Button-1>", lambda e, i=idx: self.selecionar_item(e, i))
            linha.bind("<Button-1>", lambda e, i=idx: self.selecionar_item(e, i))
            
        lbl_item.bind("<Button-3>", lambda e, i=idx: self.menu_contexto_multiplo(e, i))
        linha.bind("<Button-3>", lambda e, i=idx: self.menu_contexto_multiplo(e, i))

    def selecionar_item(self, event, index):
        caminho = self.widgets_lista[index]['caminho']
        ctrl_press = (event.state & 0x0004) != 0
        shift_press = (event.state & 0x0001) != 0

        if shift_press and self.ultimo_indice_clicado is not None:
            inicio = min(self.ultimo_indice_clicado, index)
            fim = max(self.ultimo_indice_clicado, index)
            self.itens_selecionados.clear()
            for i in range(inicio, fim + 1):
                self.itens_selecionados.add(self.widgets_lista[i]['caminho'])
        elif ctrl_press:
            if caminho in self.itens_selecionados:
                self.itens_selecionados.remove(caminho)
            else:
                self.itens_selecionados.add(caminho)
            self.ultimo_indice_clicado = index
        else:
            self.itens_selecionados = {caminho}
            self.ultimo_indice_clicado = index

        self.atualizar_cores_selecao()

    def atualizar_cores_selecao(self):
        paleta = self.cores_destaque[self.combo_cor.get()]
        cor_hover = paleta["hover"]
        for item in self.widgets_lista:
            if item['caminho'] in self.itens_selecionados:
                item['frame'].configure(fg_color=cor_hover)
            else:
                item['frame'].configure(fg_color="transparent")

    def navegar_gerenciador(self, caminho):
        self.caminho_atual_gerenciador = caminho
        self.atualizar_lista_gerenciador()

    def acao_gerenciador_criar_pasta(self, destino):
        if not destino: return
        dialog = ctk.CTkInputDialog(text="Digite o nome da nova pasta:", title="Nova Pasta")
        nome = dialog.get_input()
        if nome:
            novo_caminho = os.path.join(destino, nome)
            try:
                os.makedirs(novo_caminho, exist_ok=True)
                self.atualizar_lista_gerenciador()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar pasta: {e}", parent=self.janela_gerenciador)

    def acao_gerenciador_renomear(self, caminho):
        diretorio = os.path.dirname(caminho)
        nome_atual = os.path.basename(caminho)
        dialog = ctk.CTkInputDialog(text=f"Digite o novo nome para '{nome_atual}':", title="Renomear Pasta")
        novo_nome = dialog.get_input()
        if novo_nome:
            novo_caminho = os.path.join(diretorio, novo_nome)
            try:
                os.rename(caminho, novo_caminho)
                self.atualizar_lista_gerenciador()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao renomear: {e}", parent=self.janela_gerenciador)

    def menu_contexto_multiplo(self, event, index):
        caminho = self.widgets_lista[index]['caminho']
        
        if caminho not in self.itens_selecionados:
            self.itens_selecionados = {caminho}
            self.ultimo_indice_clicado = index
            self.atualizar_cores_selecao()

        qtd = len(self.itens_selecionados)
        menu = tk.Menu(self.janela_gerenciador, tearoff=0, font=("Segoe UI", 10))

        if qtd == 1:
            item = next((i for i in self.widgets_lista if i['caminho'] == caminho), None)
            eh_pasta = item['eh_pasta'] if item else False
            if eh_pasta:
                menu.add_command(label="📁 Entrar na Pasta", command=lambda: self.after(10, lambda: self.navegar_gerenciador(caminho)))
                menu.add_command(label="📁 Criar Nova Pasta Aqui", command=lambda: self.after(10, lambda: self.acao_gerenciador_criar_pasta(caminho)))
                menu.add_command(label="✏️ Renomear Pasta", command=lambda: self.after(10, lambda: self.acao_gerenciador_renomear(caminho)))
                menu.add_command(label="❌ Apagar Pasta", command=lambda: self.after(10, lambda: self.acao_multipla("apagar")))
                menu.add_command(label="🪟 Abrir no Windows", command=lambda: self.after(10, lambda: os.startfile(caminho)))
            else:
                menu.add_command(label="❌ Apagar Arquivo", command=lambda: self.after(10, lambda: self.acao_multipla("apagar")))
                menu.add_command(label="📄 Copiar para...", command=lambda: self.after(10, lambda: self.acao_multipla("copiar")))
                menu.add_command(label="📦 Mover para...", command=lambda: self.after(10, lambda: self.acao_multipla("mover")))
        else:
            menu.add_command(label=f"❌ Apagar ({qtd}) itens", command=lambda: self.after(10, lambda: self.acao_multipla("apagar")))
            menu.add_command(label=f"📄 Copiar ({qtd}) itens para...", command=lambda: self.after(10, lambda: self.acao_multipla("copiar")))
            menu.add_command(label=f"📦 Mover ({qtd}) itens para...", command=lambda: self.after(10, lambda: self.acao_multipla("mover")))
            
        menu.post(event.x_root, event.y_root)

    def acao_multipla(self, acao):
        itens = list(self.itens_selecionados)
        if not itens: return

        if acao == "apagar":
            texto_msg = f"Deseja realmente apagar os {len(itens)} itens selecionados?" if len(itens) > 1 else f"Deseja apagar este item permanentemente?"
            if messagebox.askyesno("Confirmar Exclusão", texto_msg, parent=self.janela_gerenciador):
                try:
                    for caminho in itens:
                        if os.path.isdir(caminho): shutil.rmtree(caminho)
                        else: os.remove(caminho)
                    self.atualizar_lista_gerenciador()
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro ao apagar: {e}", parent=self.janela_gerenciador)

        elif acao == "copiar":
            destino = filedialog.askdirectory(title="Selecione a pasta de destino para COPIAR", parent=self.janela_gerenciador)
            if destino:
                try:
                    for caminho in itens:
                        if os.path.isdir(caminho):
                            shutil.copytree(caminho, os.path.join(destino, os.path.basename(caminho)), dirs_exist_ok=True)
                        else:
                            shutil.copy2(caminho, destino)
                    messagebox.showinfo("Sucesso", f"{len(itens)} item(ns) copiado(s) com sucesso!", parent=self.janela_gerenciador)
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro ao copiar: {e}", parent=self.janela_gerenciador)

        elif acao == "mover":
            destino = filedialog.askdirectory(title="Selecione a pasta de destino para MOVER", parent=self.janela_gerenciador)
            if destino:
                try:
                    for caminho in itens:
                        shutil.move(caminho, destino)
                    self.atualizar_lista_gerenciador()
                    messagebox.showinfo("Sucesso", f"{len(itens)} item(ns) movido(s) com sucesso!", parent=self.janela_gerenciador)
                except Exception as e:
                    messagebox.showerror("Erro", f"Ocorreu um erro ao mover: {e}", parent=self.janela_gerenciador)

    def mudar_status(self, mensagem, cor_fundo, cor_texto):
        self.after(0, lambda: self.lbl_status.configure(text=mensagem, fg_color=cor_fundo, text_color=cor_texto))

    def exibir_popup(self, titulo, mensagem, pasta_destino=None):
        popup = ctk.CTkToplevel(self)
        popup.title(titulo)
        largura, altura = 400, 180
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        popup.geometry(f"{largura}x{altura}+{x}+{y}")
        popup.resizable(False, False)
        popup.transient(self)
        
        popup.attributes('-topmost', True)
        popup.after(200, popup.grab_set)
        popup.after(250, lambda: popup.focus_force())
        popup.after(300, lambda: popup.attributes('-topmost', False))

        lbl_msg = ctk.CTkLabel(popup, text=mensagem, font=("Segoe UI", 14), justify="center")
        lbl_msg.pack(pady=(35, 25), padx=20)

        paleta = self.cores_destaque[self.combo_cor.get()]
        frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
        frame_btns.pack()

        if pasta_destino:
            def fechar_e_continuar():
                popup.destroy()
            btn_ok = ctk.CTkButton(frame_btns, text="OK", width=120, height=35, command=fechar_e_continuar,
                                   fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            btn_ok.pack()
        else:
            btn_ok = ctk.CTkButton(frame_btns, text="OK", width=120, height=35, command=popup.destroy,
                                   fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            btn_ok.pack()
        
        popup.bind("<Return>", lambda e: popup.destroy())
        self._aplicar_icone(popup)

    def mostrar_assinatura(self, event):
        self.exibir_popup("Fiuza Technology", "Aplicação desenvolvida por Felipe Fiuza\n\nFiuza Technology - Development & Software Solutions")

    def aplicar_tema_inicial(self):
        config = carregar_config()
        if config.get("primeira_execucao", True):
            modo_salvo = "Light"
            cor_salva = "Azul"
            auto_update_salvo = True
            salvar_tema(modo_salvo, cor_salva, auto_update_salvo)
            config["primeira_execucao"] = False
            salvar_config(config)
        else:
            modo_salvo, cor_salva, auto_update_salvo = carregar_tema()

        self.combo_modo.set(modo_salvo)
        self.combo_cor.set(cor_salva if cor_salva in self.cores_destaque else "Azul")
        self.auto_update = auto_update_salvo
        self.mudar_tema(None)

    def mudar_tema(self, _):
        modo = self.combo_modo.get()
        cor = self.combo_cor.get()
        ctk.set_appearance_mode(modo)
        paleta = self.cores_destaque[cor]
        
        if modo == "Light":
            self.configure(fg_color="#E8ECEF")
            self.frame_principal.configure(fg_color="#FFFFFF", border_color="#D1D1D1")
            self.lbl_versao.configure(text_color="#888888")
            self.lbl_path.configure(text_color="#888888")
            bg_status, fg_status = "#F8F9FA", "#000000"
            cor_engrenagem = "#222222"
        else:
            self.configure(fg_color="#0F0F0F")
            self.frame_principal.configure(fg_color="#1E1E1E", border_color="#333333")
            self.lbl_versao.configure(text_color="#AAAAAA")
            self.lbl_path.configure(text_color="#AAAAAA")
            bg_status, fg_status = "#2C2C2C", "#FFFFFF"
            cor_engrenagem = "#EEEEEE"

        self.frame_logo.configure(border_color=paleta["fg"])

        for btn in [self.btn_gerar, self.btn_cancelar, self.btn_novo]:
            btn.configure(fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            
        self.progressbar.configure(progress_color=paleta["fg"])
        self.btn_config.configure(text_color=cor_engrenagem, hover_color=paleta["hover"])
        
        self.btn_abrir_gerenciador_main.configure(
            border_color=paleta["fg"], 
            border_width=2,
            text_color=paleta["fg"] if modo == "Light" else "#FFFFFF", 
            fg_color=paleta["fg"] if modo == "Dark" else "transparent",
            hover_color=paleta["hover"]
        )
        
        for el in [self.combo_versao, self.combo_path, self.combo_modo, self.combo_cor]:
            el.configure(border_color=paleta["fg"], button_color=paleta["fg"], button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"])
            
        self.logs.configure(border_color=paleta["fg"], border_width=2)
        self.lbl_status.configure(fg_color=bg_status, text_color=fg_status)
        
        salvar_tema(modo, cor, self.auto_update)

    def carregar_paths(self, versao):
        self.combo_path.configure(state="normal")
        if versao in ["instaladores", "sistema_operacional"]:
            self.combo_path.configure(values=["Não se aplica"])
            self.combo_path.set("Não se aplica")
            self.combo_path.configure(state="disabled")
            self.log(f"Pasta especial '{versao}' selecionada.")
        else:
            paths = get_paths(versao)
            self.combo_path.configure(values=paths)
            if paths:
                self.combo_path.set(paths[0])
            else:
                self.combo_path.set("Selecione aqui o path desejado")
            self.log(f"Paths carregados para {versao}")

    def log(self, mensagem):
        self.after(0, lambda: self._inserir_log(mensagem))

    def _inserir_log(self, mensagem):
        self.logs.configure(state="normal")
        posicao = self.logs.yview()
        ta_no_fundo = True if not posicao else (posicao[1] >= 0.90)
        self.logs.insert("end", f"{mensagem}\n")
        self.logs.configure(state="disabled")
        if ta_no_fundo:
            self.logs.see("end")

    def atualizar_progresso(self, valor_float, texto_stats, nome_arquivo):
        self.after(0, lambda: self.progressbar.set(valor_float))
        self.after(0, lambda: self.lbl_porcentagem.configure(text=texto_stats))
        self.after(0, lambda: self.lbl_arquivo.configure(text=f"Baixando: {nome_arquivo}"))
        
        if nome_arquivo and nome_arquivo not in self.historico_arquivos:
            self.historico_arquivos.append(nome_arquivo)
            self.after(0, lambda n=nome_arquivo: self.bloqueio_manager.adicionar_arquivo_painel(n, concluido=False))
            
        self.after(0, lambda n=nome_arquivo, v=valor_float, t=texto_stats: self.bloqueio_manager.atualizar_status(n, v, t))

    def acionar_cancelamento(self):
        self.flag_cancelar = True
        self.btn_cancelar.configure(state="disabled", text="CANCELANDO...")
        self.mudar_status("⚠️ Cancelamento solicitado. Interrompendo...", "#ffc107", "#000000")

    def checar_cancelamento(self):
        return self.flag_cancelar
        
    def abrir_configuracoes(self):
        modal_cfg = ctk.CTkToplevel(self)
        modal_cfg.title("Configurações do Sistema")
        # Aumentei a altura de 260 para 320 para acomodar o novo botão com folga
        largura, altura = 400, 320
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        modal_cfg.geometry(f"{largura}x{altura}+{x}+{y}")
        modal_cfg.resizable(False, False)
        modal_cfg.transient(self)
        
        modal_cfg.attributes('-topmost', True)
        modal_cfg.after(200, modal_cfg.grab_set)
        modal_cfg.after(250, lambda: modal_cfg.focus_force())
        modal_cfg.after(300, lambda: modal_cfg.attributes('-topmost', False))

        paleta = self.cores_destaque[self.combo_cor.get()]
        try:
            img_logo_path = obter_caminho("assets/logotipo.png")
            self.img_logotipo_modal = ctk.CTkImage(light_image=Image.open(img_logo_path), size=(180, 50))
            lbl_img_logo = ctk.CTkLabel(modal_cfg, image=self.img_logotipo_modal, text="")
            lbl_img_logo.pack(pady=(20, 5))
        except Exception:
            pass

        lbl_nome_app = ctk.CTkLabel(modal_cfg, text="Fiuza Technology - Pack Full Aplicação Socin", font=("Segoe UI", 13, "bold"))
        lbl_nome_app.pack(pady=(0, 5))
        lbl_versao_app = ctk.CTkLabel(modal_cfg, text=f"Versão Instalada: {self.VERSAO_PROGRAMA}", font=("Segoe UI", 12))
        lbl_versao_app.pack(pady=(0, 15))

        self.switch_var = ctk.BooleanVar(value=self.auto_update)
        switch_update = ctk.CTkSwitch(modal_cfg, text="Atualizar automaticamente (GitHub)", variable=self.switch_var, command=self.salvar_config_modal, progress_color=paleta["fg"])
        switch_update.pack(pady=(10, 15))

        # --- NOVO BOTÃO DE INTEGRAÇÃO NUVEM ---
        btn_nuvem = ctk.CTkButton(
            modal_cfg, 
            text="☁️ Alternar para integração API Nuvem Ilimitada", 
            height=35, 
            fg_color="#17a2b8", 
            hover_color="#138496", 
            text_color="#FFFFFF",
            corner_radius=8,
            command=self.acionar_api_nuvem
        )
        btn_nuvem.pack(pady=(0, 15), fill="x", padx=30)
        # --------------------------------------

        btn_fechar_cfg = ctk.CTkButton(modal_cfg, text="FECHAR", width=120, height=32, command=modal_cfg.destroy, fg_color="#6c757d", hover_color="#5a6268", text_color="#FFFFFF")
        btn_fechar_cfg.pack(pady=(0, 15))
        self._aplicar_icone(modal_cfg)

    def salvar_config_modal(self):
        self.auto_update = self.switch_var.get()
        salvar_tema(self.combo_modo.get(), self.combo_cor.get(), self.auto_update)
        self.log(f"Status do Auto-Update alterado para: {self.auto_update}")

    # --- LÓGICA DE TRANSIÇÃO ---
    def acionar_api_nuvem(self):
        self.log("[SISTEMA] Preparando ambiente da Nuvem Ilimitada (Telegram API)...")
        self.mudar_status("☁️ Conectando à nuvem...", "#17a2b8", "#FFFFFF")
        self.after(500, self._abrir_telegram_cloud)

    def _abrir_telegram_cloud(self):
        import subprocess
        try:
            if getattr(sys, 'frozen', False):
                # Se for o executável compilado (.exe)
                caminho_exe = os.path.join(os.path.dirname(sys.executable), "TelegramCloud.exe")
                if os.path.exists(caminho_exe):
                    subprocess.Popen([caminho_exe])
                else:
                    messagebox.showerror("Erro", "O módulo da Nuvem (TelegramCloud.exe) não foi encontrado na pasta de instalação.")
                    return
            else:
                pasta_ui = os.path.dirname(os.path.abspath(__file__))
                pasta_raiz = os.path.dirname(pasta_ui)
                
                # Sistema Inteligente de Busca: Tenta encontrar o arquivo nas rotas mais prováveis
                possiveis_caminhos = [
                    os.path.join(pasta_raiz, "telegram_api", "telegram_cloud_app.py"),     # Se estiver na raiz
                    os.path.join(pasta_ui, "telegram_api", "telegram_cloud_app.py"),       # Se estiver dentro da ui
                    os.path.join(pasta_raiz, "telegram_api", "telegram_cloud_app.py.py"),  # Se o Windows duplicou o .py
                    os.path.join(pasta_raiz, "telegram_cloud_app.py")                      # Se estiver solto na raiz
                ]
                
                caminho_script = None
                for caminho in possiveis_caminhos:
                    if os.path.exists(caminho):
                        caminho_script = caminho
                        break
                
                if caminho_script:
                    # Se achou, abre garantindo que a raiz do projeto seja o local de trabalho
                    subprocess.Popen([sys.executable, caminho_script], cwd=pasta_raiz)
                else:
                    # Se não achou em nenhum lugar, abre uma janela para o usuário escolher o arquivo!
                    messagebox.showwarning("Aviso", "O sistema não encontrou o arquivo automaticamente.\n\nPor favor, localize e selecione o arquivo 'telegram_cloud_app.py' na próxima janela.")
                    caminho_script = filedialog.askopenfilename(
                        title="Selecione o arquivo telegram_cloud_app.py",
                        filetypes=[("Python Files", "*.py")]
                    )
                    
                    if caminho_script:
                        subprocess.Popen([sys.executable, caminho_script], cwd=pasta_raiz)
                    else:
                        self.mudar_status("❌ Operação Cancelada", "#dc3545", "#FFFFFF")
                        return # Usuário cancelou a seleção manual
            
            # Fecha a janela atual encerrando o processo limpamente
            self.destroy()
            sys.exit(0)
            
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Não foi possível iniciar a Nuvem: {e}")
            self.log(f"[ERRO] Falha ao alternar para nuvem: {e}")

    def abrir_modal_opcoes(self):
        versao = self.combo_versao.get()
        path = self.combo_path.get()
        
        textos_invalidos = ["Selecione aqui a versao desejada", "Selecione aqui o path desejado", "Selecione", ""]
        if versao in textos_invalidos or path in textos_invalidos:
            messagebox.showerror("Aviso", "Selecione os campos desejados - Versao e Patch.")
            return

        lista_arquivos = gerar_arquivos(versao, path)
        nomes_arquivos = [item["arquivo"] for item in lista_arquivos]

        self.modal = ctk.CTkToplevel(self)
        self.modal.title("Opções")
        modal_width, modal_height = 500, 370
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (modal_width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (modal_height // 2)
        self.modal.geometry(f"{modal_width}x{modal_height}+{x}+{y}")
        self.modal.resizable(False, False)
        self.modal.transient(self)
        
        self.modal.attributes('-topmost', True)
        self.modal.after(200, self.modal.grab_set)
        self.modal.after(250, lambda: self.modal.focus_force())
        self.modal.after(300, lambda: self.modal.attributes('-topmost', False))

        lbl_titulo = ctk.CTkLabel(self.modal, text="Escolha o pacote abaixo:", font=("Segoe UI", 18, "bold"))
        lbl_titulo.pack(pady=(15, 10))

        self.modo_var = ctk.StringVar(value="completo")
        paleta = self.cores_destaque[self.combo_cor.get()]

        if versao == "sistema_operacional":
            self.modo_var.set("individual") 
            lbl_info = ctk.CTkLabel(self.modal, text="Para sistemas operacionais, baixe um arquivo por vez.", font=("Segoe UI", 13))
            lbl_info.pack(pady=(10, 15))
            self.combo_arquivos_modal = ctk.CTkComboBox(self.modal, values=nomes_arquivos, width=380, state="normal", border_color=paleta["fg"], button_color=paleta["fg"], button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"])
            self.combo_arquivos_modal.pack(pady=10)
            self.btn_confirmar = ctk.CTkButton(self.modal, text="CONFIRMAR", command=lambda: self.iniciar_fluxo("individual", self.combo_arquivos_modal.get()), fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            self.btn_confirmar.pack(pady=25)

        elif versao == "instaladores":
            rb_completo = ctk.CTkRadioButton(self.modal, text="Baixar Todos (Selecione 32 ou 64 Bits)", variable=self.modo_var, value="completo", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_completo.pack(pady=5, padx=20, anchor="w")
            rb_individual = ctk.CTkRadioButton(self.modal, text="Pacote Individual (Baixar apenas um arquivo)", variable=self.modo_var, value="individual", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_individual.pack(pady=5, padx=20, anchor="w")
            self.combo_arquivos_modal = ctk.CTkComboBox(self.modal, values=nomes_arquivos, width=380, state="disabled", border_color=paleta["fg"], button_color=paleta["fg"], button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"])
            self.combo_arquivos_modal.pack(pady=10)
            self.frame_botoes = ctk.CTkFrame(self.modal, fg_color="transparent")
            self.btn_32 = ctk.CTkButton(self.frame_botoes, text="32 BITS", command=lambda: self.iniciar_fluxo("completo", None, bits="32"), fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            self.btn_32.pack(side="left", padx=10)
            self.btn_64 = ctk.CTkButton(self.frame_botoes, text="64 BITS", command=lambda: self.iniciar_fluxo("completo", None, bits="64"), fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            self.btn_64.pack(side="right", padx=10)
            self.btn_confirmar = ctk.CTkButton(self.modal, text="CONFIRMAR", command=lambda: self.iniciar_fluxo("individual", self.combo_arquivos_modal.get()), fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            self.atualizar_estado_combo()
        else:
            rb_completo = ctk.CTkRadioButton(self.modal, text="Pacote Completo (Baixar Todos)", variable=self.modo_var, value="completo", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_completo.pack(pady=5, padx=20, anchor="w")
            rb_atualizadores = ctk.CTkRadioButton(self.modal, text="Pacote Atualizadores (Baixa só os atualizadores)", variable=self.modo_var, value="atualizadores", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_atualizadores.pack(pady=5, padx=20, anchor="w")
            rb_individual = ctk.CTkRadioButton(self.modal, text="Pacote Individual (Baixar apenas um arquivo)", variable=self.modo_var, value="individual", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_individual.pack(pady=5, padx=20, anchor="w")
            self.combo_arquivos_modal = ctk.CTkComboBox(self.modal, values=nomes_arquivos, width=380, state="disabled", border_color=paleta["fg"], button_color=paleta["fg"], button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"])
            self.combo_arquivos_modal.pack(pady=10)
            self.btn_confirmar = ctk.CTkButton(self.modal, text="CONFIRMAR", command=self.verificar_restaurante, fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            self.btn_confirmar.pack(pady=15)
        self._aplicar_icone(self.modal)

    def atualizar_estado_combo(self):
        if not hasattr(self, 'combo_arquivos_modal') or not self.combo_arquivos_modal.winfo_exists(): return
        modo = self.modo_var.get()
        versao = self.combo_versao.get()
        if modo == "individual":
            self.combo_arquivos_modal.configure(state="normal")
            if versao == "instaladores":
                if hasattr(self, 'frame_botoes') and self.frame_botoes.winfo_ismapped(): self.frame_botoes.pack_forget()
                if hasattr(self, 'btn_confirmar') and not self.btn_confirmar.winfo_ismapped(): self.btn_confirmar.pack(pady=15)
        else:
            self.combo_arquivos_modal.configure(state="disabled")
            if versao == "instaladores":
                if hasattr(self, 'btn_confirmar'): self.btn_confirmar.pack_forget()
                if hasattr(self, 'frame_botoes'): self.frame_botoes.pack(pady=15)

    def verificar_restaurante(self):
        modo = self.modo_var.get()
        arq = self.combo_arquivos_modal.get() if modo == "individual" else None
        self.modal.destroy()
        if modo == "completo": self.perguntar_restaurante(modo, arq)
        else: self.iniciar_fluxo(modo, arq)

    def perguntar_restaurante(self, modo, arq):
        popup = ctk.CTkToplevel(self)
        popup.title("Módulo Opcional")
        largura, altura = 360, 160
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        popup.geometry(f"{largura}x{altura}+{x}+{y}")
        popup.resizable(False, False)
        popup.transient(self)
        
        popup.attributes('-topmost', True)
        popup.after(200, popup.grab_set)
        popup.after(250, lambda: popup.focus_force())
        popup.after(300, lambda: popup.attributes('-topmost', False))

        lbl_msg = ctk.CTkLabel(popup, text="Incluir módulo Restaurante (RES)?", font=("Segoe UI", 16, "bold"))
        lbl_msg.pack(pady=(25, 20))
        frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
        frame_btns.pack(pady=5)
        paleta = self.cores_destaque[self.combo_cor.get()]
        
        def on_sim(): popup.destroy(); self.iniciar_fluxo(modo, arq, incluir_restaurante=True)
        def on_nao(): popup.destroy(); self.iniciar_fluxo(modo, arq, incluir_restaurante=False)
            
        btn_sim = ctk.CTkButton(frame_btns, text="Sim", command=on_sim, width=100, fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
        btn_sim.pack(side="left", padx=15)
        btn_nao = ctk.CTkButton(frame_btns, text="Não", command=on_nao, width=100, fg_color="#dc3545", hover_color="#c82333", text_color="#FFFFFF")
        btn_nao.pack(side="right", padx=15)
        self._aplicar_icone(popup)

    def iniciar_fluxo(self, modo, arq, incluir_restaurante=False, bits=None):
        versao_selecionada = self.combo_versao.get()
        path_selecionado = self.combo_path.get()
        
        if hasattr(self, 'modal') and self.modal.winfo_exists(): 
            self.modal.destroy()
            
        lista_arquivos = gerar_arquivos(versao_selecionada, path_selecionado)
        if modo == "individual":
            self.total_arquivos_sessao = 1
        else:
            self.total_arquivos_sessao = len(lista_arquivos)
            
        threading.Thread(target=self.gerar_pack, args=(modo, arq, incluir_restaurante, bits, versao_selecionada, path_selecionado)).start()

    def gerar_pack(self, modo, arquivo_selecionado, incluir_restaurante, bits, versao, path):
        try:
            self.flag_cancelar = False
            self.is_downloading = True
            
            self.historico_arquivos.clear()
            self.after(0, lambda: self.bloqueio_manager.sincronizar_painel_topo())
            
            self.after(0, lambda: self.btn_cancelar.configure(state="normal", text="CANCELAR"))
            self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa("Iniciando download..."))
            
            self.mudar_status("⬇️ Baixando pacotes...", "#007BFF", "#FFFFFF")

            self.after(0, lambda: self.btn_gerar.pack_forget()) 
            self.after(0, lambda: self.frame_pos_download.pack_forget()) 
            self.after(0, lambda: self.lbl_arquivo.pack(pady=(5, 5), before=self.logs))
            self.after(0, lambda: self.progressbar.pack(pady=(0, 5), before=self.logs))
            self.after(0, lambda: self.lbl_porcentagem.pack(pady=(0, 10), before=self.logs))
            self.after(0, lambda: self.btn_cancelar.pack(pady=(0, 15), before=self.logs))

            self.log("================================")
            self.log(f"Modo: {modo.upper()}")
            
            baixar_arquivos(
                versao, path, log_callback=self.log, progress_callback=self.atualizar_progresso,
                cancel_callback=self.checar_cancelamento, apenas_arquivo=arquivo_selecionado,
                modo=modo, incluir_restaurante=incluir_restaurante, bits=bits
            )

            if self.flag_cancelar:
                self.mudar_status("❌ Download cancelado!", "#dc3545", "#FFFFFF")
                self.log("================================")
                self.log("PROCESSO ABORTADO. Arquivos preservados.")
                self.after(0, lambda: self._restaurar_botoes(sucesso=False))
                return

            pasta_temp = f"temp/{versao}" if versao in ["instaladores", "sistema_operacional"] else f"temp/{versao}_{path}"
            self.pasta_concluida = pasta_temp

            self.after(0, lambda: self.bloqueio_manager.finalizar_painel_topo())
            self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa("Download concluído! 🚀"))

            if versao not in ["instaladores", "sistema_operacional"] and modo in ["completo", "atualizadores"]:
                nome_zip = f"output/PACK_{'FULL' if modo == 'completo' else 'ATUALIZADORES'}_{versao.replace('.', '_')}_{path}.zip"
                self.after(0, lambda: self.perguntar_compactacao(pasta_temp, nome_zip))
                return
            else:
                self.log(f"ARQUIVOS SALVOS NA PASTA: {pasta_temp}")

            self.mudar_status("🚀 Download concluído com sucesso!", "#28a745", "#FFFFFF")
            self.after(0, lambda: self.exibir_popup("Concluído", "Download concluído com sucesso! 🚀"))
            self.after(0, lambda: self._restaurar_botoes(sucesso=True))

        except Exception as e:
            self.mudar_status("❌ Erro Crítico no processo", "#dc3545", "#FFFFFF")
            self.log(f"ERRO CRÍTICO: {str(e)}")
            self.after(0, lambda: self._restaurar_botoes(sucesso=False))

    def perguntar_compactacao(self, pasta_temp, nome_arquivo_final):
        popup = ctk.CTkToplevel(self)
        popup.title("Download Concluído")
        largura, altura = 380, 160
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        popup.geometry(f"{largura}x{altura}+{x}+{y}")
        popup.resizable(False, False)
        popup.transient(self)
        
        popup.attributes('-topmost', True)
        popup.after(200, popup.grab_set)
        popup.after(250, lambda: popup.focus_force())
        popup.after(300, lambda: popup.attributes('-topmost', False))

        lbl = ctk.CTkLabel(popup, text="Downloads finalizados!\nDeseja compactar os arquivos (.zip)?", font=("Segoe UI", 14, "bold"))
        lbl.pack(pady=20)
        paleta = self.cores_destaque[self.combo_cor.get()]

        def iniciar_compactacao():
            popup.destroy()
            threading.Thread(target=self._processar_compactacao, args=(pasta_temp, nome_arquivo_final)).start()

        def pular_compactacao():
            popup.destroy()
            self.log(f"ARQUIVOS SALVOS NA PASTA: {pasta_temp}")
            self.mudar_status("🚀 Download concluído com sucesso!", "#28a745", "#FFFFFF")
            self.exibir_popup("Concluído", "Arquivos mantidos na pasta temp.\nDownload concluído! 🚀")
            self._restaurar_botoes(sucesso=True)

        frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
        frame_btns.pack(fill="x", padx=40)
        btn_sim = ctk.CTkButton(frame_btns, text="Sim", command=iniciar_compactacao, width=120, fg_color=paleta["fg"], hover_color=paleta["hover"])
        btn_sim.pack(side="left", padx=10)
        btn_nao = ctk.CTkButton(frame_btns, text="Não", fg_color="#6c757d", hover_color="#5a6268", command=pular_compactacao, width=120)
        btn_nao.pack(side="right", padx=10)
        self._aplicar_icone(popup)

    def _processar_compactacao(self, pasta_temp, nome_arquivo_final):
        try:
            os.makedirs("output", exist_ok=True)
            self.log("Compactando arquivos...")
            self.mudar_status("📦 Compactando arquivos...", "#FF8C00", "#FFFFFF")
            
            criar_zip(pasta_temp, nome_arquivo_final, log_callback=self.log)
            shutil.rmtree(pasta_temp)
            self.pasta_concluida = nome_arquivo_final

            self.log(f"PACK SALVO EM: {nome_arquivo_final}")
            self.mudar_status("🚀 Download e Compactação concluídos!", "#28a745", "#FFFFFF")
            self.after(0, lambda: self.exibir_popup("Concluído", "Processo concluído com sucesso! 🚀"))
        except Exception as e:
            self.log(f"ERRO AO COMPACTAR: {str(e)}")
            self.mudar_status("❌ Erro na compactação", "#dc3545", "#FFFFFF")
            self.after(0, lambda: self._restaurar_botoes(sucesso=False))
        else:
            self.after(0, lambda: self._restaurar_botoes(sucesso=True))

    def _restaurar_botoes(self, sucesso=False):
        self.is_downloading = False
        self.after(0, lambda: self.bloqueio_manager.definir_mensagem_fixa("Download pendente...", esconder_barra=True))
        
        self.btn_cancelar.pack_forget()
        self.lbl_arquivo.pack_forget()
        self.progressbar.pack_forget()
        self.lbl_porcentagem.pack_forget()
        self.btn_gerar.pack_forget()
        
        if sucesso:
            self.frame_pos_download.pack(pady=8, before=self.logs)
        else:
            self.btn_gerar.pack(pady=8, before=self.logs)