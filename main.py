import os
import re
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
    "2": "xls_porArquivo",
    "3": "csv_porArquivo",
    "4": "xls_unico"
}

def slugify(text):
    # Remove acentos, cedilha e caracteres especiais, deixa só letras, números e _
    text = text.lower()
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[áàãâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòõôö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[^a-z0-9_]', '_', text)
    return text

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
print("3 - CSV por estado")
print("4 - XLSX único")
formato_escolhido = formatos.get(input("Digite o número correspondente: ").strip(), "csv_unico")

# Definição dos estados a serem processados
if formato_escolhido in ["csv_unico", "xls_unico"]:
    estados_selecionados = estados
    print("\n🔄 Formato único selecionado — todos os estados serão processados automaticamente.")
else:
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
subpasta = f"{slugify(tipo_escolhido)}_{formato_escolhido}"
pasta_destino = os.path.join(base_destino, subpasta)
os.makedirs(pasta_destino, exist_ok=True)

# Função de filtro
def filtrar_dados(dados, tipo):
    if tipo == "Ambos":
        return dados
    return [d for d in dados if d.get("Tipo") == tipo]

# Lista acumuladora para formatos únicos
todos_dados = []

# Novos campos esperados
campos_esperados = [
    'Estado', 'Município', 'Cartório', 'Serviços', 'Status do Cartório', 'Tipo',
    'Escrivão Titular', 'Data de Criação', 'CNS'
]

# Execução
print(f"\n🚀 Iniciando raspagem: {tipo_escolhido} → {formato_escolhido}")
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

        # Salvar conforme formato escolhido
        if formato_escolhido == "csv_unico":
            todos_dados.extend(dados_estado)

        elif formato_escolhido == "xls_unico":
            todos_dados.extend(dados_estado)

        elif formato_escolhido == "csv_porArquivo":
            df = pd.DataFrame(dados_estado)
            for campo in campos_esperados:
                if campo not in df.columns:
                    df[campo] = 'Não informado'
            df = df[campos_esperados]
            caminho_csv = os.path.join(pasta_destino, f"{estado}.csv")
            df.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
            print(f"✅ Arquivo gerado para {estado} ({len(dados_estado)} registros)")

        elif formato_escolhido == "xls_porArquivo":
            df = pd.DataFrame(dados_estado)
            for campo in campos_esperados:
                if campo not in df.columns:
                    df[campo] = 'Não informado'
            df = df[campos_esperados]
            caminho_xlsx = os.path.join(pasta_destino, f"cartorios_{estado}.xlsx")
            df.to_excel(caminho_xlsx, index=False)
            print(f"✅ Arquivo gerado para {estado} ({len(dados_estado)} registros)")

    except Exception as e:
        print(f"⚠️ Erro ao processar {estado}: {e}")

# Garantir consistência de colunas nos arquivos únicos
for registro in todos_dados:
    for campo in campos_esperados:
        if campo not in registro:
            registro[campo] = 'Não informado'

# Salvar arquivos únicos após o loop
if formato_escolhido == "csv_unico":
    df = pd.DataFrame(todos_dados)[campos_esperados]
    caminho_csv_unico = os.path.join(pasta_destino, "cartorios_e_varas_brasil.csv")
    df.to_csv(caminho_csv_unico, index=False, encoding='utf-8-sig')
    print(f"\n📁 CSV único gerado: {caminho_csv_unico} ({len(todos_dados)} registros)")

elif formato_escolhido == "xls_unico":
    df = pd.DataFrame(todos_dados)[campos_esperados]
    caminho_xls_unico = os.path.join(pasta_destino, "cartorios_e_varas_brasil.xlsx")
    df.to_excel(caminho_xls_unico, index=False)
    print(f"\n📁 XLSX único gerado: {caminho_xls_unico} ({len(todos_dados)} registros)")

print("\n🏁 Raspagem concluída com sucesso.")