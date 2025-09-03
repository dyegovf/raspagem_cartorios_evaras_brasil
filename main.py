import os
import time
import pandas as pd
from dotenv import load_dotenv
from scripts.raspagem_core import extrair_links_municipios, extrair_dados_municipio

load_dotenv()

# Lista de estados brasileiros
estados = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO'
]

# Opções de tipo e formato
tipos = {
    "1": "Cartório",
    "2": "Vara",
    "3": "Ambos"
}

formatos = {
    "1": "csv_unico",
    "2": "xls_porArquivo"
}

# Escolha do tipo de dado
print("📌 Escolha o tipo de dado a ser extraído:")
print("1 - Apenas Cartórios")
print("2 - Apenas Varas Judiciais")
print("3 - Ambos")
tipo_escolhido = tipos.get(input("Digite o número correspondente: ").strip(), "Ambos")

# Escolha do formato de saída
print("\n📁 Escolha o formato de saída:")
print("1 - CSV único")
print("2 - XLSX por estado")
formato_escolhido = formatos.get(input("Digite o número correspondente: ").strip(), "csv_unico")

# Escolha do estado
print("\n🌎 Escolha o estado a ser processado:")
print("Digite a sigla do estado (ex: SP, RJ, DF) ou 'TODOS' para processar o Brasil inteiro")
estado_input = input("Estado: ").strip().upper()

if estado_input == "TODOS":
    estados_selecionados = estados
elif estado_input in estados:
    estados_selecionados = [estado_input]
else:
    print(f"⚠️ Estado inválido: {estado_input}. Encerrando.")
    exit()

# Pasta de destino
base_destino = os.getenv("PASTA_CARTORIO", "./data")
subpasta = f"{tipo_escolhido.lower()}_{formato_escolhido}"
pasta_destino = os.path.join(base_destino, subpasta)
os.makedirs(pasta_destino, exist_ok=True)

# Função de filtro
def filtrar_dados(dados, tipo):
    if tipo == "Ambos":
        return dados
    return [d for d in dados if d["Tipo"] == tipo]

# Execução
print(f"\n🚀 Iniciando raspagem: {tipo_escolhido} → {formato_escolhido} → {estado_input}")
for estado in estados_selecionados:
    print(f"🔍 Processando estado {estado}...")
    try:
        links_municipios = extrair_links_municipios(estado)
        dados_estado = []

        for url_municipio in links_municipios:
            print(f"   ➤ Extraindo dados de {url_municipio}")
            dados_municipio = extrair_dados_municipio(url_municipio, estado)
            dados_filtrados = filtrar_dados(dados_municipio, tipo_escolhido)
            dados_estado.extend(dados_filtrados)
            time.sleep(1)

        if formato_escolhido == "csv_unico":
            caminho_csv = os.path.join(pasta_destino, f"{estado}.csv")
            pd.DataFrame(dados_estado).to_csv(caminho_csv, index=False, encoding='utf-8-sig')
        else:
            caminho_xlsx = os.path.join(pasta_destino, f"cartorios_{estado}.xlsx")
            pd.DataFrame(dados_estado).to_excel(caminho_xlsx, index=False)

        print(f"✅ Arquivo gerado para {estado}")

    except Exception as e:
        print(f"⚠️ Erro ao processar {estado}: {e}")

print("\n🏁 Raspagem concluída com sucesso.")