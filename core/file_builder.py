# =========================================================
# MONTA AUTOMATICAMENTE OS NOMES E PASTAS DOS ARQUIVOS
# =========================================================

def gerar_arquivos(versao, path):
    versao = versao.strip()
    path = path.strip()
    
    if not versao or not path:
        return []

    versao_formatada = versao.replace(".", "_")
    full_version = f"{versao_formatada}_{path}"

    arquivos = [
        {
            "pasta": "Econect-Concentrador/patch",
            "arquivo": f"CONC_V_RLS_{full_version}.zip"
        },
        {
            "pasta": "Econect-Concentrador/instalador", 
            "arquivo": f"installConc-econect-cli-V_RLS_{full_version}.jar"
        },
        {
            "pasta": "Econect-Concentrador/instalador", 
            "arquivo": f"installConc-econect-srv-V_RLS_{full_version}.jar"
        },
        {
            "pasta": "Econect-PDV/instalador", 
            "arquivo": f"installPdv-econect-V_RLS_{full_version}.jar"
        },
        {
            "pasta": "Econect-PDV/patch",
            "arquivo": f"PDV_V_RLS_{full_version}.zip"
        },
        {
            "pasta": "", 
            "arquivo": f"V_RLS_{full_version}.econect"  
        }
    ]

    return arquivos