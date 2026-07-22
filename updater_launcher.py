import sys
import time
import os
import requests
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

def iniciar_atualizacao(root, label, progress, zip_url):
    base_dir = os.path.dirname(sys.executable)
    zip_path = os.path.join(base_dir, "update.zip")
    exe_path = os.path.join(base_dir, "Pack_econect.exe")

    try:
        label.config(text="Aguardando aplicativo fechar...")
        root.update()
        time.sleep(2) # Espera 2s para o app principal não bloquear os arquivos

        label.config(text="Baixando atualização do GitHub...")
        root.update()
        
        # Faz o download e move a barra de progresso
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()
        total_length = response.headers.get('content-length')
        
        with open(zip_path, "wb") as f:
            if total_length is None: 
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(100 * dl / total_length)
                    progress['value'] = done
                    root.update()

        label.config(text="Instalando atualização...")
        progress['value'] = 0
        progress['mode'] = 'indeterminate'
        progress.start(10)
        root.update()

        # Extrai os novos arquivos sobre os antigos
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(base_dir)

        label.config(text="Finalizando...")
        root.update()
        time.sleep(1)
        
        # Apaga o zip para não ocupar espaço
        if os.path.exists(zip_path):
            os.remove(zip_path)

        # Abre o programa principal de novo
        subprocess.Popen([exe_path])
        root.destroy()
        sys.exit(0)

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível concluir:\n{str(e)}")
        root.destroy()
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        messagebox.showerror("Aviso", "O atualizador não deve ser aberto manualmente.")
        sys.exit(1)
        
    zip_url = sys.argv[1]

    root = tk.Tk()
    root.title("Fiuza Technology - Atualizador")
    root.geometry("350x120")
    root.resizable(False, False)
    
    # Centraliza na tela
    largura = root.winfo_screenwidth()
    altura = root.winfo_screenheight()
    x = (largura // 2) - (350 // 2)
    y = (altura // 2) - (120 // 2)
    root.geometry(f"350x120+{x}+{y}")

    label = tk.Label(root, text="Iniciando...", font=("Segoe UI", 10))
    label.pack(pady=(20, 10))

    progress = ttk.Progressbar(root, orient="horizontal", length=280, mode="determinate")
    progress.pack()

    # Inicia a atualização meio segundo após abrir a janelinha
    root.after(500, lambda: iniciar_atualizacao(root, label, progress, zip_url))
    root.mainloop()

if __name__ == "__main__":
    main()