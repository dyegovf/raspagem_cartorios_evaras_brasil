import sys
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import unicodedata


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
estados_comparar = sorted(df['estado'].dropna().unique())

# Função para normalizar nomes de colunas para camelCase, sem acentos e sem caracteres especiais
def normalizar_nome_campo(nome):
    nome = unicodedata.normalize('NFKD', nome)
    nome = ''.join([c for c in nome if not unicodedata.combining(c)])
    nome = ''.join([c for c in nome if c.isalnum() or c.isspace()])
    partes = nome.lower().split()
    if not partes:
        return ''
    return partes[0] + ''.join(p.capitalize() for p in partes[1:])

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

# Substitui o campo municipio pelo valor normalizado
df['municipio'] = df.apply(lambda row: normalize_nome(row['municipio'], row['estado']), axis=1)

# Padroniza os valores da coluna 'tipo' para 'cartorio' e 'vara' (minúsculo, sem acento ou caractere especial)
def padronizar_tipo(valor):
    if not isinstance(valor, str):
        return valor
    valor = unicodedata.normalize('NFKD', valor)
    valor = ''.join([c for c in valor if not unicodedata.combining(c)])
    valor = ''.join([c for c in valor if c.isalnum() or c.isspace()])
    valor = valor.lower().strip()
    if valor == 'cartorio' or valor == 'cartorio judicial':
        return 'cartorio'
    if valor == 'vara':
        return 'vara'
    return valor
df['tipo'] = df['tipo'].apply(padronizar_tipo)

# Identificar o(s) tipo(s) presentes no arquivo
tipos_arquivo = set(df['tipo'].unique())
tipo_cartorio = 'cartorio' in tipos_arquivo and len(tipos_arquivo) == 1
tipo_vara = 'vara' in tipos_arquivo and len(tipos_arquivo) == 1
tipo_ambos = len(tipos_arquivo) > 1

# Contagem do arquivo por Estado e Município
def contagem_arquivo(df, tipo):
    df = df.copy()
    if tipo == 'Cartório':
        filtro = df[df['tipo'] == 'Cartório']
        return filtro.groupby(['estado', 'municipio']).size().reset_index(name='cartoriosArquivo')
    elif tipo == 'Vara':
        filtro = df[df['tipo'] == 'Vara']
        return filtro.groupby(['estado', 'municipio']).size().reset_index(name='varasArquivo')
    else:
        return df.groupby(['estado', 'municipio']).size().reset_index(name='cartorioEVaraArquivo')

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
        municipio = municipio_norm
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
for idx_estado, estado in enumerate(estados_comparar, 1):
    print(f"\nValidando {estado} [{str(idx_estado).zfill(2)}/{str(len(estados_comparar)).zfill(2)}] no site...")
    resultado_estado = defaultdict(lambda: {'CartoriosSite': 0, 'VarasSite': 0, 'CartoriosEVaraSite': 0})
    url_estado = f"https://cartorios.info/cartorios-{estado.lower()}.html"
    response = requests.get(url_estado)
    soup = BeautifulSoup(response.content, 'html.parser')
    cidades_div = soup.find('div', id='cidades')
    if not cidades_div:
        continue
    cidades = cidades_div.find_all('div', class_='cidades')
    total_municipios = len(cidades)
    for idx_mun, cidade in enumerate(cidades, 1):
        a_tag = cidade.find('a', href=True)
        if not a_tag:
            continue
        link = a_tag['href']
        url_municipio = f"https://cartorios.info/{link}"
        print(f"- Municípios processados: {idx_mun}/{total_municipios}", end='\r')
        resp = requests.get(url_municipio)
        soup_mun = BeautifulSoup(resp.content, 'html.parser')
        # Nome do município
        path = link.split("cartorios-de-")[-1].split(f"-{estado.lower()}")[0]
        municipio = ' '.join([parte.capitalize() for parte in path.split('-')])
        municipio_norm = normalize_nome(municipio)
        municipio = municipio_norm
        # Cartórios
        div_cartorios = soup_mun.find('div', id='cartorios')
        if div_cartorios:
            cartorios = div_cartorios.find_all('div', class_='row', id=True)
            resultado_estado[(estado, municipio_norm)]['CartoriosSite'] = len(cartorios)
        else:
            resultado_estado[(estado, municipio_norm)]['CartoriosSite'] = 0
        # Varas
        div_varas = soup_mun.find('div', id='varas')
        if div_varas:
            varas = div_varas.find_all('div', class_='row', id=True)
            resultado_estado[(estado, municipio_norm)]['VarasSite'] = len(varas)
        else:
            resultado_estado[(estado, municipio_norm)]['VarasSite'] = 0
        resultado_estado[(estado, municipio_norm)]['CartoriosEVaraSite'] = resultado_estado[(estado, municipio_norm)]['CartoriosSite'] + resultado_estado[(estado, municipio_norm)]['VarasSite']
    contagem_site_total.update(resultado_estado)
    print(f"- Municípios processados: {total_municipios}/{total_municipios}")

