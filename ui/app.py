import threading
import os
import sys
import customtkinter as ctk
from PIL import Image, ImageEnhance

from core.downloader import baixar_arquivos
from core.zip_manager import criar_zip
from core.parser import get_versions, get_paths
from core.file_builder import gerar_arquivos
from core.theme import carregar_tema, salvar_tema
from core.updater import checar_atualizacao

# ==========================================
# FUNÇÃO PARA LOCALIZAR ARQUIVOS NO PYINSTALLER
# ==========================================
def obter_caminho(caminho_relativo):
    """ Retorna o caminho absoluto para o recurso, compatível com PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, caminho_relativo)

class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        
        self.VERSAO_PROGRAMA = "v1.0.0"
        self.title(f"Fiuza Technology - Pack Full Aplicação Socin ({self.VERSAO_PROGRAMA})")
        
        # Ícone da janela principal
        self._aplicar_icone(self)
        
        app_width = 720
        app_height = 610 
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (app_width // 2)
        y = (screen_height // 2) - (app_height // 2)
        self.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.resizable(False, False)
        
        self.flag_cancelar = False
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

        if self.auto_update:
            threading.Thread(target=lambda: checar_atualizacao(self.log)).start()

    # ==========================================
    # CORREÇÃO DEFINITIVA DO ÍCONE
    # ==========================================
    def _aplicar_icone(self, janela):
        """Aplica um delay de 250ms para garantir que o Windows não resete o ícone"""
        try:
            caminho_ico = obter_caminho("assets/icon.ico")
            if os.path.exists(caminho_ico):
                # O "after" aguarda o Windows terminar de desenhar a janela antes de injetar o .ico
                janela.after(250, lambda: janela.iconbitmap(caminho_ico))
        except Exception:
            pass

    def criar_widgets(self):
        self.btn_config = ctk.CTkButton(
            self, text="⚙️", width=35, height=35, font=("Segoe UI", 18), 
            fg_color="transparent", command=self.abrir_configuracoes
        )
        self.btn_config.place(x=670, y=10)

        img_path = obter_caminho("assets/logo.png")
        img_original = Image.open(img_path)
        img_brilhante = ImageEnhance.Brightness(img_original).enhance(1.6)

        self.img_normal = ctk.CTkImage(light_image=img_original, size=(130, 60))
        self.img_glow = ctk.CTkImage(light_image=img_brilhante, size=(130, 60))
        
        self.lbl_logo = ctk.CTkLabel(self, image=self.img_normal, text="")
        self.lbl_logo.pack(pady=(15, 0))
        
        self.lbl_logo.bind("<Enter>", lambda e: self.lbl_logo.configure(image=self.img_glow))
        self.lbl_logo.bind("<Leave>", lambda e: self.lbl_logo.configure(image=self.img_normal))
        self.lbl_logo.bind("<Button-1>", self.mostrar_assinatura)

        titulo = ctk.CTkLabel(self, text="PACK FULL SOCIN", font=("Segoe UI", 24, "bold"))
        titulo.pack(pady=(2, 5))

        frame_temas = ctk.CTkFrame(self, fg_color="transparent")
        frame_temas.pack(pady=(0, 5), fill="x", padx=30)
        
        lbl_modo = ctk.CTkLabel(frame_temas, text="Modo Visual:", font=("Segoe UI", 12))
        lbl_modo.pack(side="left", padx=(0, 10))
        self.combo_modo = ctk.CTkComboBox(frame_temas, values=["Dark", "Light"], width=120, command=self.mudar_tema)
        self.combo_modo.pack(side="left")

        self.combo_cor = ctk.CTkComboBox(frame_temas, values=list(self.cores_destaque.keys()), width=120, command=self.mudar_tema)
        self.combo_cor.pack(side="right")
        lbl_cor = ctk.CTkLabel(frame_temas, text="Cor de Destaque:", font=("Segoe UI", 12))
        lbl_cor.pack(side="right", padx=(0, 10))

        frame = ctk.CTkFrame(self)
        frame.pack(padx=20, pady=5, fill="both", expand=True)

        lbl_versao = ctk.CTkLabel(frame, text="Versão")
        lbl_versao.pack(pady=(8, 2))
        self.combo_versao = ctk.CTkComboBox(frame, values=self.versoes, command=self.carregar_paths, width=300)
        self.combo_versao.pack()

        lbl_path = ctk.CTkLabel(frame, text="Path")
        lbl_path.pack(pady=(8, 2))
        self.combo_path = ctk.CTkComboBox(frame, values=["Selecione"], width=300)
        self.combo_path.pack()

        self.lbl_arquivo = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12))
        self.progressbar = ctk.CTkProgressBar(frame, width=300, mode="determinate")
        self.progressbar.set(0)
        self.lbl_porcentagem = ctk.CTkLabel(frame, text="0%", font=("Segoe UI", 14, "bold"))

        self.btn_cancelar = ctk.CTkButton(
            frame, text="CANCELAR", width=250, height=40, command=self.acionar_cancelamento
        )

        self.btn_gerar = ctk.CTkButton(
            frame, text="GERAR PACK", width=250, height=40, command=self.abrir_modal_opcoes
        )
        self.btn_gerar.pack(pady=15)

        self.logs = ctk.CTkTextbox(frame, width=640, height=115)
        self.logs.pack(pady=5)
        
        self.lbl_status = ctk.CTkButton(
            frame, text="⏳ Pronto para iniciar", width=640, height=30, 
            state="disabled", fg_color="#333333", text_color="#FFFFFF"
        )
        self.lbl_status.pack(pady=(5, 5))

        self.log("Sistema iniciado.")

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
        popup.grab_set()
        popup.focus_force()

        lbl_msg = ctk.CTkLabel(popup, text=mensagem, font=("Segoe UI", 14), justify="center")
        lbl_msg.pack(pady=(35, 25), padx=20)

        paleta = self.cores_destaque[self.combo_cor.get()]
        frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
        frame_btns.pack()

        if pasta_destino:
            def abrir_pasta():
                caminho_absoluto = os.path.abspath(pasta_destino)
                if os.path.exists(caminho_absoluto):
                    os.startfile(caminho_absoluto)
                popup.destroy()

            btn_abrir = ctk.CTkButton(
                frame_btns, text="Abrir Pasta", width=130, height=35, command=abrir_pasta,
                fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"]
            )
            btn_abrir.pack(side="left", padx=10)
            
            btn_ok = ctk.CTkButton(
                frame_btns, text="OK", width=100, height=35, command=popup.destroy,
                fg_color="#6c757d", hover_color="#5a6268", text_color="#FFFFFF"
            )
            btn_ok.pack(side="right", padx=10)
        else:
            btn_ok = ctk.CTkButton(
                frame_btns, text="OK", width=120, height=35, command=popup.destroy,
                fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"]
            )
            btn_ok.pack()
        
        popup.bind("<Return>", lambda e: popup.destroy())
        btn_ok.focus() 

        # Chama a função do ícone APÓS todas as configurações do popup
        self._aplicar_icone(popup)

    def mostrar_assinatura(self, event):
        self.exibir_popup(
            "Fiuza Tecnology", 
            "Aplicação desenvolvida por Felipe Fiuza\n\nFiuza Tecnology - Development & Software Solutions"
        )

    def aplicar_tema_inicial(self):
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
        
        for btn in [self.btn_gerar, self.btn_cancelar]:
            btn.configure(fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            
        self.progressbar.configure(progress_color=paleta["fg"])
        
        cor_engrenagem = "#222222" if modo == "Light" else "#EEEEEE"
        self.btn_config.configure(text_color=cor_engrenagem, hover_color=paleta["hover"])
        
        for el in [self.combo_versao, self.combo_path, self.combo_modo, self.combo_cor]:
            el.configure(
                border_color=paleta["fg"], button_color=paleta["fg"],
                button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"]
            )
            
        self.logs.configure(border_color=paleta["fg"], border_width=2)
        
        bg_status = "#E0E0E0" if modo == "Light" else "#333333"
        fg_status = "#000000" if modo == "Light" else "#FFFFFF"
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
            self.log(f"Paths carregados para {versao}")

    def log(self, mensagem):
        self.after(0, lambda: self._inserir_log(mensagem))

    def _inserir_log(self, mensagem):
        # 1. Libera a caixa temporariamente para o sistema poder escrever
        self.logs.configure(state="normal")
        
        # 2. Verifica a posição da barra ANTES de inserir o texto. 
        # Margem de 0.90 (90%) é bem mais fluida e não trava a rolagem.
        posicao = self.logs.yview()
        ta_no_fundo = True if not posicao else (posicao[1] >= 0.90)
        
        # 3. Insere a nova mensagem na última linha
        self.logs.insert("end", f"{mensagem}\n")
        
        # 4. Bloqueia a caixa (modo leitura) para evitar que o clique do usuário trave a tela
        self.logs.configure(state="disabled")
        
        # 5. Se o usuário estava olhando o final do texto, desce a tela automaticamente
        if ta_no_fundo:
            self.logs.see("end")

    def atualizar_progresso(self, valor_float, texto_stats, nome_arquivo):
        self.after(0, lambda: self.progressbar.set(valor_float))
        self.after(0, lambda: self.lbl_porcentagem.configure(text=texto_stats))
        self.after(0, lambda: self.lbl_arquivo.configure(text=f"Baixando: {nome_arquivo}"))

    def acionar_cancelamento(self):
        self.flag_cancelar = True
        self.btn_cancelar.configure(state="disabled", text="CANCELANDO...")
        self.mudar_status("⚠️ Cancelamento solicitado. Interrompendo...", "#ffc107", "#000000")

    def checar_cancelamento(self):
        return self.flag_cancelar
        
    def abrir_configuracoes(self):
        modal_cfg = ctk.CTkToplevel(self)
        modal_cfg.title("Configurações do Sistema")
        
        largura, altura = 400, 320
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (largura // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altura // 2)
        modal_cfg.geometry(f"{largura}x{altura}+{x}+{y}")
        modal_cfg.resizable(False, False)
        modal_cfg.transient(self)
        modal_cfg.grab_set()

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
        switch_update = ctk.CTkSwitch(
            modal_cfg, text="Atualizar automaticamente (GitHub)", 
            variable=self.switch_var, command=self.salvar_config_modal, progress_color=paleta["fg"]
        )
        switch_update.pack(pady=10)

        btn_fechar_cfg = ctk.CTkButton(
            modal_cfg, text="FECHAR", width=120, height=32, command=modal_cfg.destroy,
            fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"]
        )
        btn_fechar_cfg.pack(pady=(15, 15))

        # Chama a função do ícone APÓS todas as configurações do popup
        self._aplicar_icone(modal_cfg)

    def salvar_config_modal(self):
        self.auto_update = self.switch_var.get()
        salvar_tema(self.combo_modo.get(), self.combo_cor.get(), self.auto_update)
        self.log(f"Status do Auto-Update alterado para: {self.auto_update}")

    def abrir_modal_opcoes(self):
        versao = self.combo_versao.get()
        path = self.combo_path.get()

        if not versao or versao == "Selecione":
            self.log("Aviso: Selecione uma versão válida.")
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
        self.modal.grab_set()

        lbl_titulo = ctk.CTkLabel(self.modal, text="Escolha o pacote abaixo:", font=("Segoe UI", 18, "bold"))
        lbl_titulo.pack(pady=(15, 10))

        self.modo_var = ctk.StringVar(value="completo")
        paleta = self.cores_destaque[self.combo_cor.get()]

        if versao == "sistema_operacional":
            self.modo_var.set("individual") 
            lbl_info = ctk.CTkLabel(self.modal, text="Para sistemas operacionais, baixe um arquivo por vez.", font=("Segoe UI", 13))
            lbl_info.pack(pady=(10, 15))
            
            self.combo_arquivos_modal = ctk.CTkComboBox(
                self.modal, values=nomes_arquivos, width=380, state="normal",
                border_color=paleta["fg"], button_color=paleta["fg"], 
                button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"]
            )
            self.combo_arquivos_modal.pack(pady=10)
            
            self.btn_confirmar = ctk.CTkButton(
                self.modal, text="CONFIRMAR", 
                command=lambda: self.iniciar_fluxo("individual", self.combo_arquivos_modal.get()), 
                fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"]
            )
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
            rb_completo = ctk.CTkRadioButton(self.modal, text="Pacote Completo (Baixar Todos e Compactar)", variable=self.modo_var, value="completo", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_completo.pack(pady=5, padx=20, anchor="w")

            rb_atualizadores = ctk.CTkRadioButton(self.modal, text="Pacote Atualizadores (Baixa só os atualizadores)", variable=self.modo_var, value="atualizadores", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_atualizadores.pack(pady=5, padx=20, anchor="w")

            rb_individual = ctk.CTkRadioButton(self.modal, text="Pacote Individual (Baixar apenas um arquivo)", variable=self.modo_var, value="individual", command=self.atualizar_estado_combo, fg_color=paleta["fg"])
            rb_individual.pack(pady=5, padx=20, anchor="w")

            self.combo_arquivos_modal = ctk.CTkComboBox(self.modal, values=nomes_arquivos, width=380, state="disabled", border_color=paleta["fg"], button_color=paleta["fg"], button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"])
            self.combo_arquivos_modal.pack(pady=10)

            self.btn_confirmar = ctk.CTkButton(self.modal, text="CONFIRMAR", command=self.verificar_restaurante, fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
            self.btn_confirmar.pack(pady=15)

        # Chama a função do ícone APÓS todas as configurações do popup
        self._aplicar_icone(self.modal)

    def atualizar_estado_combo(self):
        if not hasattr(self, 'combo_arquivos_modal') or not self.combo_arquivos_modal.winfo_exists():
            return
            
        modo = self.modo_var.get()
        versao = self.combo_versao.get()
        
        if modo == "individual":
            self.combo_arquivos_modal.configure(state="normal")
            if versao == "instaladores":
                if hasattr(self, 'frame_botoes') and self.frame_botoes.winfo_ismapped():
                    self.frame_botoes.pack_forget()
                if hasattr(self, 'btn_confirmar') and not self.btn_confirmar.winfo_ismapped():
                    self.btn_confirmar.pack(pady=15)
        else:
            self.combo_arquivos_modal.configure(state="disabled")
            if versao == "instaladores":
                if hasattr(self, 'btn_confirmar'):
                    self.btn_confirmar.pack_forget()
                if hasattr(self, 'frame_botoes'):
                    self.frame_botoes.pack(pady=15)

    def verificar_restaurante(self):
        modo = self.modo_var.get()
        arq = self.combo_arquivos_modal.get() if modo == "individual" else None
        self.modal.destroy()
        
        if modo == "completo":
            self.perguntar_restaurante(modo, arq)
        else:
            self.iniciar_fluxo(modo, arq)

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
        popup.grab_set()

        lbl_msg = ctk.CTkLabel(popup, text="Incluir módulo Restaurante (RES)?", font=("Segoe UI", 16, "bold"))
        lbl_msg.pack(pady=(25, 20))
        
        frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
        frame_btns.pack(pady=5)
        paleta = self.cores_destaque[self.combo_cor.get()]
        
        def on_sim():
            popup.destroy()
            self.iniciar_fluxo(modo, arq, incluir_restaurante=True)
            
        def on_nao():
            popup.destroy()
            self.iniciar_fluxo(modo, arq, incluir_restaurante=False)
            
        btn_sim = ctk.CTkButton(frame_btns, text="Sim", command=on_sim, width=100, fg_color=paleta["fg"], hover_color=paleta["hover"], text_color=paleta["text"])
        btn_sim.pack(side="left", padx=15)
        
        btn_nao = ctk.CTkButton(frame_btns, text="Não", command=on_nao, width=100, fg_color="#dc3545", hover_color="#c82333", text_color="#FFFFFF")
        btn_nao.pack(side="right", padx=15)
        
        # Chama a função do ícone APÓS todas as configurações do popup
        self._aplicar_icone(popup)

    def iniciar_fluxo(self, modo, arq, incluir_restaurante=False, bits=None):
        if hasattr(self, 'modal') and self.modal.winfo_exists():
            self.modal.destroy()
        threading.Thread(target=self.gerar_pack, args=(modo, arq, incluir_restaurante, bits)).start()

    def gerar_pack(self, modo, arquivo_selecionado, incluir_restaurante, bits):
        try:
            self.flag_cancelar = False
            self.after(0, lambda: self.btn_cancelar.configure(state="normal", text="CANCELAR"))
            
            self.mudar_status("⬇️ Baixando pacotes...", "#007BFF", "#FFFFFF")

            versao = self.combo_versao.get()
            path = self.combo_path.get()

            self.after(0, lambda: self.btn_gerar.pack_forget()) 
            self.after(0, lambda: self.lbl_arquivo.pack(pady=(5, 5), before=self.logs))
            self.after(0, lambda: self.progressbar.pack(pady=(0, 5), before=self.logs))
            self.after(0, lambda: self.lbl_porcentagem.pack(pady=(0, 10), before=self.logs))
            self.after(0, lambda: self.btn_cancelar.pack(pady=(0, 15), before=self.logs))

            self.log("================================")
            self.log(f"Modo: {modo.upper()}")
            
            baixar_arquivos(
                versao, path, 
                log_callback=self.log, 
                progress_callback=self.atualizar_progresso,
                cancel_callback=self.checar_cancelamento,
                apenas_arquivo=arquivo_selecionado,
                modo=modo,
                incluir_restaurante=incluir_restaurante,
                bits=bits
            )

            if self.flag_cancelar:
                self.mudar_status("❌ Download cancelado!", "#dc3545", "#FFFFFF")
                self.log("================================")
                self.log("PROCESSO ABORTADO. Arquivos concluídos foram preservados.")
                return

            if versao in ["instaladores", "sistema_operacional"]:
                pasta_temp = f"temp/{versao}"
            else:
                pasta_temp = f"temp/{versao}_{path}"

            pasta_alvo = pasta_temp 

            if versao not in ["instaladores", "sistema_operacional"]:
                if modo == "completo":
                    nome_zip = f"output/PACK_FULL_{versao.replace('.', '_')}_{path}.zip"
                    os.makedirs("output", exist_ok=True)
                    self.log("Compactando arquivos...")
                    self.mudar_status("📦 Compactando arquivos...", "#FF8C00", "#FFFFFF")
                    criar_zip(pasta_temp, nome_zip, log_callback=self.log)
                    self.log(f"PACK SALVO EM: {nome_zip}")
                    pasta_alvo = "output"
                
                elif modo == "atualizadores":
                    nome_zip = f"output/PACK_ATUALIZADORES_{versao.replace('.', '_')}_{path}.zip"
                    os.makedirs("output", exist_ok=True)
                    self.log("Compactando atualizadores...")
                    self.mudar_status("📦 Compactando atualizadores...", "#FF8C00", "#FFFFFF")
                    criar_zip(pasta_temp, nome_zip, log_callback=self.log)
                    self.log(f"PACK SALVO EM: {nome_zip}")
                    pasta_alvo = "output"
                
                else:
                    self.log(f"ARQUIVO SALVO NA PASTA: {pasta_temp}")
            else:
                self.log(f"ARQUIVOS SALVOS NA PASTA: {pasta_temp}")

            self.mudar_status("🚀 Download concluído com sucesso!", "#28a745", "#FFFFFF")
            self.after(0, lambda: self.exibir_popup("Concluído", "Download concluído com sucesso! 🚀", pasta_alvo))

        except Exception as e:
            self.mudar_status("❌ Erro Crítico no processo", "#dc3545", "#FFFFFF")
            self.log(f"ERRO CRÍTICO: {str(e)}")
            
        finally:
            self.after(0, lambda: self.btn_cancelar.pack_forget())
            self.after(0, lambda: self.lbl_arquivo.pack_forget())
            self.after(0, lambda: self.progressbar.pack_forget())
            self.after(0, lambda: self.lbl_porcentagem.pack_forget())
            self.after(0, lambda: self.btn_gerar.pack(pady=15, before=self.logs))