import threading
import os
import customtkinter as ctk

from core.downloader import baixar_arquivos
from core.zip_manager import criar_zip
from core.parser import get_versions, get_paths
from core.file_builder import gerar_arquivos

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Pack Full - Aplicação Socin")
        
        # ==========================================
        # 1. CENTRALIZAR A TELA PRINCIPAL
        # ==========================================
        app_width = 700
        app_height = 620 # Aumentado um pouco para caber todos os elementos perfeitamente
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (app_width // 2)
        y = (screen_height // 2) - (app_height // 2)
        
        self.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.resizable(False, False)
        
        # Flag global que controla o cancelamento
        self.flag_cancelar = False

        self.versoes = get_versions()

        self.criar_widgets()

    def criar_widgets(self):

        titulo = ctk.CTkLabel(
            self,
            text="PACK FULL SOCIN",
            font=("Segoe UI", 28, "bold")
        )
        titulo.pack(pady=25)

        frame = ctk.CTkFrame(self)
        frame.pack(padx=20, pady=10, fill="both", expand=True)

        lbl_versao = ctk.CTkLabel(frame, text="Versão")
        lbl_versao.pack(pady=(20, 5))

        self.combo_versao = ctk.CTkComboBox(
            frame,
            values=self.versoes,
            command=self.carregar_paths,
            width=300
        )
        self.combo_versao.pack()

        lbl_path = ctk.CTkLabel(frame, text="Path")
        lbl_path.pack(pady=(20, 5))

        self.combo_path = ctk.CTkComboBox(
            frame,
            values=["Selecione"],
            width=300
        )
        self.combo_path.pack()

        # ELEMENTOS DE PROGRESSO (Iniciam Ocultos)
        self.lbl_arquivo = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12))
        
        self.progressbar = ctk.CTkProgressBar(
            frame, width=300, mode="determinate", progress_color="#28a745"
        )
        self.progressbar.set(0)
        
        self.lbl_porcentagem = ctk.CTkLabel(frame, text="0%", font=("Segoe UI", 14, "bold"))

        # BOTÃO CANCELAR (Vermelho, Inicia Oculto)
        self.btn_cancelar = ctk.CTkButton(
            frame, text="CANCELAR", width=250, height=45,
            fg_color="#dc3545", hover_color="#c82333",
            command=self.acionar_cancelamento
        )

        # BOTÃO GERAR PACK
        self.btn_gerar = ctk.CTkButton(
            frame, text="GERAR PACK", width=250, height=45,
            command=self.abrir_modal_opcoes
        )
        self.btn_gerar.pack(pady=25)

        # LOGS
        self.logs = ctk.CTkTextbox(frame, width=600, height=150)
        self.logs.pack(pady=10)

        self.log("Sistema iniciado.")
        self.log("Versões carregadas.")

    def carregar_paths(self, versao):
        paths = get_paths(versao)
        self.combo_path.configure(values=paths)
        if paths:
            self.combo_path.set(paths[0])
        self.log(f"Paths carregados para versão {versao}")

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
    # LÓGICA DE CANCELAMENTO
    # ==========================================
    def acionar_cancelamento(self):
        """Disparado quando o botão vermelho é clicado."""
        self.flag_cancelar = True
        self.btn_cancelar.configure(state="disabled", text="CANCELANDO...")
        self.log("Solicitação de cancelamento enviada...")

    def checar_cancelamento(self):
        """Retorna o status atual para o downloader ler."""
        return self.flag_cancelar

    # ==========================================
    # JANELA MODAL
    # ==========================================
    def abrir_modal_opcoes(self):
        versao = self.combo_versao.get()
        path = self.combo_path.get()

        if not versao or path == "Selecione":
            self.log("Aviso: Selecione uma versão e um path válidos antes de gerar.")
            return

        lista_arquivos = gerar_arquivos(versao, path)
        nomes_arquivos = [item["arquivo"] for item in lista_arquivos]

        self.modal = ctk.CTkToplevel(self)
        self.modal.title("Opções de Download")
        
        modal_width = 450
        modal_height = 300

        self.update_idletasks()
        app_x = self.winfo_rootx()
        app_y = self.winfo_rooty()
        app_width = self.winfo_width()
        app_height = self.winfo_height()

        x = app_x + (app_width // 2) - (modal_width // 2)
        y = app_y + (app_height // 2) - (modal_height // 2)

        self.modal.geometry(f"{modal_width}x{modal_height}+{x}+{y}")
        self.modal.resizable(False, False)
        
        self.modal.transient(self)
        self.modal.grab_set()

        lbl_titulo = ctk.CTkLabel(self.modal, text="Escolha o pacote abaixo:", font=("Segoe UI", 18, "bold"))
        lbl_titulo.pack(pady=(20, 15))

        self.modo_var = ctk.StringVar(value="completo")

        rb_completo = ctk.CTkRadioButton(
            self.modal, text="Pacote Completo (Baixar Todos e Compactar)", 
            variable=self.modo_var, value="completo", command=self.atualizar_estado_combo
        )
        rb_completo.pack(pady=10, padx=20, anchor="w")

        rb_individual = ctk.CTkRadioButton(
            self.modal, text="Pacote Individual (Baixar apenas um arquivo)", 
            variable=self.modo_var, value="individual", command=self.atualizar_estado_combo
        )
        rb_individual.pack(pady=10, padx=20, anchor="w")

        self.combo_arquivos_modal = ctk.CTkComboBox(
            self.modal, values=nomes_arquivos, width=350, state="disabled"
        )
        self.combo_arquivos_modal.pack(pady=10)

        btn_confirmar = ctk.CTkButton(
            self.modal, text="CONFIRMAR", command=self.confirmar_selecao
        )
        btn_confirmar.pack(pady=15)

    def atualizar_estado_combo(self):
        if self.modo_var.get() == "individual":
            self.combo_arquivos_modal.configure(state="normal")
        else:
            self.combo_arquivos_modal.configure(state="disabled")

    def confirmar_selecao(self):
        modo = self.modo_var.get()
        arquivo_selecionado = self.combo_arquivos_modal.get() if modo == "individual" else None
        self.modal.destroy()
        
        thread = threading.Thread(target=self.gerar_pack, args=(modo, arquivo_selecionado))
        thread.start()

    # ==========================================
    # GERENCIAMENTO DA THREAD DE DOWNLOAD
    # ==========================================
    def gerar_pack(self, modo, arquivo_selecionado):
        try:
            self.flag_cancelar = False
            self.after(0, lambda: self.btn_cancelar.configure(state="normal", text="CANCELAR"))

            versao = self.combo_versao.get()
            path = self.combo_path.get()

            # ==========================================================
            # CORREÇÃO: "before=self.logs" trava os elementos ACIMA dos logs!
            # ==========================================================
            self.after(0, lambda: self.btn_gerar.pack_forget()) 
            self.after(0, lambda: self.lbl_arquivo.pack(pady=(5, 5), before=self.logs))
            self.after(0, lambda: self.progressbar.pack(pady=(0, 5), before=self.logs))
            self.after(0, lambda: self.lbl_porcentagem.pack(pady=(0, 10), before=self.logs))
            self.after(0, lambda: self.btn_cancelar.pack(pady=(0, 15), before=self.logs))

            self.log("================================")
            self.log(f"Versão: {versao} | Path: {path}")
            if modo == "completo":
                self.log("Modo: PACOTE COMPLETO")
            else:
                self.log(f"Modo: INDIVIDUAL -> {arquivo_selecionado}")
            self.log("Iniciando downloads...")

            baixar_arquivos(
                versao, path, 
                log_callback=self.log, 
                progress_callback=self.atualizar_progresso,
                cancel_callback=self.checar_cancelamento,
                apenas_arquivo=arquivo_selecionado
            )

            if self.flag_cancelar:
                self.log("================================")
                self.log("PROCESSO ABORTADO!")
                return

            pasta_temp = f"temp/{versao}_{path}"

            if modo == "completo":
                nome_zip = f"output/PACK_FULL_{versao.replace('.', '_')}_{path}.zip"
                os.makedirs("output", exist_ok=True)
                self.log("Compactando arquivos...")
                
                criar_zip(pasta_temp, nome_zip, log_callback=self.log)

                self.log("================================")
                self.log("PACK GERADO COM SUCESSO!")
                self.log(f"Salvo em: {nome_zip}")
            
            else:
                self.log("================================")
                self.log("ARQUIVO INDIVIDUAL BAIXADO!")
                self.log(f"Salvo na pasta: {pasta_temp}")

        except Exception as e:
            self.log("ERRO CRÍTICO:")
            self.log(str(e))
            
        finally:
            # Ao restaurar, o botão GERAR também volta para o lugar correto acima dos logs
            self.after(0, lambda: self.btn_cancelar.pack_forget())
            self.after(0, lambda: self.lbl_arquivo.pack_forget())
            self.after(0, lambda: self.progressbar.pack_forget())
            self.after(0, lambda: self.lbl_porcentagem.pack_forget())
            self.after(0, lambda: self.btn_gerar.pack(pady=25, before=self.logs))