# Gerar DataFrame de validação
if tipo_cartorio:
    df_arquivo = contagem_arquivo(df, 'Cartório')
    rows = []
    # print("\nDEBUG: Chaves do arquivo:")
    # print(df_arquivo[['Estado', 'MunicipioNorm']].drop_duplicates().to_string(index=False))
    # print("\nDEBUG: Chaves do site:")
    # print([k for k in contagem_site_total.keys()])
    for _, row in df_arquivo.iterrows():
        estado, municipio, qtd_arquivo = row['estado'], row['municipio'], row['cartoriosArquivo']
        qtd_site = contagem_site_total.get((estado, municipio), {}).get('CartoriosSite', 0)
        dif = qtd_arquivo - qtd_site
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'estado': estado,
            'municipio': municipio,
            'cartoriosArquivo': qtd_arquivo,
            'cartoriosSite': qtd_site,
            'difCartorios': dif,
            'statusCartorio': status
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
        estado, municipio, qtd_arquivo = row['estado'], row['municipio'], row['varasArquivo']
        qtd_site = contagem_site_total.get((estado, municipio), {}).get('VarasSite', 0)
        dif = qtd_arquivo - qtd_site
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'estado': estado,
            'municipio': municipio,
            'varasArquivo': qtd_arquivo,
            'varasSite': qtd_site,
            'difVaras': dif,
            'statusVara': status
        })
    df_validacao = pd.DataFrame(rows)
    aba = 'validacao_vara'
elif tipo_ambos:
    # Gerar linhas separadas para cartório e vara
    df_cartorio = df[df['tipo'] == 'cartorio'].groupby(['estado', 'municipio']).size().reset_index(name='cartoriosArquivo')
    df_vara = df[df['tipo'] == 'vara'].groupby(['estado', 'municipio']).size().reset_index(name='varasArquivo')
    rows = []
    # Cartórios
    for _, row in df_cartorio.iterrows():
        estado, municipio, qtd_arquivo = row['estado'], row['municipio'], row['cartoriosArquivo']
        qtd_site = contagem_site_total.get((estado, municipio), {}).get('CartoriosSite', 0)
        dif = qtd_arquivo - qtd_site
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'estado': estado,
            'municipio': municipio,
            'tipo': 'cartorio',
            'quantidadeArquivo': qtd_arquivo,
            'quantidadeSite': qtd_site,
            'diferenca': dif,
            'status': status
        })
    # Varas
    for _, row in df_vara.iterrows():
        estado, municipio, qtd_arquivo = row['estado'], row['municipio'], row['varasArquivo']
        qtd_site = contagem_site_total.get((estado, municipio), {}).get('VarasSite', 0)
        dif = qtd_arquivo - qtd_site
        status = 'Ok' if qtd_arquivo == qtd_site else 'Divergente'
        rows.append({
            'estado': estado,
            'municipio': municipio,
            'tipo': 'vara',
            'quantidadeArquivo': qtd_arquivo,
            'quantidadeSite': qtd_site,
            'diferenca': dif,
            'status': status
        })
    df_validacao = pd.DataFrame(rows)
    aba = 'validacao_cartorio_evara'
else:
    print("Tipo de arquivo não reconhecido para validação.")
    exit()

# Salvar relatório na pasta data/validacao com nome baseado no arquivo original
import os
from datetime import datetime
dir_validacao = os.path.join('data', 'validacao')
os.makedirs(dir_validacao, exist_ok=True)
nome_base = os.path.splitext(os.path.basename(arquivo))[0]
datahora = datetime.now().strftime('%Y%m%d_%H%M')
nome_relatorio = f"{datahora}_validacao_{nome_base}.xlsx"
caminho_relatorio = os.path.join(dir_validacao, nome_relatorio)
df_validacao.columns = [normalizar_nome_campo(c) for c in df_validacao.columns]
df_validacao.to_excel(caminho_relatorio, index=False, sheet_name=aba)
print(f"\nRelatório de validação salvo em: {caminho_relatorio} (aba: {aba})")