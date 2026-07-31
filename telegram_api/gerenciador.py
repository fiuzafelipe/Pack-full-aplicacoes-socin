import customtkinter as ctk
import tkinter as tk
import tkinter.ttk as ttk
import asyncio
import traceback
from tkinter import messagebox
from utils import centralizar_janela, formatar_tamanho

class GerenciadorNuvem:
    def __init__(self, app):
        self.app = app
        self.popup_mgr = None
        self.drag_window = None
        self.drag_data = None
        self.drag_folder_window = None
        self.drag_folder_data = None
        self.botoes_pastas_widgets = {}
        self.botoes_arquivos_widgets = {}
        self.botoes_pastas_ui = []
        self.pasta_atual_mgr = None

    def _is_over_widget(self, x, y, widget):
        try:
            rx = widget.winfo_rootx()
            ry = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            return rx <= x <= rx + w and ry <= y <= ry + h
        except Exception:
            return False

    def solicitar_input(self, titulo, mensagem, callback):
        modal = ctk.CTkToplevel(self.app)
        modal.title(titulo)
        centralizar_janela(modal, 350, 180)
        modal.resizable(False, False)
        modal.transient(self.app)
        modal.grab_set()
        self.app._aplicar_icone(modal)

        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        ctk.CTkLabel(modal, text=mensagem, font=("Segoe UI", 13, "bold")).pack(pady=(15, 5))
        entrada = ctk.CTkEntry(modal, width=250)
        entrada.pack(pady=10)
        entrada.focus()

        def confirmar(event=None):
            valor = entrada.get()
            modal.destroy()
            callback(valor)

        btn_ok = ctk.CTkButton(modal, text="Confirmar", command=confirmar, fg_color=paleta["fg"], hover_color=paleta["hover"], corner_radius=8)
        btn_ok.pack(pady=5)
        modal.bind("<Return>", confirmar)

    def abrir(self):
        self.popup_mgr = ctk.CTkToplevel(self.app)
        self.popup_mgr.title("Gerenciamento da Nuvem")
        centralizar_janela(self.popup_mgr, 700, 520) 
        self.popup_mgr.resizable(False, False)
        self.popup_mgr.transient(self.app)
        self.popup_mgr.grab_set()
        self.app._aplicar_icone(self.popup_mgr)

        self.popup_mgr.bind("<Button-3>", self.app.bloqueio_manager.mostrar_menu_contexto)
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]

        frame_topo = ctk.CTkFrame(self.popup_mgr, fg_color="transparent")
        frame_topo.pack(fill="x", padx=20, pady=(15, 5))
        lbl_titulo = ctk.CTkLabel(frame_topo, text="Explorador da Nuvem", font=("Segoe UI Black", 16))
        lbl_titulo.pack(side="left")
        
        btn_nova_pasta = ctk.CTkButton(frame_topo, text="📁 Nova Pasta Raiz", width=120, fg_color=paleta["fg"], hover_color=paleta["hover"], corner_radius=8, command=lambda: self.solicitar_input("Nova Pasta", "Nome da Pasta (ex: Sistema):", self.acao_criar_pasta))
        btn_nova_pasta.pack(side="right")

        frame_corpo = ctk.CTkFrame(self.popup_mgr, fg_color="transparent")
        frame_corpo.pack(fill="both", expand=True, padx=20, pady=5)

        self.scroll_pastas = ctk.CTkScrollableFrame(frame_corpo, width=250, border_width=1, border_color=paleta["fg"], corner_radius=8)
        self.scroll_pastas.pack(side="left", fill="y", padx=(0, 5))
        
        self.scroll_arquivos = ctk.CTkScrollableFrame(frame_corpo, width=380, border_width=1, border_color=paleta["fg"], corner_radius=8)
        self.scroll_arquivos.pack(side="right", fill="both", expand=True)

        self.lbl_dica = ctk.CTkLabel(self.popup_mgr, text="💡 Dica: Arraste pastas para reordenar, ou arquivos para transferir. Botão direito p/ opções.", font=("Segoe UI", 11), text_color="gray")
        self.lbl_dica.pack(pady=5)
        
        modo = self.app.combo_modo.get() if hasattr(self.app, 'combo_modo') else self.app.saved_modo
        
        self.btn_armazenamento_mgr = ctk.CTkButton(self.popup_mgr, text=f"☁️ Nuvem em uso: {formatar_tamanho(self.app.uso_total_bytes)}", fg_color=paleta["light_bg"] if modo == "Light" else paleta["dark_bg"], border_width=1, corner_radius=8, command=self.app.mostrar_popup_armazenamento, height=30, border_color=paleta["fg"], text_color=paleta["fg"], hover_color=paleta["light_bg"] if modo == "Light" else paleta["dark_bg"])
        self.btn_armazenamento_mgr.pack(pady=(0, 10), fill="x", padx=20)

        self.atualizar_listas_gerenciador()

    def atualizar_listas_gerenciador(self):
        if not self.popup_mgr or not self.popup_mgr.winfo_exists(): return
        for widget in self.scroll_pastas.winfo_children(): widget.destroy()
        for widget in self.scroll_arquivos.winfo_children(): widget.destroy()
        
        self.botoes_pastas_ui = []
        self.botoes_pastas_widgets.clear()

        for pasta in self.app.pastas_locais:
            texto_exibicao = self.app.map_backend_to_ui.get(pasta, f"📁 {pasta}").replace('\u200b', '')
            btn = ctk.CTkButton(self.scroll_pastas, text=texto_exibicao, anchor="w", fg_color="transparent", text_color=("black", "white"), hover_color="#6c757d")
            btn.bind("<ButtonPress-1>", lambda e, p=pasta: self.iniciar_drag_pasta(e, p))
            btn.bind("<B1-Motion>", self.mover_drag_pasta)
            btn.bind("<ButtonRelease-1>", self.soltar_drag_pasta)
            btn.bind("<Button-3>", lambda e, p=pasta: self.abrir_menu_contexto(e, p))
            btn.pack(fill="x", pady=2)
            self.botoes_pastas_ui.append(btn)
            self.botoes_pastas_widgets[pasta] = btn

    def abrir_menu_contexto(self, event, pasta):
        menu = tk.Menu(self.popup_mgr, tearoff=0, font=("Segoe UI", 10))
        if "__" not in pasta:
            menu.add_command(label="📂 Criar Subpasta", command=lambda: self.solicitar_input("Subpasta", f"Criar subpasta em '{pasta.replace('#', '')}':", lambda nome: self.acao_criar_subpasta(pasta, nome)))
        
        nome_atual_limpo = pasta.split("__")[-1].replace("#", "")
        menu.add_command(label="✏️ Renomear", command=lambda: self.solicitar_input("Renomear", f"Novo nome para '{nome_atual_limpo}':", lambda novo_nome: self.acao_renomear_pasta(pasta, novo_nome)))
        menu.add_command(label="➡️ Mover / Transferir", command=lambda: self.abrir_modal_escolher_destino('pasta', pasta))
        menu.add_separator()
        menu.add_command(label="❌ Apagar Definitivamente (e arquivos)", command=lambda: self.acao_apagar_pasta(pasta))
        menu.post(event.x_root, event.y_root)

    def abrir_menu_contexto_arquivo(self, event, arq_obj):
        menu = tk.Menu(self.popup_mgr, tearoff=0, font=("Segoe UI", 10))
        menu.add_command(label="➡️ Mover / Transferir", command=lambda: self.abrir_modal_escolher_destino('arquivo', arq_obj))
        menu.add_separator()
        menu.add_command(label="❌ Apagar Arquivo", command=lambda: self.acao_apagar_arquivo_direto(arq_obj))
        menu.post(event.x_root, event.y_root)

    def abrir_modal_escolher_destino(self, tipo, origem_data):
        modal = ctk.CTkToplevel(self.popup_mgr)
        modal.title("Transferir")
        centralizar_janela(modal, 400, 220)
        modal.resizable(False, False)
        modal.transient(self.popup_mgr)
        modal.grab_set()
        self.app._aplicar_icone(modal)

        paleta = self.app.cores_destaque[self.app.combo_cor.get()]

        nome_origem = origem_data.split("__")[-1].replace("#", "") if tipo == 'pasta' else origem_data['nome']
        ctk.CTkLabel(modal, text=f"Selecione o destino para:\n'{nome_origem}'", font=("Segoe UI", 12, "bold"), justify="center").pack(pady=(15, 10))

        destinos_formatados = []
        map_destino = {}

        for p in self.app.pastas_locais:
            if tipo == 'pasta':
                if "__" not in p: 
                    ui_name = f"📁 {p.replace('#', '')}"
                    destinos_formatados.append(ui_name)
                    map_destino[ui_name] = p
            else:
                ui_name = self.app.map_backend_to_ui.get(p, p).replace('\u200b', '').strip()
                destinos_formatados.append(ui_name)
                map_destino[ui_name] = p

        combo_destino = ttk.Combobox(modal, values=destinos_formatados, state="readonly", width=45, font=("Segoe UI", 11))
        combo_destino.pack(pady=10, padx=20)
        if destinos_formatados:
            combo_destino.set(destinos_formatados[0])

        def on_confirmar():
            selecao = combo_destino.get()
            if not selecao: return
            destino_backend = map_destino[selecao]
            modal.destroy()

            if tipo == 'pasta':
                if origem_data == destino_backend:
                    messagebox.showwarning("Aviso", "A origem e o destino são iguais.", parent=self.popup_mgr)
                    return
                self.abrir_modal_acao_pasta(origem_data, destino_backend)
            else:
                if destino_backend == self.pasta_atual_mgr:
                    return
                if self.pasta_atual_mgr in self.app.ordem_arquivos and origem_data['nome'] in self.app.ordem_arquivos[self.pasta_atual_mgr]:
                    self.app.ordem_arquivos[self.pasta_atual_mgr].remove(origem_data['nome'])
                    self.app.salvar_configuracoes()
                asyncio.run_coroutine_threadsafe(self.processar_movimentacao(origem_data["msg"], destino_backend), self.app.async_loop)

        btn_conf = ctk.CTkButton(modal, text="Confirmar Transferência", command=on_confirmar, fg_color=paleta["fg"], hover_color=paleta["hover"], corner_radius=8, height=35)
        btn_conf.pack(pady=10)

    def selecionar_pasta_mgr(self, pasta, btn_clicado):
        self.pasta_atual_mgr = pasta
        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        for btn in self.botoes_pastas_ui: btn.configure(fg_color="transparent")
        btn_clicado.configure(fg_color=paleta["hover"])

        for widget in self.scroll_arquivos.winfo_children(): widget.destroy()
        self.botoes_arquivos_widgets.clear()

        arquivos = self.app.pastas_nuvem.get(pasta, [])
        if not arquivos:
            ctk.CTkLabel(self.scroll_arquivos, text="(Pasta Vazia)", text_color="gray").pack(pady=20)
            return

        for arq in arquivos:
            frame_linha = ctk.CTkFrame(self.scroll_arquivos, fg_color="transparent")
            frame_linha.pack(fill="x", pady=2)
            self.botoes_arquivos_widgets[arq["nome"]] = frame_linha
            
            lbl_arq = ctk.CTkLabel(frame_linha, text=f"📄 {arq['nome']}", anchor="w", cursor="hand2")
            lbl_arq.pack(side="left", fill="x", expand=True)
            btn_apagar = ctk.CTkButton(frame_linha, text="❌", width=30, fg_color="transparent", text_color="#dc3545", hover_color="#f8d7da", command=lambda a=arq: self.acao_apagar_arquivo_direto(a))
            btn_apagar.pack(side="right", padx=5)

            lbl_arq.bind("<ButtonPress-1>", lambda e, a=arq: self.iniciar_drag(e, a))
            lbl_arq.bind("<B1-Motion>", self.mover_drag)
            lbl_arq.bind("<ButtonRelease-1>", self.soltar_drag)
            lbl_arq.bind("<Button-3>", lambda e, a=arq: self.abrir_menu_contexto_arquivo(e, a))

    def abrir_modal_acao_pasta(self, origem, alvo):
        if not origem or not alvo: return
        modal = ctk.CTkToplevel(self.popup_mgr)
        modal.title("Ação de Pasta")
        centralizar_janela(modal, 350, 200)
        modal.resizable(False, False)
        modal.transient(self.popup_mgr)
        modal.grab_set()
        self.app._aplicar_icone(modal)

        paleta = self.app.cores_destaque[self.app.combo_cor.get()]
        nome_origem = origem.split("__")[-1].replace("#", "")
        nome_alvo = alvo.split("__")[-1].replace("#", "")
        
        ctk.CTkLabel(modal, text=f"O que deseja fazer com '{nome_origem}'?", font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))

        def on_reordenar():
            modal.destroy()
            idx_alvo = self.app.pastas_locais.index(alvo)
            self.app.pastas_locais.remove(origem)
            self.app.pastas_locais.insert(idx_alvo, origem)
            self.app.salvar_configuracoes()
            self.atualizar_listas_gerenciador()
            self.app.atualizar_dropdowns()
            self.selecionar_pasta_mgr(origem, self.botoes_pastas_widgets.get(origem))

        def on_mover():
            modal.destroy()
            base_nome = origem.split("__")[-1]
            raiz_alvo = alvo.split("__")[0]
            if not raiz_alvo.startswith("#"):
                raiz_alvo = f"#{raiz_alvo}"
            nova_pasta = f"{raiz_alvo}__{base_nome}"
            
            if nova_pasta == origem:
                return
            
            self.app.log(f"[SISTEMA] Solicitado mover '{origem}' para '{nova_pasta}'")
            asyncio.run_coroutine_threadsafe(
                self.processar_renomeacao_pasta(origem, nova_pasta), 
                self.app.async_loop
            )

        btn_reord = ctk.CTkButton(modal, text=f"Reordenar (Perto de {nome_alvo})", command=on_reordenar, fg_color=paleta["fg"], hover_color=paleta["hover"], corner_radius=8)
        btn_reord.pack(pady=5, fill="x", padx=20)

        if "__" not in alvo:
            btn_mov = ctk.CTkButton(modal, text=f"Mover para DENTRO de {nome_alvo}", command=on_mover, fg_color="#17a2b8", hover_color="#138496", corner_radius=8)
            btn_mov.pack(pady=5, fill="x", padx=20)
            
        btn_canc = ctk.CTkButton(modal, text="Cancelar", command=modal.destroy, fg_color="#6c757d", hover_color="#5a6268", corner_radius=8)
        btn_canc.pack(pady=5, fill="x", padx=20)

    def iniciar_drag_pasta(self, event, pasta):
        self.drag_folder_data = pasta
        self.drag_folder_window = tk.Toplevel(self.popup_mgr)
        self.drag_folder_window.overrideredirect(True)
        self.drag_folder_window.attributes('-alpha', 0.8)
        self.drag_folder_window.configure(bg="#28a745")
        texto = pasta.split('__')[-1].replace('#', '')
        lbl = tk.Label(self.drag_folder_window, text=f"📂 Movendo: {texto}", bg="#28a745", fg="white", font=("Segoe UI", 11, "bold"), padx=10, pady=5)
        lbl.pack()
        self.mover_drag_pasta(event)

    def mover_drag_pasta(self, event):
        if self.drag_folder_window:
            x, y = self.popup_mgr.winfo_pointerxy()
            self.drag_folder_window.geometry(f"+{x+15}+{y+15}")

    def soltar_drag_pasta(self, event):
        if not self.drag_folder_data:
            if self.drag_folder_window:
                self.drag_folder_window.destroy()
                self.drag_folder_window = None
            return

        if self.drag_folder_window:
            self.drag_folder_window.destroy()
            self.drag_folder_window = None
            
        x, y = self.popup_mgr.winfo_pointerxy()
        pasta_alvo = None
        
        for pasta, btn in self.botoes_pastas_widgets.items():
            if self._is_over_widget(x, y, btn):
                pasta_alvo = pasta
                break
        
        if pasta_alvo and pasta_alvo != self.drag_folder_data:
            self.abrir_modal_acao_pasta(self.drag_folder_data, pasta_alvo)
        else:
            if self.drag_folder_data in self.botoes_pastas_widgets:
                self.selecionar_pasta_mgr(self.drag_folder_data, self.botoes_pastas_widgets[self.drag_folder_data])
        self.drag_folder_data = None

    def iniciar_drag(self, event, arq_obj):
        self.drag_window = tk.Toplevel(self.popup_mgr)
        self.drag_window.overrideredirect(True)
        self.drag_window.attributes('-alpha', 0.8)
        self.drag_window.configure(bg="#007BFF")
        lbl = tk.Label(self.drag_window, text=f"📄 {arq_obj['nome']}", bg="#007BFF", fg="white", font=("Segoe UI", 11, "bold"), padx=10, pady=5)
        lbl.pack()
        self.drag_data = arq_obj
        self.mover_drag(event)

    def mover_drag(self, event):
        if self.drag_window:
            x, y = self.popup_mgr.winfo_pointerxy()
            self.drag_window.geometry(f"+{x+15}+{y+15}")

    def soltar_drag(self, event):
        if self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None
            
        x, y = self.popup_mgr.winfo_pointerxy()
        pasta_destino = None
        for pasta, btn in self.botoes_pastas_widgets.items():
            if self._is_over_widget(x, y, btn):
                pasta_destino = pasta
                break
        
        if pasta_destino and pasta_destino != self.pasta_atual_mgr and self.drag_data:
            if self.pasta_atual_mgr in self.app.ordem_arquivos and self.drag_data['nome'] in self.app.ordem_arquivos[self.pasta_atual_mgr]:
                self.app.ordem_arquivos[self.pasta_atual_mgr].remove(self.drag_data['nome'])
                self.app.salvar_configuracoes()
            asyncio.run_coroutine_threadsafe(self.processar_movimentacao(self.drag_data["msg"], pasta_destino), self.app.async_loop)
            self.drag_data = None
            return

        arquivo_alvo = None
        for nome_arq, widget in self.botoes_arquivos_widgets.items():
            if self._is_over_widget(x, y, widget):
                arquivo_alvo = nome_arq
                break
                
        if arquivo_alvo and self.drag_data and arquivo_alvo != self.drag_data['nome']:
            nome_arrastado = self.drag_data['nome']
            lista_ordem = self.app.ordem_arquivos.get(self.pasta_atual_mgr, [])
            for a in self.app.pastas_nuvem.get(self.pasta_atual_mgr, []):
                if a['nome'] not in lista_ordem: lista_ordem.append(a['nome'])
                    
            if nome_arrastado in lista_ordem and arquivo_alvo in lista_ordem:
                lista_ordem.remove(nome_arrastado)
                idx_alvo = lista_ordem.index(arquivo_alvo)
                lista_ordem.insert(idx_alvo, nome_arrastado)
                
                self.app.ordem_arquivos[self.pasta_atual_mgr] = lista_ordem
                self.app.salvar_configuracoes()
                
                def get_sort_key(arq_dict):
                    try: return lista_ordem.index(arq_dict["nome"])
                    except ValueError: return 999999
                self.app.pastas_nuvem[self.pasta_atual_mgr].sort(key=get_sort_key)
                if self.pasta_atual_mgr in self.botoes_pastas_widgets:
                    self.selecionar_pasta_mgr(self.pasta_atual_mgr, self.botoes_pastas_widgets[self.pasta_atual_mgr])

        self.drag_data = None

    async def processar_movimentacao(self, msg_obj, nova_pasta):
        try:
            # CORREÇÃO: Limpando a string FORA da f-string para não dar erro no Python 3.8
            nome_pasta_limpo = self.app.map_backend_to_ui.get(nova_pasta, nova_pasta).replace('    ↳ 📁 ', '').replace('📁 ', '').replace('\u200b', '')
            self.app.log(f"[SISTEMA] Movendo arquivo para '{nome_pasta_limpo}'...")
            
            novo_caption = f"{nova_pasta} \nEnviado via Fiuza Cloud"
            try:
                await self.app.client.edit_message('me', msg_obj.id, text=novo_caption)
            except Exception as ex:
                if "Content of the message was not modified" in str(ex):
                    pass
                else:
                    raise ex
            await self.app.fetch_cloud_files()
            if self.popup_mgr and self.popup_mgr.winfo_exists():
                self.popup_mgr.after(0, self.atualizar_listas_gerenciador)
            self.app.mudar_status("✅ Arquivo movido!", "#28a745", "#FFFFFF")
        except Exception as e:
            self.app.log(f"[ERRO] Falha ao mover: {str(e)}")
            self.app.mudar_status("❌ Erro ao mover arquivo", "#dc3545", "#FFFFFF")

    def acao_criar_pasta(self, nome):
        if not nome: return
        hashtag = nome if nome.startswith("#") else f"#{nome.replace(' ', '_')}"
        if hashtag not in self.app.pastas_locais:
            self.app.pastas_locais.append(hashtag)
            self.app.pastas_nuvem[hashtag] = []
            self.app.salvar_configuracoes()
            self.app.construir_mapa_pastas()
            self.atualizar_listas_gerenciador()
            self.app.atualizar_dropdowns()
        else:
            messagebox.showwarning("Aviso", "Esta pasta já existe.", parent=self.popup_mgr)

    def acao_criar_subpasta(self, pasta_pai, nome_subpasta):
        if not nome_subpasta: return
        nome_limpo = nome_subpasta.replace(' ', '_').replace('#', '')
        hashtag = f"{pasta_pai}__{nome_limpo}"
        
        if hashtag not in self.app.pastas_locais:
            idx_pai = self.app.pastas_locais.index(pasta_pai)
            self.app.pastas_locais.insert(idx_pai + 1, hashtag)
            self.app.pastas_nuvem[hashtag] = []
            self.app.salvar_configuracoes()
            self.app.construir_mapa_pastas()
            self.atualizar_listas_gerenciador()
            self.app.atualizar_dropdowns()

    def acao_renomear_pasta(self, pasta_antiga, novo_nome):
        if not novo_nome: return
        prefixo = ""
        if "__" in pasta_antiga: prefixo = pasta_antiga.split("__")[0] + "__"
            
        novo_limpo = novo_nome.replace(' ', '_').replace('#', '')
        pasta_nova = f"{prefixo}{novo_limpo}"
        if not pasta_nova.startswith("#"): pasta_nova = f"#{pasta_nova}"
        
        if pasta_nova == pasta_antiga:
            return
            
        asyncio.run_coroutine_threadsafe(
            self.processar_renomeacao_pasta(pasta_antiga, pasta_nova), 
            self.app.async_loop
        )

    async def processar_renomeacao_pasta(self, pasta_antiga, pasta_nova):
        try:
            cor_tema = self.app.cores_destaque.get(self.app.saved_cor, {"fg": "#28a745"})["fg"]
            self.app.mudar_status("🔄 Atualizando nuvem...", cor_tema, "#FFFFFF")
            self.app.log(f"[SISTEMA] Movendo/Renomeando pasta de '{pasta_antiga}' para '{pasta_nova}'...")
            
            arquivos_para_atualizar = []
            
            chave_antiga = pasta_antiga
            if chave_antiga not in self.app.pastas_nuvem and f"#{chave_antiga}" in self.app.pastas_nuvem:
                chave_antiga = f"#{chave_antiga}"
            
            if chave_antiga in self.app.pastas_nuvem:
                for arq in self.app.pastas_nuvem[chave_antiga]:
                    if 'msg' in arq and hasattr(arq['msg'], 'id'):
                        arquivos_para_atualizar.append((arq['msg'].id, pasta_nova))
            
            prefixo_antigo = pasta_antiga + "__"
            prefixo_novo = pasta_nova + "__"
            
            subpastas_afetadas = []
            for p in list(self.app.pastas_locais):
                if p.startswith(prefixo_antigo) or p.startswith(pasta_antiga + "__"):
                    p_nova = p.replace(prefixo_antigo, prefixo_novo, 1).replace(pasta_antiga + "__", prefixo_novo, 1)
                    subpastas_afetadas.append((p, p_nova))
                    if p in self.app.pastas_nuvem:
                        for arq in self.app.pastas_nuvem[p]:
                            if 'msg' in arq and hasattr(arq['msg'], 'id'):
                                arquivos_para_atualizar.append((arq['msg'].id, p_nova))

            for msg_id, nova_tag in arquivos_para_atualizar:
                novo_caption = f"{nova_tag} \nEnviado via Fiuza Cloud"
                try:
                    await self.app.client.edit_message('me', msg_id, text=novo_caption)
                except Exception as ex:
                    if "Content of the message was not modified" in str(ex):
                        pass
                    else:
                        self.app.log(f"[AVISO] Erro ao editar mensagem {msg_id}: {str(ex)}")

            for p_ant, p_nov in subpastas_afetadas:
                if p_ant in self.app.pastas_locais:
                    idx_s = self.app.pastas_locais.index(p_ant)
                    self.app.pastas_locais[idx_s] = p_nov
                if p_ant in self.app.ordem_arquivos:
                    self.app.ordem_arquivos[p_nov] = self.app.ordem_arquivos.pop(p_ant)
                if p_ant in self.app.pastas_nuvem:
                    self.app.pastas_nuvem[p_nov] = self.app.pastas_nuvem.pop(p_ant)

            for p_old in [pasta_antiga, chave_antiga, f"#{pasta_antiga}"]:
                while p_old in self.app.pastas_locais:
                    self.app.pastas_locais.remove(p_old)

            raiz_nova = pasta_nova.split("__")[0]
            if not raiz_nova.startswith("#"):
                raiz_nova = f"#{raiz_nova}"

            if raiz_nova in self.app.pastas_locais:
                idx_raiz = self.app.pastas_locais.index(raiz_nova)
                insert_idx = idx_raiz + 1
                while insert_idx < len(self.app.pastas_locais) and self.app.pastas_locais[insert_idx].startswith(raiz_nova + "__"):
                    insert_idx += 1
                self.app.pastas_locais.insert(insert_idx, pasta_nova)
            else:
                self.app.pastas_locais.append(pasta_nova)

            if pasta_antiga in self.app.ordem_arquivos:
                self.app.ordem_arquivos[pasta_nova] = self.app.ordem_arquivos.pop(pasta_antiga)
            elif chave_antiga in self.app.ordem_arquivos:
                self.app.ordem_arquivos[pasta_nova] = self.app.ordem_arquivos.pop(chave_antiga)
            
            if pasta_antiga in self.app.pastas_nuvem:
                self.app.pastas_nuvem[pasta_nova] = self.app.pastas_nuvem.pop(pasta_antiga)
            elif chave_antiga in self.app.pastas_nuvem:
                self.app.pastas_nuvem[pasta_nova] = self.app.pastas_nuvem.pop(chave_antiga)
                
            self.app.salvar_configuracoes()
            self.app.construir_mapa_pastas()
            
            if self.popup_mgr and self.popup_mgr.winfo_exists():
                self.popup_mgr.after(0, self.atualizar_listas_gerenciador)
            self.app.after(0, self.app.atualizar_dropdowns)
            
            self.app.mudar_status("✅ Pasta movida com sucesso!", "#28a745", "#FFFFFF")
            self.app.log(f"[SISTEMA] Operação concluída para: {pasta_nova}")
        except Exception as e:
            err_msg = traceback.format_exc()
            self.app.log(f"[ERRO CRÍTICO] Falha ao mover pasta: {str(e)}")
            self.app.mudar_status("❌ Erro ao mover pasta", "#dc3545", "#FFFFFF")

    def acao_apagar_pasta(self, pasta):
        # CORREÇÃO: Limpando a string FORA da f-string para não dar erro no Python 3.8
        nome_pasta_limpo = self.app.map_backend_to_ui.get(pasta, pasta).replace('    ↳ 📁 ', '').replace('📁 ', '').replace('\u200b', '')
        
        if messagebox.askyesno("Excluir Pasta", f"CUIDADO: Deseja apagar a pasta '{nome_pasta_limpo}' e TODOS os arquivos da Nuvem?", parent=self.popup_mgr):
            asyncio.run_coroutine_threadsafe(self.processar_delecao_pasta(pasta), self.app.async_loop)

    async def processar_delecao_pasta(self, pasta):
        try:
            arquivos = self.app.pastas_nuvem.get(pasta, [])
            ids_para_apagar = [arq['msg'].id for arq in arquivos]
            if ids_para_apagar:
                await self.app.client.delete_messages('me', ids_para_apagar)
                
            if pasta in self.app.pastas_locais:
                self.app.pastas_locais.remove(pasta)
            if pasta in self.app.ordem_arquivos: 
                del self.app.ordem_arquivos[pasta]
                
            self.app.salvar_configuracoes()
            self.app.construir_mapa_pastas()
            await self.app.fetch_cloud_files()
            if self.popup_mgr and self.popup_mgr.winfo_exists():
                self.popup_mgr.after(0, self.atualizar_listas_gerenciador)
            self.app.mudar_status("✅ Pasta excluída!", "#28a745", "#FFFFFF")
        except Exception as e:
            self.app.log(f"[ERRO] Falha ao apagar pasta: {str(e)}")
            self.app.mudar_status("❌ Erro ao apagar pasta", "#dc3545", "#FFFFFF")

    def acao_apagar_arquivo_direto(self, arq_obj):
        if messagebox.askyesno("Excluir", f"Deseja apagar '{arq_obj['nome']}' permanentemente da nuvem?", parent=self.popup_mgr):
            asyncio.run_coroutine_threadsafe(self.processar_delecao_arquivo(arq_obj['msg']), self.app.async_loop)

    async def processar_delecao_arquivo(self, msg_obj):
        try:
            await self.app.client.delete_messages('me', [msg_obj.id])
            await self.app.fetch_cloud_files()
            if self.popup_mgr and self.popup_mgr.winfo_exists():
                self.popup_mgr.after(0, self.atualizar_listas_gerenciador)
            self.app.mudar_status("✅ Arquivo excluído!", "#28a745", "#FFFFFF")
        except Exception as e:
            self.app.log(f"[ERRO] Falha ao apagar: {str(e)}")
            self.app.mudar_status("❌ Erro ao apagar arquivo", "#dc3545", "#FFFFFF")