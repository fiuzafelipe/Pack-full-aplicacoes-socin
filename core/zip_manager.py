import zipfile
import os


def criar_zip(pasta_origem, nome_zip):

    with zipfile.ZipFile(nome_zip, "w") as zipf:

        for root, dirs, files in os.walk(pasta_origem):

            for file in files:

                caminho_completo = os.path.join(root, file)

                zipf.write(
                    caminho_completo,
                    arcname=file
                )

                print(f"Adicionado ao ZIP: {file}")

    print(f"\nZIP criado com sucesso: {nome_zip}")