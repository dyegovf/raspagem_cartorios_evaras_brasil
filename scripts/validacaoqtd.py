
import sys
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import unicodedata

import unicodedata
# Função para normalizar nomes (remove acentos, caracteres especiais, minúsculo)
def normalize_nome(nome, estado=None):
    if not isinstance(nome, str):
        return ''
    nome = nome.lower()
    if estado:
        sufixo = f'em {estado.lower()}'
        if nome.endswith(sufixo):
            nome = nome[: -len(sufixo)].strip()
    nome = unicodedata.normalize('NFKD', nome)
    nome = ''.join([c for c in nome if not unicodedata.combining(c)])
    nome = ''.join([c for c in nome if c.isalnum() or c.isspace()])
    nome = ' '.join(nome.split())
    return nome

# Lista de estados brasileiros
estados = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO'
]

print("Informe o caminho do arquivo CSV/XLSX gerado para comparar:")
arquivo = input("Arquivo: ").strip()

if not arquivo:
    print("Arquivo não informado. Saindo.")
    exit()





# Leitura do arquivo
if arquivo.endswith('.csv'):
    df = pd.read_csv(arquivo)
elif arquivo.endswith('.xlsx'):
    df = pd.read_excel(arquivo)
else:
    print("Arquivo deve ser .csv ou .xlsx")
    exit()

# Detecta automaticamente os estados presentes no arquivo
estados_comparar = sorted(df['Estado'].dropna().unique())
print(f"\nEstados detectados no arquivo: {', '.join(estados_comparar)}")

# Adiciona coluna normalizada logo após leitura
df['MunicipioNorm'] = df.apply(lambda row: normalize_nome(row['Município'], row['Estado']), axis=1)

# Identificar o(s) tipo(s) presentes no arquivo
tipos_arquivo = set(df['Tipo'].unique())
tipo_cartorio = 'Cartório' in tipos_arquivo and len(tipos_arquivo) == 1
tipo_vara = 'Vara' in tipos_arquivo and len(tipos_arquivo) == 1
tipo_ambos = len(tipos_arquivo) > 1

# Contagem do arquivo por Estado e Município
def contagem_arquivo(df, tipo):
    df = df.copy()
    df['MunicipioNorm'] = df.apply(lambda row: normalize_nome(row['Município'], row['Estado']), axis=1)
    if tipo == 'Cartório':
        filtro = df[df['Tipo'] == 'Cartório']
        return filtro.groupby(['Estado', 'MunicipioNorm']).size().reset_index(name='CartoriosArquivo')
    elif tipo == 'Vara':
        filtro = df[df['Tipo'] == 'Vara']
        return filtro.groupby(['Estado', 'MunicipioNorm']).size().reset_index(name='VarasArquivo')
    else:
        return df.groupby(['Estado', 'MunicipioNorm']).size().reset_index(name='CartorioEVaraArquivo')

# Contagem do site por Estado e Município
def contagem_site(sigla_estado):
    url_estado = f"https://cartorios.info/cartorios-{sigla_estado.lower()}.html"
    response = requests.get(url_estado)
    soup = BeautifulSoup(response.content, 'html.parser')
    resultado = defaultdict(lambda: {'CartoriosSite': 0, 'VarasSite': 0, 'CartoriosEVaraSite': 0})
    cidades_div = soup.find('div', id='cidades')
    if not cidades_div:
        return resultado
    cidades = cidades_div.find_all('div', class_='cidades')
    for cidade in cidades:
        a_tag = cidade.find('a', href=True)
        if not a_tag:
            continue
        link = a_tag['href']
        url_municipio = f"https://cartorios.info/{link}"
        resp = requests.get(url_municipio)
        soup_mun = BeautifulSoup(resp.content, 'html.parser')
        # Nome do município
        path = link.split("cartorios-de-")[-1].split(f"-{sigla_estado.lower()}")[0]
        municipio = ' '.join([parte.capitalize() for parte in path.split('-')])
        municipio_norm = normalize_nome(municipio)
        # Cartórios
        div_cartorios = soup_mun.find('div', id='cartorios')
        if div_cartorios:
            cartorios = div_cartorios.find_all('div', class_='row', id=True)
            resultado[(sigla_estado, municipio_norm)]['CartoriosSite'] = len(cartorios)
        else:
            resultado[(sigla_estado, municipio_norm)]['CartoriosSite'] = 0
        # Varas
        div_varas = soup_mun.find('div', id='varas')
        if div_varas:
            varas = div_varas.find_all('div', class_='row', id=True)
            resultado[(sigla_estado, municipio_norm)]['VarasSite'] = len(varas)
        else:
            resultado[(sigla_estado, municipio_norm)]['VarasSite'] = 0
        resultado[(sigla_estado, municipio_norm)]['CartoriosEVaraSite'] = resultado[(sigla_estado, municipio_norm)]['CartoriosSite'] + resultado[(sigla_estado, municipio_norm)]['VarasSite']
    return resultado

