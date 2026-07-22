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