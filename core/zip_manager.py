import zipfile
import os

def criar_zip(pasta_origem, nome_zip, log_callback=print):
    """
    Compacta a pasta de origem ignorando arquivos zerados ou inexistentes.
    """
    try:
        if not os.path.exists(pasta_origem) or not os.listdir(pasta_origem):
            log_callback("Aviso: Nenhum arquivo válido encontrado para compactar.")
            return

        with zipfile.ZipFile(nome_zip, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(pasta_origem):
                for file in files:
                    caminho_completo = os.path.join(root, file)
                    
                    # Filtro de segurança: Apenas compacta arquivos maiores que 0 bytes
                    if os.path.getsize(caminho_completo) > 0:
                        caminho_relativo = os.path.relpath(caminho_completo, pasta_origem)
                        zipf.write(caminho_completo, arcname=caminho_relativo)
                        log_callback(f"Compactando: {file}")
                    else:
                        log_callback(f"Ignorando arquivo vazio: {file}")

        log_callback("Arquivo ZIP criado com sucesso!")
        
    except Exception as e:
        log_callback(f"Erro ao compactar arquivos: {e}")