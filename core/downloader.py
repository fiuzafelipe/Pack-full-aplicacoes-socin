import os
import time
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
    
    if modo == "atualizadores":
        arquivos = [a for a in arquivos if a["arquivo"].startswith("CONC_V_RLS") or a["arquivo"].startswith("PDV_V_RLS") or a["arquivo"].startswith("V_RLS")]
    elif apenas_arquivo:
        arquivos = [a for a in arquivos if a["arquivo"] == apenas_arquivo]
    elif modo == "completo" and not incluir_restaurante:
        arquivos = [a for a in arquivos if "installRES" not in a["arquivo"]]

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
            progress_callback(0.0, "Calculando velocidade...", arquivo)

        try:
            response = session.get(download_url, stream=True, timeout=30)
            
            if response.status_code == 200:
                tamanho_total = int(response.headers.get('content-length', 0))
                total_mb = tamanho_total / (1024 * 1024)
                tamanho_baixado = 0
                
                caminho_arquivo = os.path.join(pasta_temp, arquivo)
                download_concluido = True 
                
                tempo_inicio = time.time()
                
                with open(caminho_arquivo, "wb") as f:
                    # Bloco de 256KB para giro rápido dos decimais na tela
                    for chunk in response.iter_content(chunk_size=262144):
                        if cancel_callback and cancel_callback():
                            download_concluido = False
                            break
                            
                        if chunk:
                            f.write(chunk)
                            tamanho_baixado += len(chunk)
                            
                            if tamanho_total > 0 and progress_callback:
                                tempo_decorrido = time.time() - tempo_inicio
                                
                                if tempo_decorrido > 0:
                                    velocidade_bps = tamanho_baixado / tempo_decorrido
                                    bytes_restantes = tamanho_total - tamanho_baixado
                                    tempo_restante_seg = bytes_restantes / velocidade_bps
                                    
                                    # LÓGICA DO CHROME PARA A VELOCIDADE (KB/s ou MB/s)
                                    if velocidade_bps < (1024 * 1024):
                                        velocidade_str = f"{int(velocidade_bps / 1024)} KB/s"
                                    else:
                                        velocidade_str = f"{(velocidade_bps / (1024 * 1024)):.1f} MB/s"
                                    
                                    # LÓGICA DE TEMPO
                                    minutos = int(tempo_restante_seg // 60)
                                    segundos = int(tempo_restante_seg % 60)
                                    if minutos > 0:
                                        tempo_str = f"{minutos}:{segundos:02d} mins restantes"
                                    else:
                                        tempo_str = f"{segundos} segs restantes"
                                        
                                else:
                                    velocidade_str = "0 KB/s"
                                    tempo_str = "Calculando..."

                                # MEGABYTES COM CASAS DECIMAIS GIRANDO (.1f)
                                baixado_mb = tamanho_baixado / (1024 * 1024)
                                percentual_float = tamanho_baixado / tamanho_total
                                
                                # TEXTO NO PADRÃO EXATO DO PRINT
                                texto_stats = f"{velocidade_str} - {baixado_mb:.1f} MB de {total_mb:.1f} MB, {tempo_str}"
                                
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