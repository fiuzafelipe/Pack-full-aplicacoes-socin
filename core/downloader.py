import os
import shutil
from core.auth import get_authenticated_session
from core.file_builder import gerar_arquivos
from core.parser import mudar_diretorio

BASE_URL = "http://aplicacoes.socin.com.br"

def baixar_arquivos(versao, path, log_callback=print, progress_callback=None, cancel_callback=None, apenas_arquivo=None):
    session = get_authenticated_session()
    
    if not session:
        log_callback("Erro: Falha na autenticação. Download cancelado.")
        return False

    arquivos = gerar_arquivos(versao, path)
    
    if apenas_arquivo:
        arquivos = [item for item in arquivos if item["arquivo"] == apenas_arquivo]

    pasta_temp = f"temp/{versao}_{path}"
    
    if not apenas_arquivo and os.path.exists(pasta_temp):
        shutil.rmtree(pasta_temp)
    os.makedirs(pasta_temp, exist_ok=True)

    for item in arquivos:
        # Verifica se o usuário cancelou antes mesmo de iniciar o próximo arquivo
        if cancel_callback and cancel_callback():
            log_callback("Operação abortada pelo usuário.")
            return False

        subpasta = item["pasta"]
        arquivo = item["arquivo"]

        diretorio_alvo = f"/aplicativos/{versao}/{path}"
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
                download_concluido = True # Flag interna para controle de integridade
                
                with open(caminho_arquivo, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        
                        # CHECAGEM DE CANCELAMENTO EM TEMPO REAL
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
                
                # Se o loop parou por causa do botão cancelar...
                if not download_concluido:
                    if os.path.exists(caminho_arquivo):
                        os.remove(caminho_arquivo) # Deleta o pedaço incompleto do disco
                    log_callback(f"Download de {arquivo} interrompido e excluído.")
                    return False
                
                log_callback("Sucesso!")
            else:
                log_callback(f"Aviso: {arquivo} não existe no servidor para esta versão (Status {response.status_code})")
                
        except Exception as e:
            log_callback(f"Falha de conexão com {arquivo}: {e}")

    log_callback("Todos os downloads solicitados foram finalizados!")
    return True # Indica que tudo correu até o fim sem cancelamentos