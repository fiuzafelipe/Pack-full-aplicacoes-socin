import threading
import os
import customtkinter as ctk

from core.downloader import baixar_arquivos
from core.zip_manager import criar_zip
from core.parser import get_versions, get_paths

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Pack Full - Aplicação Socin")
        self.geometry("700x550")
        self.resizable(False, False)

        self.versoes = get_versions()

        self.criar_widgets()

    def criar_widgets(self):

        titulo = ctk.CTkLabel(
            self,
            text="PACK FULL SOCIN",
            font=("Segoe UI", 28, "bold")
        )
        titulo.pack(pady=25)

        # FRAME PRINCIPAL
        frame = ctk.CTkFrame(self)
        frame.pack(padx=20, pady=10, fill="both", expand=True)

        # LABEL VERSÃO
        lbl_versao = ctk.CTkLabel(frame, text="Versão")
        lbl_versao.pack(pady=(20, 5))

        # COMBO VERSÃO
        self.combo_versao = ctk.CTkComboBox(
            frame,
            values=self.versoes,
            command=self.carregar_paths,
            width=300
        )
        self.combo_versao.pack()

        # LABEL PATH
        lbl_path = ctk.CTkLabel(frame, text="Path")
        lbl_path.pack(pady=(20, 5))

        # COMBO PATH
        self.combo_path = ctk.CTkComboBox(
            frame,
            values=["Selecione"],
            width=300
        )
        self.combo_path.pack()

        # LABEL DO NOME DO ARQUIVO (Inicia oculta)
        self.lbl_arquivo = ctk.CTkLabel(
            frame, 
            text="", 
            font=("Segoe UI", 12)
        )

        # BARRA DE PROGRESSO VERDE (Inicia oculta)
        self.progressbar = ctk.CTkProgressBar(
            frame, 
            width=300, 
            mode="determinate", 
            progress_color="#28a745"
        )
        self.progressbar.set(0)

        # LABEL DA PORCENTAGEM E MBs (Inicia oculta)
        self.lbl_porcentagem = ctk.CTkLabel(
            frame, 
            text="0%", 
            font=("Segoe UI", 14, "bold")
        )

        # BOTÃO
        self.btn_gerar = ctk.CTkButton(
            frame,
            text="GERAR PACK",
            width=250,
            height=45,
            command=self.iniciar_geracao
        )
        self.btn_gerar.pack(pady=25)

        # LOGS
        self.logs = ctk.CTkTextbox(
            frame,
            width=600,
            height=150
        )
        self.logs.pack(pady=10)

        self.log("Sistema iniciado.")
        self.log("Versões carregadas.")

    def carregar_paths(self, versao):
        paths = get_paths(versao)
        self.combo_path.configure(values=paths)

        if paths:
            self.combo_path.set(paths[0])

        self.log(f"Paths carregados para versão {versao}")

    # ==========================================
    # SISTEMA DE LOGS E PROGRESSO THREAD-SAFE
    # ==========================================
    def log(self, mensagem):
        self.after(0, lambda: self._inserir_log(mensagem))

    def _inserir_log(self, mensagem):
        self.logs.insert("end", f"{mensagem}\n")
        self.logs.see("end")

    def atualizar_progresso(self, valor_float, texto_stats, nome_arquivo):
        """Atualiza a barra, a porcentagem (MBs) e o nome do arquivo com segurança na thread principal."""
        self.after(0, lambda: self.progressbar.set(valor_float))
        self.after(0, lambda: self.lbl_porcentagem.configure(text=texto_stats))
        self.after(0, lambda: self.lbl_arquivo.configure(text=f"Baixando: {nome_arquivo}"))
    
    # ==========================================
    # GERENCIAMENTO DA THREAD DE DOWNLOAD
    # ==========================================
    def iniciar_geracao(self):
        thread = threading.Thread(target=self.gerar_pack)
        thread.start()

    def gerar_pack(self):
        try:
            versao = self.combo_versao.get()
            path = self.combo_path.get()

            if not versao or path == "Selecione":
                self.log("Aviso: Selecione uma versão e um path válidos antes de gerar.")
                return

            # Altera a UI para o "Modo Carregamento"
            self.after(0, lambda: self.btn_gerar.configure(state="disabled", text="BAIXANDO..."))
            self.after(0, lambda: self.btn_gerar.pack_forget()) 
            
            # Mostra os 3 elementos de progresso na tela na ordem correta
            self.after(0, lambda: self.lbl_arquivo.pack(pady=(15, 5)))
            self.after(0, lambda: self.progressbar.pack(pady=(0, 5)))
            self.after(0, lambda: self.lbl_porcentagem.pack(pady=(0, 10)))

            self.log("================================")
            self.log(f"Versão selecionada: {versao}")
            self.log(f"Path selecionado: {path}")
            self.log("Iniciando downloads...")

            # Aciona o download passando as funções de retorno para atualizar a tela
            baixar_arquivos(
                versao, 
                path, 
                log_callback=self.log, 
                progress_callback=self.atualizar_progresso
            )

            pasta_temp = f"temp/{versao}_{path}"
            nome_zip = f"output/PACK_FULL_{versao.replace('.', '_')}_{path}.zip"

            os.makedirs("output", exist_ok=True)

            self.log("Compactando arquivos...")
            
            # Aciona a compactação também enviando log para a tela
            criar_zip(
                pasta_temp, 
                nome_zip,
                log_callback=self.log
            )

            self.log("================================")
            self.log("PACK GERADO COM SUCESSO!")
            self.log(f"Salvo em: {nome_zip}")

        except Exception as e:
            self.log("ERRO CRÍTICO:")
            self.log(str(e))
            
        finally:
            # Independentemente de dar certo ou erro, oculta as barras e restaura o botão
            self.after(0, lambda: self.lbl_arquivo.pack_forget())
            self.after(0, lambda: self.progressbar.pack_forget())
            self.after(0, lambda: self.lbl_porcentagem.pack_forget())
            self.after(0, lambda: self.btn_gerar.pack(pady=25))
            self.after(0, lambda: self.btn_gerar.configure(state="normal", text="GERAR PACK"))