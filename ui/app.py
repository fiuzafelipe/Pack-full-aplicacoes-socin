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
        self.geometry("700x500")
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
        lbl_versao = ctk.CTkLabel(
            frame,
            text="Versão"
        )
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
        lbl_path = ctk.CTkLabel(
            frame,
            text="Path"
        )
        lbl_path.pack(pady=(20, 5))

        # COMBO PATH
        self.combo_path = ctk.CTkComboBox(
            frame,
            values=["Selecione"],
            width=300
        )

        self.combo_path.pack()

        # BOTÃO
        self.btn_gerar = ctk.CTkButton(
            frame,
            text="GERAR PACK",
            width=250,
            height=45,
            command=self.iniciar_geracao
        )

        self.btn_gerar.pack(pady=35)

        # LOGS
        self.logs = ctk.CTkTextbox(
            frame,
            width=600,
            height=180
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

    def log(self, mensagem):

        self.logs.insert("end", f"{mensagem}\n")
        self.logs.see("end")
    
    def iniciar_geracao(self):

        thread = threading.Thread(
            target=self.gerar_pack
        )

        thread.start()

    def gerar_pack(self):

        try:

            versao = self.combo_versao.get()
            path = self.combo_path.get()

            self.log("================================")
            self.log(f"Versão selecionada: {versao}")
            self.log(f"Path selecionado: {path}")
            self.log("Iniciando downloads...")

            baixar_arquivos(versao, path)

            pasta_temp = f"temp/{versao}_{path}"

            nome_zip = (
                f"output/"
                f"PACK_FULL_"
                f"{versao.replace('.', '_')}_{path}.zip"
            )

            os.makedirs("output", exist_ok=True)

            self.log("Compactando arquivos...")

            criar_zip(
                pasta_temp,
                nome_zip
            )

            self.log("================================")
            self.log("PACK GERADO COM SUCESSO!")
            self.log(nome_zip)

        except Exception as e:

            self.log("ERRO:")
            self.log(str(e))

app = App()
app.mainloop()