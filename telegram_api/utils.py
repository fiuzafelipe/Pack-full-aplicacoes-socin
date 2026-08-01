import os
import sys
import customtkinter as ctk

# ==========================================
# PATCH DE CORREÇÃO DO CUSTOMTKINTER (SCROLL)
# ==========================================
try:
    original_check = ctk.windows.widgets.ctk_scrollable_frame.CTkScrollableFrame.check_if_master_is_canvas
    def patched_check(self, widget):
        if isinstance(widget, str) or not hasattr(widget, "master"): return False
        return original_check(self, widget)
    ctk.windows.widgets.ctk_scrollable_frame.CTkScrollableFrame.check_if_master_is_canvas = patched_check
except AttributeError:
    pass

def obter_caminho(caminho_relativo):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, caminho_relativo)

def centralizar_janela(janela, largura, altura, offset_y=0):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2) - offset_y
    janela.geometry(f"{largura}x{altura}+{x}+{y}")

def is_inside_widget(x, y, widget):
    bx, by = widget.winfo_rootx(), widget.winfo_rooty()
    bw, bh = widget.winfo_width(), widget.winfo_height()
    return bx <= x <= bx + bw and by <= y <= by + bh

def formatar_tamanho(tamanho_em_bytes):
    if tamanho_em_bytes < 1024:
        return f"{tamanho_em_bytes} B"
    elif tamanho_em_bytes < 1024 ** 2:
        return f"{tamanho_em_bytes / 1024:.2f} KB"
    elif tamanho_em_bytes < 1024 ** 3:
        return f"{tamanho_em_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{tamanho_em_bytes / (1024 ** 3):.2f} GB"