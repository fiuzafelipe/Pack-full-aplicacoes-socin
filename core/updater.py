import requests

def checar_atualizacao(log_callback):
    """Verifica a última release lançada no seu GitHub"""
    url_api = "https://api.github.com/repos/fiuzafelipe/Pack-full-aplicacoes-socin/releases/latest"
    
    try:
        response = requests.get(url_api, timeout=5)
        if response.status_code == 200:
            dados = response.json()
            versao_recente = dados.get("tag_name", "Desconhecida")
            
            # Aqui você poderá implementar a lógica futura de baixar o .zip ou .exe
            # ex: link_download = dados["assets"][0]["browser_download_url"]
            
            log_callback(f"[GitHub] Verificação de Atualização: Última versão online é a {versao_recente}.")
        else:
            log_callback(f"[GitHub] Nenhuma release publicada ainda (Status {response.status_code}).")
            
    except Exception as e:
        log_callback(f"[GitHub] Aviso: Modo offline ou falha ao checar atualizações.")