# =========================================================
# MONTA AUTOMATICAMENTE OS NOMES DOS ARQUIVOS
# =========================================================

def gerar_arquivos(versao, path):
    
    versao_formatada = versao.replace(".", "_")
    full_version = f"{versao_formatada}_{path}"

    arquivos = [
        f"CONC_V_RLS_{full_version}.zip",
        
        f"installConc-econect-cli-V_RLS_{full_version}.jar",
        f"installConc-econect-srv-V_RLS_{full_version}.jar",
        f"installPdv-econect-V_RLS_{full_version}.jar",
        
        f"PDV_V_RLS_{full_version}.zip",
        f"V_RLS_{full_version}.econect"  
    ]

    return arquivos