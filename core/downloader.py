import os
from core.auth import get_authenticated_session
from core.file_builder import gerar_arquivos
from core.parser import mudar_diretorio

BASE_URL = "http://aplicacoes.socin.com.br"

def baixar_arquivos(versao, path, log_callback=print, progress_callback=None, cancel_callback=None, apenas_arquivo=None, modo=None, incluir_restaurante=False, bits=None):
    session = get_authenticated_session()
    
    if not session:
        log_callback("Erro: Falha na autenticação. Download cancelado.")
        return False

    arquivos = gerar_arquivos(versao, path, incluir_restaurante, bits)
    
    # Filtros baseados no modo selecionado
    if modo == "atualizadores":
        arquivos = [a for a in arquivos if a["arquivo"].startswith("CONC_V_RLS") or a["arquivo"].startswith("PDV_V_RLS") or a["arquivo"].startswith("V_RLS")]
    elif apenas_arquivo:
        arquivos = [a for a in arquivos if a["arquivo"] == apenas_arquivo]
    elif modo == "completo" and not incluir_restaurante:
        # Se for pacote completo e o usuário disse NÃO para o restaurante, remove ele da fila de download
        arquivos = [a for a in arquivos if "installRES" not in a["arquivo"]]

    # Ajuste de caminho dinâmico para as pastas especiais
    if versao in ["instaladores", "sistema_operacional"]:
        pasta_temp = f"temp/{versao}"
        diretorio_base = f"/aplicativos/{versao}"
    else:
        pasta_temp = f"temp/{versao}_{path}"
        diretorio_base = f"/aplicativos/{versao}/{path}"
        
    os.makedirs(pasta_temp, exist_ok=True)

    for item in arquivos:
        if cancel_callback and cancel_callback():
            log_callback("Operação abortada pelo usuário.")
            return False

        subpasta = item["pasta"]
        arquivo = item["arquivo"]

        diretorio_alvo = diretorio_base
        if subpasta:
            diretorio_alvo += f"/{subpasta}"
            
        log_callback(f"Acessando: {diretorio_alvo}...")
        mudar_diretorio(session, diretorio_alvo)

        download_url = f"{BASE_URL}/?download&filename={arquivo}"
        log_callback(f"Baixando: {arquivo}...")

        if progress_callback:
            progress_callback(0.0, "0% - Verificando...", arquivo)

        try:
            response = session.get(download_url, stream=True, timeout=30)
            
            if response.status_code == 200:
                tamanho_total = int(response.headers.get('content-length', 0))
                total_mb = tamanho_total / (1024 * 1024)
                tamanho_baixado = 0
                
                caminho_arquivo = os.path.join(pasta_temp, arquivo)
                download_concluido = True 
                
                with open(caminho_arquivo, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if cancel_callback and cancel_callback():
                            download_concluido = False
                            break
                            
                        if chunk:
                            f.write(chunk)
                            tamanho_baixado += len(chunk)
                            
                            if tamanho_total > 0 and progress_callback:
                                baixado_mb = tamanho_baixado / (1024 * 1024)
                                percentual_float = tamanho_baixado / tamanho_total
                                texto_stats = f"{int(percentual_float * 100)}% - {baixado_mb:.1f} MB de {total_mb:.1f} MB"
                                progress_callback(percentual_float, texto_stats, arquivo)
                
                if not download_concluido:
                    if os.path.exists(caminho_arquivo):
                        os.remove(caminho_arquivo)
                    log_callback(f"Download de {arquivo} cancelado.")
                    return False
                
                log_callback("Sucesso!")
            else:
                log_callback(f"Aviso: {arquivo} não existe no servidor (Status {response.status_code})")
                
        except Exception as e:
            log_callback(f"Falha de conexão com {arquivo}: {e}")

    log_callback("Todos os downloads solicitados foram finalizados!")
    return True