import os

# =========================================================
# MONTA AUTOMATICAMENTE OS NOMES E PASTAS DOS ARQUIVOS
# =========================================================

def gerar_arquivos(versao, path, incluir_restaurante=True, bits=None):
    
    # ==========================================
    # 1. TRATAMENTO PARA PASTA DE INSTALADORES
    # ==========================================
    if versao == "instaladores":
        if bits == "64":
            return [
                {"pasta": "", "arquivo": "mysql-5.5.38-winx64.msi"},
                {"pasta": "", "arquivo": "mysql-gui-tools-5.0-r12-win32.msi"},
                {"pasta": "", "arquivo": "FileZilla_Server-0_9_50.exe"},
                {"pasta": "", "arquivo": "JRE Windows 64bits.exe"},
                {"pasta": "", "arquivo": "sshsecureshellclient-3.2.2.exe"}
            ]
        elif bits == "32":
            return [
                {"pasta": "", "arquivo": "mysql-5.5.38-win32.msi"},
                {"pasta": "", "arquivo": "mysql-gui-tools-5.0-r12-win32.msi"},
                {"pasta": "", "arquivo": "FileZilla_Server-0_9_50.exe"},
                {"pasta": "", "arquivo": "JRE Windows 32bits.exe"},
                {"pasta": "", "arquivo": "sshsecureshellclient-3.2.2.exe"}
            ]
        else:
            return [
                {"pasta": "", "arquivo": "mysql-5.5.38-winx64.msi"},
                {"pasta": "", "arquivo": "mysql-5.5.38-win32.msi"},
                {"pasta": "", "arquivo": "mysql-gui-tools-5.0-r12-win32.msi"},
                {"pasta": "", "arquivo": "FileZilla_Server-0_9_50.exe"},
                {"pasta": "", "arquivo": "JRE Windows 64bits.exe"},
                {"pasta": "", "arquivo": "JRE Windows 32bits.exe"},
                {"pasta": "", "arquivo": "sshsecureshellclient-3.2.2.exe"}
            ]
            
    # ==========================================
    # 2. TRATAMENTO PARA SISTEMA OPERACIONAL
    # ==========================================
    if versao == "sistema_operacional":
        return [
            {"pasta": "", "arquivo": "99-usb-serial.rules"},
            {"pasta": "", "arquivo": "genlax-1.4.0-bematech.rar"},
            {"pasta": "", "arquivo": "installGerSO-V_RLS_1_0_0_9.jar"},
            {"pasta": "", "arquivo": "Econect-Lubuntu-15-10-07.iso"},
            {"pasta": "", "arquivo": "Econect-Lubuntu-18-04-05.iso"},
            {"pasta": "", "arquivo": "Linux-Mint-econect-1.6-x64.iso"},
            {"pasta": "", "arquivo": "linux-mint-xfce-econect-21.3.0-x64.iso"}
        ]

    # ==========================================
    # 3. TRATAMENTO NORMAL (VERSÕES PDV/CONC)
    # ==========================================
    if not versao or not path or path == "Selecione":
        return []

    versao_formatada = versao.replace(".", "_")
    full_version = f"{versao_formatada}_{path}"

    # Lista completa incluindo o Restaurante para que ele apareça no Pacote Individual
    arquivos = [
        {"pasta": "Econect-Concentrador/patch", "arquivo": f"CONC_V_RLS_{full_version}.zip"},
        {"pasta": "Econect-Concentrador/instalador", "arquivo": f"installConc-econect-cli-V_RLS_{full_version}.jar"},
        {"pasta": "Econect-Concentrador/instalador", "arquivo": f"installConc-econect-srv-V_RLS_{full_version}.jar"},
        {"pasta": "Econect-PDV/instalador", "arquivo": f"installPdv-econect-V_RLS_{full_version}.jar"},
        {"pasta": "Econect-PDV/patch", "arquivo": f"PDV_V_RLS_{full_version}.zip"},
        {"pasta": "", "arquivo": f"V_RLS_{full_version}.econect"},
        {"pasta": "Econect-Restaurante/instalador", "arquivo": f"installRES-econect-V_RLS_{full_version}.jar"}
    ]

    return arquivos

# =========================================================
# FUNÇÕES DE QUEBRA (SPLIT) E JUNÇÃO (MERGE) DE ARQUIVOS
# =========================================================

def split_file(file_path, chunk_size=1990000000):
    """
    Divide um arquivo grande em múltiplas partes menores.
    Lê e grava em pequenos blocos (buffer) para não estourar a memória RAM.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    partes_geradas = []
    parte_num = 1
    buffer_size = 5 * 1024 * 1024 # Buffer de leitura de 5MB
    
    tamanho_total = os.path.getsize(file_path)
    bytes_lidos_total = 0

    # Abre o arquivo original apenas para leitura
    with open(file_path, 'rb') as f_original:
        while bytes_lidos_total < tamanho_total:
            nome_parte = f"{file_path}.part{parte_num}"
            bytes_na_parte = 0
            
            # Abre/Cria o arquivo da parte atual para escrita
            with open(nome_parte, 'wb') as f_parte:
                # Continua lendo blocos de 5MB até atingir o chunk_size (~1.9GB)
                while bytes_na_parte < chunk_size and bytes_lidos_total < tamanho_total:
                    # Calcula quanto falta ler para não ultrapassar o limite da parte ou do arquivo
                    bytes_para_ler = min(buffer_size, chunk_size - bytes_na_parte, tamanho_total - bytes_lidos_total)
                    
                    chunk = f_original.read(bytes_para_ler)
                    if not chunk:
                        break
                        
                    f_parte.write(chunk)
                    bytes_na_parte += len(chunk)
                    bytes_lidos_total += len(chunk)
                    
            partes_geradas.append(nome_parte)
            parte_num += 1
            
    return partes_geradas

def merge_files(part_files, output_path):
    """
    Junta múltiplas partes de volta em um único arquivo original.
    Lê os arquivos em pequenos buffers para não estourar a memória RAM.
    """
    if not part_files:
        return None

    # Ordena as partes numericamente pelo final da string (.part1, .part2, etc.)
    # Isso é vital para remontar na ordem certa caso o array venha bagunçado do Telegram
    part_files_sorted = sorted(part_files, key=lambda x: int(x.split('.part')[-1]))
    
    buffer_size = 5 * 1024 * 1024 # Buffer de 5MB por leitura
    
    # Abre o arquivo final em modo binário de escrita
    with open(output_path, 'wb') as f_final:
        for parte in part_files_sorted:
            if not os.path.exists(parte):
                raise FileNotFoundError(f"Parte ausente para o merge: {parte}")
                
            with open(parte, 'rb') as f_parte:
                while True:
                    chunk = f_parte.read(buffer_size)
                    if not chunk:
                        break
                    f_final.write(chunk)
                    
    return output_path