# Agregar contagem do site para todos os estados
contagem_site_total = defaultdict(lambda: {'CartoriosSite': 0, 'VarasSite': 0, 'CartoriosEVaraSite': 0})
for estado in estados_comparar:
    print(f"\nValidando {estado} no site (contagem por município)...")
    resultado_estado = contagem_site(estado)
    contagem_site_total.update(resultado_estado)

# Gerar DataFrame de validação
if tipo_cartorio:
    df_arquivo = contagem_arquivo(df, 'Cartório')
    rows = []
    # print("\nDEBUG: Chaves do arquivo:")
    # print(df_arquivo[['Estado', 'MunicipioNorm']].drop_duplicates().to_string(index=False))
    # print("\nDEBUG: Chaves do site:")
    # print([k for k in contagem_site_total.keys()])
    for _, row in df_arquivo.iterrows():
        estado, municipio_norm, qtd_arquivo = row['Estado'], row['MunicipioNorm'], row['CartoriosArquivo']
        qtd_site = contagem_site_total.get((estado, municipio_norm), {}).get('CartoriosSite', 0)
        dif = qtd_arquivo - qtd_site
        # Nome original do município
        municipio_exib = df[(df['Estado'] == estado) & (df['MunicipioNorm'] == municipio_norm)]['Município'].iloc[0] if not df[(df['Estado'] == estado) & (df['MunicipioNorm'] == municipio_norm)].empty else ''
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'Estado': estado,
            'Municipio': municipio_exib,
            'MunicipioNorm': municipio_norm,
            'CartoriosArquivo': qtd_arquivo,
            'CartoriosSite': qtd_site,
            'DifCartorios': dif,
            'StatusCartorio': status
        })
    df_validacao = pd.DataFrame(rows)
    aba = 'validacao_cartorio'
elif tipo_vara:
    df_arquivo = contagem_arquivo(df, 'Vara')
    rows = []
    # print("\nDEBUG: Chaves do arquivo:")
    # print(df_arquivo[['Estado', 'MunicipioNorm']].drop_duplicates().to_string(index=False))
    # print("\nDEBUG: Chaves do site:")
    # print([k for k in contagem_site_total.keys()])
    for _, row in df_arquivo.iterrows():
        estado, municipio_norm, qtd_arquivo = row['Estado'], row['MunicipioNorm'], row['VarasArquivo']
        qtd_site = contagem_site_total.get((estado, municipio_norm), {}).get('VarasSite', 0)
        dif = qtd_arquivo - qtd_site
        municipio_exib = df[(df['Estado'] == estado) & (df['MunicipioNorm'] == municipio_norm)]['Município'].iloc[0] if not df[(df['Estado'] == estado) & (df['MunicipioNorm'] == municipio_norm)].empty else ''
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'Estado': estado,
            'Municipio': municipio_exib,
            'MunicipioNorm': municipio_norm,
            'VarasArquivo': qtd_arquivo,
            'VarasSite': qtd_site,
            'DifVaras': dif,
            'StatusVara': status
        })
    df_validacao = pd.DataFrame(rows)
    aba = 'validacao_vara'
elif tipo_ambos:
    df_arquivo = contagem_arquivo(df, 'Ambos')
    rows = []
    # print("\nDEBUG: Chaves do arquivo:")
    # print(df_arquivo[['Estado', 'MunicipioNorm']].drop_duplicates().to_string(index=False))
    # print("\nDEBUG: Chaves do site:")
    # print([k for k in contagem_site_total.keys()])
    for _, row in df_arquivo.iterrows():
        estado, municipio_norm, qtd_arquivo = row['Estado'], row['MunicipioNorm'], row['CartorioEVaraArquivo']
        qtd_site = contagem_site_total.get((estado, municipio_norm), {}).get('CartoriosEVaraSite', 0)
        dif = qtd_arquivo - qtd_site
        municipio_exib = df[(df['Estado'] == estado) & (df['MunicipioNorm'] == municipio_norm)]['Município'].iloc[0] if not df[(df['Estado'] == estado) & (df['MunicipioNorm'] == municipio_norm)].empty else ''
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'Estado': estado,
            'Municipio': municipio_exib,
            'MunicipioNorm': municipio_norm,
            'CartorioEVaraArquivo': qtd_arquivo,
            'CartoriosEVaraSite': qtd_site,
            'DifCartorioEVara': dif,
            'StatusCartorioEVara': status
        })
    df_validacao = pd.DataFrame(rows)
    aba = 'validacao_cartorio_evara'
else:
    print("Tipo de arquivo não reconhecido para validação.")
    exit()

# Salvar relatório na pasta data/validacao com nome baseado no arquivo original
import os
dir_validacao = os.path.join('data', 'validacao')
os.makedirs(dir_validacao, exist_ok=True)
nome_base = os.path.splitext(os.path.basename(arquivo))[0]
nome_relatorio = f"validacao_{nome_base}.xlsx"
caminho_relatorio = os.path.join(dir_validacao, nome_relatorio)
df_validacao.to_excel(caminho_relatorio, index=False, sheet_name=aba)
print(f"\nRelatório de validação salvo em: {caminho_relatorio} (aba: {aba})")