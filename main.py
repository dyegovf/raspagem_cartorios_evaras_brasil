import os
import time
import unicodedata
import re
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import concurrent.futures
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
    text = text.lower()
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[áàãâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòõôö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[^a-z0-9_]', '_', text)
    return text

def normalizar_campo(valor, manter_ponto_virgula=False):
    if not isinstance(valor, str):
        return valor
    valor = valor.lower()
    valor = valor.replace('-', ' ')
    if manter_ponto_virgula:
        valor = unicodedata.normalize('NFKD', valor)
        valor = ''.join([c for c in valor if not unicodedata.combining(c)])
        valor = ''.join([c for c in valor if c.isalnum() or c.isspace() or c == ';'])
    else:
        valor = unicodedata.normalize('NFKD', valor)
        valor = ''.join([c for c in valor if not unicodedata.combining(c)])
        valor = ''.join([c for c in valor if c.isalnum() or c.isspace()])
    valor = ' '.join(valor.split())
    return valor

def normalizar_nome_campo(nome):
    nome = unicodedata.normalize('NFKD', nome)
    nome = ''.join([c for c in nome if not unicodedata.combining(c)])
    nome = ''.join([c for c in nome if c.isalnum() or c.isspace()])
    partes = nome.lower().split()
    if not partes:
        return ''
    return partes[0] + ''.join(p.capitalize() for p in partes[1:])

# Função para gerar nome de arquivo com data e hora
def nome_arquivo_datahora(nome_base, extensao):
    agora = datetime.now()
    data_hora = agora.strftime("%Y%m%d_%H%M")
    return f"{data_hora}_{nome_base}.{extensao}"

data_geracao = datetime.now().strftime("%Y%m%d")
data_geracao_formatada = datetime.now().strftime("%d/%m/%y")
hora_inicio = datetime.now().strftime("%H:%M")

print("📌 Escolha o tipo de dado a ser extraído:")
print("1 - Apenas Cartórios")
print("2 - Apenas Varas Judiciais")
print("3 - Ambos")
tipo_escolhido = tipos.get(input("Digite o número correspondente: ").strip(), "Ambos")

print("\n📁 Escolha o formato de saída:")
print("1 - CSV único")
print("2 - XLSX por estado")
print("3 - CSV por estado")
print("4 - XLSX único")
formato_escolhido = formatos.get(input("Digite o número correspondente: ").strip(), "csv_unico")

if formato_escolhido in ["csv_unico", "xls_unico"]:
    estados_selecionados = estados
    print("\n🔄 Formato único selecionado — todos os estados serão processados automaticamente.")
else:
    print("\n🌎 Escolha o(s) estado(s) a ser(em) processado(s):")
    print("Digite a(s) sigla(s) do(s) estado(s) separadas por vírgula (ex: SP, RJ, DF) ou 'TODOS' para processar o Brasil inteiro")
    estado_input = input("Estado(s): ").strip().upper()

    if estado_input == "TODOS":
        estados_selecionados = estados
    else:
        siglas = [sigla.strip() for sigla in estado_input.split(',') if sigla.strip()]
        estados_invalidos = [sigla for sigla in siglas if sigla not in estados]
        if estados_invalidos:
            print(f"⚠️ Estado(s) inválido(s): {', '.join(estados_invalidos)}. Encerrando.")
            exit()
        estados_selecionados = siglas

    # Se mais de um estado foi selecionado, forçar formato único
    if len(estados_selecionados) > 1:
        print("\n🔄 Múltiplos estados selecionados — a saída será gerada em arquivo único XLSX.")
        formato_escolhido = "xls_unico"

base_destino = os.getenv("PASTA_CARTORIO", "./data")
subpasta = f"{slugify(tipo_escolhido)}_{formato_escolhido}"
pasta_destino = os.path.join(base_destino, subpasta)
os.makedirs(pasta_destino, exist_ok=True)

def filtrar_dados(dados, tipo):
    if tipo == "Ambos":
        return dados
    return [d for d in dados if d.get("Tipo") == tipo]

todos_dados = []

campos_esperados = [
    'Estado', 'Município', 'Cartório', 'Serviços', 'Status do Cartório', 'Tipo',
    'Escrivão Titular', 'Data de Criação', 'CNS'
]
campos_esperados_camel = [normalizar_nome_campo(c) for c in campos_esperados]

def processar_municipio(args):
    url_municipio, estado, tipo_escolhido = args
    dados_municipio = extrair_dados_municipio(url_municipio, estado)
    time.sleep(0.3)  # Delay para evitar bloqueio do servidor
    dados_filtrados = filtrar_dados(dados_municipio, tipo_escolhido)
    return dados_filtrados

print(f"\n🚀 Iniciando raspagem: {tipo_escolhido} → {formato_escolhido}")
for idx_estado, estado in enumerate(estados_selecionados, 1):
    print(f"\nRaspando {estado} [{str(idx_estado).zfill(2)}/{str(len(estados_selecionados)).zfill(2)}] do site...")
    try:
        links_municipios = extrair_links_municipios(estado)
        dados_estado = []
        total = len(links_municipios)
        max_msg_len = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            args_list = [(url, estado, tipo_escolhido) for url in links_municipios]
            resultados = executor.map(processar_municipio, args_list)
            for i, dados_filtrados in enumerate(resultados, 1):
                dados_estado.extend(dados_filtrados)
                if i == total or i % 10 == 0:
                    msg = f"Municipios raspados: {i}/{total}"
                    max_msg_len = max(max_msg_len, len(msg))
                    print(f"{msg}{' ' * (max_msg_len - len(msg))}", end='\r')
            # Imprime a linha final de progresso com o check de conclusão
            msg = f"Municipios raspados: {total}/{total} ✅"
            print(f"{msg}{' ' * (max_msg_len - len(msg))}")

        if formato_escolhido == "csv_unico":
            todos_dados.extend(dados_estado)

        elif formato_escolhido == "xls_unico":
            todos_dados.extend(dados_estado)

        elif formato_escolhido == "csv_porArquivo" or formato_escolhido == "xls_porArquivo":
            # Preencher campos ausentes, mas NÃO normalizar os valores
            for registro in dados_estado:
                for campo in campos_esperados:
                    if campo not in registro:
                        registro[campo] = 'Não informado'

            df = pd.DataFrame(dados_estado)
            for campo in campos_esperados:
                if campo not in df.columns:
                    df[campo] = 'Não informado'
            df = df[campos_esperados]
            df.columns = campos_esperados_camel
            if tipo_escolhido == "Cartório":
                nome_base = f"cartorios_{estado}"
            elif tipo_escolhido == "Vara":
                nome_base = f"varas_{estado}"
            else:
                nome_base = f"cartorios_e_varas_{estado}"
            if formato_escolhido == "csv_porArquivo":
                nome_arquivo = nome_arquivo_datahora(nome_base, "csv")
                caminho_csv = os.path.join(pasta_destino, nome_arquivo)
                df.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
                print(f"✅ Arquivo gerado para {estado} ({len(dados_estado)} registros)")
            else:
                nome_arquivo = nome_arquivo_datahora(nome_base, "xlsx")
                caminho_xlsx = os.path.join(pasta_destino, nome_arquivo)
                df.to_excel(caminho_xlsx, index=False)
                print(f"✅ Arquivo gerado para {estado} ({len(dados_estado)} registros)")

    except Exception as e:
        print(f"\n⚠️ Erro ao processar {estado}: {e}")

for registro in todos_dados:
    for campo in campos_esperados:
        if campo not in registro:
            registro[campo] = 'Não informado'

if formato_escolhido == "csv_unico":
    df = pd.DataFrame(todos_dados)[campos_esperados]
    # Remove duplicatas apenas se todos os campos principais forem iguais, incluindo CNS
    df = df.drop_duplicates(subset=['Estado', 'Município', 'Cartório', 'CNS'])
    df.columns = campos_esperados_camel
    if tipo_escolhido == "Cartório":
        nome_base = "cartorios_brasil"
    elif tipo_escolhido == "Vara":
        nome_base = "varas_brasil"
    else:
        nome_base = "cartorios_e_varas_brasil"
    nome_arquivo = nome_arquivo_datahora(nome_base, "csv")
    caminho_csv_unico = os.path.join(pasta_destino, nome_arquivo)
    df.to_csv(caminho_csv_unico, index=False, encoding='utf-8-sig')
    print(f"\n📁 CSV único gerado: {caminho_csv_unico} ({len(df)} registros)")

elif formato_escolhido == "xls_unico":
    df = pd.DataFrame(todos_dados)[campos_esperados]
    # Remove duplicatas apenas se todos os campos principais forem iguais, incluindo CNS
    df = df.drop_duplicates(subset=['Estado', 'Município', 'Cartório', 'CNS'])
    df.columns = campos_esperados_camel
    if tipo_escolhido == "Cartório":
        nome_base = "cartorios_brasil"
    elif tipo_escolhido == "Vara":
        nome_base = "varas_brasil"
    else:
        nome_base = "cartorios_e_varas_brasil"
    nome_arquivo = nome_arquivo_datahora(nome_base, "xlsx")
    caminho_xls_unico = os.path.join(pasta_destino, nome_arquivo)
    df.to_excel(caminho_xls_unico, index=False)
    print(f"\n📁 XLSX único gerado: {caminho_xls_unico} ({len(df)} registros)")

hora_fim = datetime.now().strftime("%H:%M")
print(f"\n📅 Data de extração: {data_geracao_formatada}")
print(f"⏰ Hora de início: {hora_inicio}")
print(f"⏰ Hora de fim: {hora_fim}")
print("\n🏁 Raspagem concluída com sucesso.")