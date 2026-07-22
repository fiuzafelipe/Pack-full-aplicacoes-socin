import threading
import os
import customtkinter as ctk
from PIL import Image

from core.downloader import baixar_arquivos
from core.zip_manager import criar_zip
from core.parser import get_versions, get_paths
from core.file_builder import gerar_arquivos
from core.theme import carregar_tema, salvar_tema

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Pack Full - Aplicação Socin")
        
        # Centralização Dinâmica e Tela Compactada
        app_width = 720
        app_height = 650 
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (app_width // 2)
        y = (screen_height // 2) - (app_height // 2)
        self.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.resizable(False, False)
        
        self.flag_cancelar = False
        self.versoes = get_versions()

        # Dicionário de cores dinâmicas
        self.cores_destaque = {
            "Azul": {"fg": "#1f538d", "hover": "#14375e", "progress": "#1f538d"},
            "Verde": {"fg": "#28a745", "hover": "#218838", "progress": "#28a745"},
            "Vermelho": {"fg": "#dc3545", "hover": "#c82333", "progress": "#dc3545"},
            "Roxo": {"fg": "#6f42c1", "hover": "#59339d", "progress": "#6f42c1"}
        }

        self.criar_widgets()
        self.aplicar_tema_inicial()

    def criar_widgets(self):
        
        # ==========================================
        # EFEITOS DE LOGO
        # ==========================================
        img_path = "assets/logo.png"
        self.img_normal = ctk.CTkImage(light_image=Image.open(img_path), size=(130, 60))
        self.img_zoom = ctk.CTkImage(light_image=Image.open(img_path), size=(150, 70))
        
        self.lbl_logo = ctk.CTkLabel(self, image=self.img_normal, text="")
        self.lbl_logo.pack(pady=(15, 0))
        
        self.lbl_logo.bind("<Enter>", lambda e: self.lbl_logo.configure(image=self.img_zoom))
        self.lbl_logo.bind("<Leave>", lambda e: self.lbl_logo.configure(image=self.img_normal))
        self.lbl_logo.bind("<Button-1>", self.mostrar_assinatura)

        titulo = ctk.CTkLabel(self, text="PACK FULL SOCIN", font=("Segoe UI", 26, "bold"))
        titulo.pack(pady=(5, 10))

        # ==========================================
        # FRAME DE TEMAS (EXTERNO E NO TOPO)
        # ==========================================
        frame_temas = ctk.CTkFrame(self, fg_color="transparent")
        frame_temas.pack(pady=(0, 10), fill="x", padx=30)
        
        lbl_modo = ctk.CTkLabel(frame_temas, text="Modo Visual:", font=("Segoe UI", 12))
        lbl_modo.pack(side="left", padx=(0, 10))
        self.combo_modo = ctk.CTkComboBox(frame_temas, values=["Dark", "Light"], width=120, command=self.mudar_tema)
        self.combo_modo.pack(side="left")

        self.combo_cor = ctk.CTkComboBox(frame_temas, values=list(self.cores_destaque.keys()), width=120, command=self.mudar_tema)
        self.combo_cor.pack(side="right")
        lbl_cor = ctk.CTkLabel(frame_temas, text="Cor de Destaque:", font=("Segoe UI", 12))
        lbl_cor.pack(side="right", padx=(0, 10))

        # ==========================================
        # FRAME PRINCIPAL (NÚCLEO DO SISTEMA)
        # ==========================================
        frame = ctk.CTkFrame(self)
        frame.pack(padx=20, pady=5, fill="both", expand=True)

        lbl_versao = ctk.CTkLabel(frame, text="Versão")
        lbl_versao.pack(pady=(15, 5))
        self.combo_versao = ctk.CTkComboBox(frame, values=self.versoes, command=self.carregar_paths, width=300)
        self.combo_versao.pack()

        lbl_path = ctk.CTkLabel(frame, text="Path")
        lbl_path.pack(pady=(15, 5))
        self.combo_path = ctk.CTkComboBox(frame, values=["Selecione"], width=300)
        self.combo_path.pack()

        # PROGRESSO
        self.lbl_arquivo = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12))
        self.progressbar = ctk.CTkProgressBar(frame, width=300, mode="determinate")
        self.progressbar.set(0)
        self.lbl_porcentagem = ctk.CTkLabel(frame, text="0%", font=("Segoe UI", 14, "bold"))

        # BOTOES
        self.btn_cancelar = ctk.CTkButton(
            frame, text="CANCELAR", width=250, height=45,
            fg_color="#dc3545", hover_color="#c82333",
            command=self.acionar_cancelamento
        )

        self.btn_gerar = ctk.CTkButton(
            frame, text="GERAR PACK", width=250, height=45,
            command=self.abrir_modal_opcoes
        )
        self.btn_gerar.pack(pady=20)

        # LOGS
        self.logs = ctk.CTkTextbox(frame, width=640, height=140)
        self.logs.pack(pady=10)

        self.log("Sistema iniciado.")
        self.log("Pronto para uso.")

    # ==========================================
    # ASSINATURA, TEMAS E POPUPS ELEGANTES
    # ==========================================
    def exibir_popup(self, titulo, mensagem):
        """Cria um popup elegante, centralizado e tematizado na tela."""
        popup = ctk.CTkToplevel(self)
        popup.title(titulo)
        
        largura, altura = 380, 180
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

        # Botão com a cor de destaque atual
        cor_atual = self.combo_cor.get()
        paleta = self.cores_destaque.get(cor_atual, self.cores_destaque["Azul"])
        
        btn_ok = ctk.CTkButton(
            popup, text="OK", width=120, height=35,
            command=popup.destroy,
            fg_color=paleta["fg"], hover_color=paleta["hover"]
        )
        btn_ok.pack()

    def mostrar_assinatura(self, event):
        self.exibir_popup(
            "Fiuza Tecnology", 
            "Aplicação desenvolvida por Felipe Fiuza\n\nFiuza Tecnology - Development & Software Solutions"
        )

    def aplicar_tema_inicial(self):
        modo_salvo, cor_salva = carregar_tema()
        self.combo_modo.set(modo_salvo)
        self.combo_cor.set(cor_salva)
        self.mudar_tema(None)

    def mudar_tema(self, _):
        modo = self.combo_modo.get()
        cor = self.combo_cor.get()
        
        ctk.set_appearance_mode(modo)
        paleta = self.cores_destaque[cor]
        
        self.btn_gerar.configure(fg_color=paleta["fg"], hover_color=paleta["hover"])
        self.progressbar.configure(progress_color=paleta["progress"])
        
        # Aplica o destaque nas bordas e menus suspensos das caixas de seleção
        elementos_borda = [self.combo_versao, self.combo_path, self.combo_modo, self.combo_cor]
        for el in elementos_borda:
            el.configure(
                border_color=paleta["fg"], 
                button_color=paleta["fg"],
                button_hover_color=paleta["hover"],
                dropdown_hover_color=paleta["hover"]
            )
            
        # Adiciona a borda fina e colorida na caixa de logs
        self.logs.configure(border_color=paleta["fg"], border_width=2)
        
        salvar_tema(modo, cor)

    # ==========================================
    # LOGS E PROGRESSO
    # ==========================================
    def carregar_paths(self, versao):
        paths = get_paths(versao)
        self.combo_path.configure(values=paths)
        if paths:
            self.combo_path.set(paths[0])
        self.log(f"Paths carregados para {versao}")

    def log(self, mensagem):
        self.after(0, lambda: self._inserir_log(mensagem))

    def _inserir_log(self, mensagem):
        self.logs.insert("end", f"{mensagem}\n")
        self.logs.see("end")

    def atualizar_progresso(self, valor_float, texto_stats, nome_arquivo):
        self.after(0, lambda: self.progressbar.set(valor_float))
        self.after(0, lambda: self.lbl_porcentagem.configure(text=texto_stats))
        self.after(0, lambda: self.lbl_arquivo.configure(text=f"Baixando: {nome_arquivo}"))

    # ==========================================
    # CANCELAMENTO
    # ==========================================
    def acionar_cancelamento(self):
        self.flag_cancelar = True
        self.btn_cancelar.configure(state="disabled", text="CANCELANDO...")
        self.log("Cancelamento solicitado. Interrompendo arquivo atual...")

    def checar_cancelamento(self):
        return self.flag_cancelar

    # ==========================================
    # JANELA MODAL DE OPÇÕES
    # ==========================================
    def abrir_modal_opcoes(self):
        versao = self.combo_versao.get()
        path = self.combo_path.get()

        if not versao or path == "Selecione":
            self.log("Aviso: Selecione uma versão válida.")
            return

        lista_arquivos = gerar_arquivos(versao, path)
        nomes_arquivos = [item["arquivo"] for item in lista_arquivos]

        self.modal = ctk.CTkToplevel(self)
        self.modal.title("Opções")
        
        modal_width = 450
        modal_height = 300
        self.update_idletasks()
        
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (modal_width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (modal_height // 2)

        self.modal.geometry(f"{modal_width}x{modal_height}+{x}+{y}")
        self.modal.resizable(False, False)
        self.modal.transient(self)
        self.modal.grab_set()

        lbl_titulo = ctk.CTkLabel(self.modal, text="Escolha o pacote abaixo:", font=("Segoe UI", 18, "bold"))
        lbl_titulo.pack(pady=(20, 15))

        self.modo_var = ctk.StringVar(value="completo")
        paleta = self.cores_destaque[self.combo_cor.get()]

        rb_completo = ctk.CTkRadioButton(
            self.modal, text="Pacote Completo (Baixar Todos e Compactar)", 
            variable=self.modo_var, value="completo", command=self.atualizar_estado_combo,
            fg_color=paleta["fg"]
        )
        rb_completo.pack(pady=10, padx=20, anchor="w")

        rb_individual = ctk.CTkRadioButton(
            self.modal, text="Pacote Individual (Baixar apenas um arquivo)", 
            variable=self.modo_var, value="individual", command=self.atualizar_estado_combo,
            fg_color=paleta["fg"]
        )
        rb_individual.pack(pady=10, padx=20, anchor="w")

        self.combo_arquivos_modal = ctk.CTkComboBox(
            self.modal, values=nomes_arquivos, width=350, state="disabled",
            border_color=paleta["fg"], button_color=paleta["fg"], 
            button_hover_color=paleta["hover"], dropdown_hover_color=paleta["hover"]
        )
        self.combo_arquivos_modal.pack(pady=10)

        btn_confirmar = ctk.CTkButton(
            self.modal, text="CONFIRMAR", command=self.confirmar_selecao,
            fg_color=paleta["fg"], hover_color=paleta["hover"]
        )
        btn_confirmar.pack(pady=15)

    def atualizar_estado_combo(self):
        if self.modo_var.get() == "individual":
            self.combo_arquivos_modal.configure(state="normal")
        else:
            self.combo_arquivos_modal.configure(state="disabled")

    def confirmar_selecao(self):
        modo = self.modo_var.get()
        arq = self.combo_arquivos_modal.get() if modo == "individual" else None
        self.modal.destroy()
        
        threading.Thread(target=self.gerar_pack, args=(modo, arq)).start()

    # ==========================================
    # DOWNLOAD E CONTROLE DE TELA
    # ==========================================
    def gerar_pack(self, modo, arquivo_selecionado):
        try:
            self.flag_cancelar = False
            self.after(0, lambda: self.btn_cancelar.configure(state="normal", text="CANCELAR"))

            versao = self.combo_versao.get()
            path = self.combo_path.get()

            self.after(0, lambda: self.btn_gerar.pack_forget()) 
            self.after(0, lambda: self.lbl_arquivo.pack(pady=(5, 5), before=self.logs))
            self.after(0, lambda: self.progressbar.pack(pady=(0, 5), before=self.logs))
            self.after(0, lambda: self.lbl_porcentagem.pack(pady=(0, 10), before=self.logs))
            self.after(0, lambda: self.btn_cancelar.pack(pady=(0, 15), before=self.logs))

            self.log("================================")
            self.log(f"Modo: {'COMPLETO' if modo == 'completo' else f'INDIVIDUAL -> {arquivo_selecionado}'}")

            baixar_arquivos(
                versao, path, 
                log_callback=self.log, 
                progress_callback=self.atualizar_progresso,
                cancel_callback=self.checar_cancelamento,
                apenas_arquivo=arquivo_selecionado
            )

            if self.flag_cancelar:
                self.log("================================")
                self.log("PROCESSO ABORTADO. Arquivos já baixados foram preservados.")
                return

            pasta_temp = f"temp/{versao}_{path}"

            if modo == "completo":
                nome_zip = f"output/PACK_FULL_{versao.replace('.', '_')}_{path}.zip"
                os.makedirs("output", exist_ok=True)
                self.log("Compactando arquivos...")
                criar_zip(pasta_temp, nome_zip, log_callback=self.log)
                self.log(f"PACK SALVO EM: {nome_zip}")
            else:
                self.log(f"ARQUIVO SALVO NA PASTA: {pasta_temp}")

            # Dispara o popup de sucesso caso não tenha havido erro ou cancelamento
            self.after(0, lambda: self.exibir_popup("Concluído", "Download concluído com sucesso! 🚀"))

        except Exception as e:
            self.log(f"ERRO CRÍTICO: {str(e)}")
            
        finally:
            self.after(0, lambda: self.btn_cancelar.pack_forget())
            self.after(0, lambda: self.lbl_arquivo.pack_forget())
            self.after(0, lambda: self.progressbar.pack_forget())
            self.after(0, lambda: self.lbl_porcentagem.pack_forget())
            self.after(0, lambda: self.btn_gerar.pack(pady=20, before=self.logs))