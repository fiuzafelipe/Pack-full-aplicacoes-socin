import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import cv2 
from PIL import Image
from utils import obter_caminho

class TelaDeBloqueio:
    def __init__(self, app):
        self.app = app
        self.lock_frame = None
        self.lbl_fundo = None
        self.target_label_fundo = None 
        self.midias = []
        self.idx_midia = 0
        self.timer_id = None
        self.video_after_id = None
        self.video_cap = None
        self.arquivos_vistos = set()
        self.current_bg_img = None 
        
        self.app.bind_all("<Button-3>", self.mostrar_menu_contexto)
        self.app.bind_all("<Return>", self.sair_bloqueio_tecla)

    def mostrar_menu_contexto(self, event):
        try:
            if self.lock_frame is not None: return
            if hasattr(self.app, 'senha_frame') and self.app.senha_frame.winfo_ismapped(): return
            
            # --- TRAVA NOVA: Ignora o clique direito se estiver na tela de Login ---
            if hasattr(self.app, 'login_frame') and self.app.login_frame.winfo_ismapped(): return 
            # ------------------------------------------------------------------------
            
            if event.widget.winfo_toplevel() != self.app: return

            menu = tk.Menu(self.app, tearoff=0, font=("Segoe UI", 10))
            menu.add_command(label="🔒 Plano de Bloqueio", command=self.ativar_bloqueio_tela_cheia)
            menu.post(event.x_root, event.y_root)
        except Exception: pass

    def carregar_midias(self):
        pasta_assets = obter_caminho(os.path.join("assets", "wallpaper"))
        os.makedirs(pasta_assets, exist_ok=True)
        extensoes_suportadas = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv')
        self.midias = [os.path.join(pasta_assets, f) for f in os.listdir(pasta_assets) if f.lower().endswith(extensoes_suportadas)]
        return len(self.midias) > 0

    def iniciar_apresentacao(self, label_fundo):
        if not self.carregar_midias(): return
        self.target_label_fundo = label_fundo
        self.idx_midia = 0
        self.parar_apresentacao() 
        self.transicionar_midia()

    def parar_apresentacao(self):
        if self.timer_id: self.app.after_cancel(self.timer_id); self.timer_id = None
        if self.video_after_id: self.app.after_cancel(self.video_after_id); self.video_after_id = None
        if self.video_cap: self.video_cap.release(); self.video_cap = None
        self.current_bg_img = None

    def ativar_bloqueio_tela_cheia(self):
        if not self.carregar_midias():
            pasta_assets = obter_caminho(os.path.join("assets", "wallpaper"))
            messagebox.showinfo("Plano de Bloqueio", f"Nenhuma imagem ou vídeo encontrado.\nPor favor, adicione arquivos na pasta:\n{pasta_assets}")
            return

        self.lock_frame = ctk.CTkFrame(self.app, corner_radius=0, fg_color="#000000")
        self.lock_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.lbl_fundo = ctk.CTkLabel(self.lock_frame, text="", fg_color="#000000")
        self.lbl_fundo.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        
        self.frame_topo_concluido = ctk.CTkFrame(self.lock_frame, width=520, height=90, fg_color="#0A0A0A", border_width=2, border_color=paleta["fg"], corner_radius=0)
        self.frame_topo_concluido.pack_propagate(False)
        frame_header = ctk.CTkFrame(self.frame_topo_concluido, fg_color="transparent")
        frame_header.pack(fill="x", padx=15, pady=(5, 0))
        self.lbl_contador_atual = ctk.CTkLabel(frame_header, text="0", font=("Segoe UI Black", 14), text_color=paleta["fg"])
        self.lbl_contador_atual.pack(side="left")
        self.lbl_titulo_topo = ctk.CTkLabel(frame_header, text="SISTEMA OCIOSO", font=("Segoe UI Black", 12), text_color=paleta["fg"])
        self.lbl_titulo_topo.pack(side="left", expand=True)
        self.lbl_contador_total = ctk.CTkLabel(frame_header, text="0", font=("Segoe UI Black", 14), text_color=paleta["fg"])
        self.lbl_contador_total.pack(side="right")
        self.scroll_files = ctk.CTkScrollableFrame(self.frame_topo_concluido, orientation="horizontal", height=32, fg_color="transparent")
        self.scroll_files.pack(fill="both", expand=True, padx=5, pady=(0, 2))
        self.progressbar_topo = ctk.CTkProgressBar(self.frame_topo_concluido, mode="determinate", height=4, corner_radius=0)
        self.progressbar_topo.set(0)
        self.progressbar_topo.configure(progress_color=paleta["fg"])
        self.progressbar_topo.pack(fill="x", padx=20, pady=(0, 6))
        
        self.frame_central = ctk.CTkFrame(self.lock_frame, width=350, height=80, corner_radius=0, fg_color="#0A0A0A", border_width=2, border_color=paleta["fg"])
        self.frame_central.place(relx=0.5, rely=0.45, anchor="center")
        lbl_msg = ctk.CTkLabel(self.frame_central, text="Modo Apresentação Ativo\nClique ou aperte ENTER para retornar", font=("Segoe UI", 16, "bold"), text_color="#FFFFFF")
        lbl_msg.pack(pady=20, padx=30)

        self.frame_bottom = ctk.CTkFrame(self.lock_frame, corner_radius=0, fg_color="#0A0A0A", border_width=2, border_color=paleta["fg"])
        self.frame_bottom.place(relx=0.5, rely=0.88, anchor="center", relwidth=0.8)
        self.lbl_bloqueio_arquivo = ctk.CTkLabel(self.frame_bottom, text="Aguardando...", font=("Segoe UI", 16, "bold"), text_color="#FFFFFF", anchor="center", justify="center")
        self.lbl_bloqueio_arquivo.pack(pady=(15, 5), fill="x")
        self.bloqueio_progressbar = ctk.CTkProgressBar(self.frame_bottom, mode="determinate", height=12, corner_radius=0)
        self.bloqueio_progressbar.set(0)
        self.bloqueio_progressbar.configure(progress_color=paleta["fg"])
        self.bloqueio_progressbar.pack(fill="x", padx=30, pady=5)
        self.lbl_bloqueio_stats = ctk.CTkLabel(self.frame_bottom, text="", font=("Segoe UI", 14, "bold"), text_color="#FFFFFF", anchor="center", justify="center")
        self.lbl_bloqueio_stats.pack(pady=(5, 15), fill="x")

        if not getattr(self.app, 'is_downloading', False): self.bloqueio_progressbar.pack_forget()

        self.lbl_fundo.bind("<Button-1>", self.sair_bloqueio)
        self.frame_central.bind("<Button-1>", self.sair_bloqueio)
        lbl_msg.bind("<Button-1>", self.sair_bloqueio)
        self.frame_bottom.bind("<Button-1>", self.sair_bloqueio)
        self.frame_topo_concluido.bind("<Button-1>", self.sair_bloqueio)

        self.iniciar_apresentacao(self.lbl_fundo)
        self.sincronizar_painel_topo()

    def sincronizar_painel_topo(self):
        if not self.lock_frame: return
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        self.arquivos_vistos.clear()
        for widget in self.scroll_files.winfo_children(): widget.destroy()

        self.frame_topo_concluido.place(relx=0.5, rely=0.03, anchor="n")
        self.frame_topo_concluido.lift() 

        if self.app.is_downloading:
            self.lbl_titulo_topo.configure(text="OPERAÇÕES EM ANDAMENTO", text_color=paleta["fg"])
            for arq in self.app.historico_arquivos:
                self.adicionar_arquivo_painel(arq, concluido=False)
        elif self.app.historico_arquivos:
            self.lbl_titulo_topo.configure(text="CONCLUÍDO", text_color=paleta["fg"])
            self.progressbar_topo.set(1.0)
            for arq in self.app.historico_arquivos:
                self.adicionar_arquivo_painel(arq, concluido=True)
        else:
            self.lbl_titulo_topo.configure(text="SISTEMA OCIOSO", text_color=paleta["fg"])
            self.progressbar_topo.set(0)

    def adicionar_arquivo_painel(self, nome_arquivo, concluido=False):
        if not self.lock_frame: return
        if not nome_arquivo or nome_arquivo in self.arquivos_vistos: return
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
        self.progressbar_topo.set(atual / total if total > 0 else 0)
        try: self.scroll_files._parent_canvas.xview_moveto(1.0)
        except: pass

    def finalizar_painel_topo(self):
        if not self.lock_frame: return
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        self.lbl_titulo_topo.configure(text="CONCLUÍDO", text_color=paleta["fg"])
        self.progressbar_topo.set(1.0)
        for frame in self.scroll_files.winfo_children():
            for child in frame.winfo_children():
                if child.cget("text") == "⏳": child.configure(text="✅")

    def transicionar_midia(self):
        if not self.midias or self.target_label_fundo is None: return
        caminho_midia = self.midias[self.idx_midia]
        extensao = os.path.splitext(caminho_midia)[1].lower()

        if extensao in ['.mp4', '.avi', '.mov', '.mkv']: self.reproduzir_video(caminho_midia)
        else: self.mostrar_imagem(caminho_midia)

    def mostrar_imagem(self, caminho_img):
        if self.target_label_fundo is None: return
        try:
            pil_img = Image.open(caminho_img)
            w, h = self._obter_dimensoes_alvo()
            self.current_bg_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
            self.target_label_fundo.configure(image=self.current_bg_img)
        except Exception: pass
        self.idx_midia = (self.idx_midia + 1) % len(self.midias)
        self.timer_id = self.app.after(15000, self.transicionar_midia)

    def reproduzir_video(self, caminho_video):
        self.video_cap = cv2.VideoCapture(caminho_video)
        fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps != fps: fps = 30
        self.delay_frame = int(1000 / fps)
        self._tocar_frame()

    def _tocar_frame(self):
        if self.target_label_fundo is None or not self.video_cap: return
        ret, frame = self.video_cap.read()
        if ret:
            w, h = self._obter_dimensoes_alvo()
            frame_resized = cv2.resize(frame, (w, h))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            self.current_bg_img = ctk.CTkImage(light_image=pil_img, size=(w, h))
            self.target_label_fundo.configure(image=self.current_bg_img)
            self.video_after_id = self.app.after(self.delay_frame, self._tocar_frame)
        else:
            self.video_cap.release()
            self.video_cap = None
            self.idx_midia = (self.idx_midia + 1) % len(self.midias)
            self.transicionar_midia()

    def _obter_dimensoes_alvo(self):
        if self.target_label_fundo is None: return 100, 100
        self.target_label_fundo.update_idletasks()
        w, h = self.target_label_fundo.winfo_width(), self.target_label_fundo.winfo_height()
        return (w, h) if w > 10 else (720, 630) 

    def atualizar_status(self, arquivo, progresso, stats):
        if self.lock_frame:
            if not self.bloqueio_progressbar.winfo_ismapped():
                self.bloqueio_progressbar.pack(fill="x", padx=30, pady=5, before=self.lbl_bloqueio_stats)
            self.lbl_bloqueio_arquivo.configure(text=f"Processando: {arquivo}")
            self.bloqueio_progressbar.set(progresso)
            # Agora exibe o texto completo contendo velocidade, MBs e o tempo restante (ETA)
            self.lbl_bloqueio_stats.configure(text=stats)

    def definir_mensagem_fixa(self, mensagem, esconder_barra=False):
        if self.lock_frame:
            self.lbl_bloqueio_arquivo.configure(text=mensagem)
            self.lbl_bloqueio_stats.configure(text="")
            if esconder_barra: self.bloqueio_progressbar.pack_forget()
            else: self.bloqueio_progressbar.set(1.0 if "concluído" in mensagem.lower() else 0)

    def sair_bloqueio_tecla(self, event): self.sair_bloqueio(None)
    def sair_bloqueio(self, event):
        if self.lock_frame:
            self.parar_apresentacao()
            self.lock_frame.destroy()
            self.lock_frame = None
            self.lbl_fundo = None
            self.target_label_fundo = None