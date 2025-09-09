import sys
import os
import pandas as pd
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import unicodedata
from datetime import datetime
import concurrent.futures
import numpy as np
import openpyxl
import time

# -------------------- FUNÇÕES --------------------
def normalize_nome(nome, estado=None):
    nome = str(nome) if nome is not None else ''
    nome = nome.lower()
    if estado:
        sufixo = f' em {estado.lower()}'
        if nome.endswith(sufixo):
            nome = nome[: -len(sufixo)].strip()
    nome = unicodedata.normalize('NFKD', nome)
    nome = ''.join([c for c in nome if not unicodedata.combining(c)])
    nome = ''.join([c for c in nome if c.isalnum() or c.isspace()])
    nome = ' '.join(nome.split())
    return nome

def normalize_cns(cns):
    if not isinstance(cns, str):
        return ''
    return cns.replace('.', '').replace('-', '').replace(' ', '').strip()

def contagem_site_cns(sigla_estado):
    url_estado = f"https://cartorios.info/cartorios-{sigla_estado.lower()}.html"
    response = requests.get(url_estado)
    soup = BeautifulSoup(response.content, 'html.parser')
    resultado = []
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
            blocos = div_cartorios.find_all('div', class_='row')
            for bloco in blocos:
                nome_tag = bloco.find('h3')
                nome = nome_tag.text.strip() if nome_tag else ''
                cns = 'Não informado'
                cns_tag = bloco.find('strong', string=lambda s: s and "CNS" in s)
                if cns_tag:
                    cns_val = cns_tag.next_sibling
                    if cns_val:
                        cns = cns_val.strip()
                tipo = 'cartorio'
                resultado.append({
                    'estado': sigla_estado,
                    'municipio': municipio,
                    'municipio_norm': municipio_norm,
                    'tipo': tipo,
                    'cartorio': nome,
                    'cns': cns,
                    'cns_norm': normalize_cns(cns)
                })
        # Varas
        div_varas = soup_mun.find('div', id='varas')
        if div_varas:
            blocos = div_varas.find_all('div', class_='row')
            for bloco in blocos:
                nome_tag = bloco.find('h3')
                nome = nome_tag.text.strip() if nome_tag else ''
                cns = 'Não informado'
                cns_tag = bloco.find('strong', string=lambda s: s and "CNS" in s)
                if cns_tag:
                    cns_val = cns_tag.next_sibling
                    if cns_val:
                        cns = cns_val.strip()
                tipo = 'vara'
                resultado.append({
                    'estado': sigla_estado,
                    'municipio': municipio,
                    'municipio_norm': municipio_norm,
                    'tipo': tipo,
                    'cartorio': nome,
                    'cns': cns,
                    'cns_norm': normalize_cns(cns)
                })
    return resultado

# -------------------- CONSTANTES --------------------
estados = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO'
]

# -------------------- CÓDIGO PRINCIPAL --------------------
if __name__ == "__main__":
    hora_inicio = datetime.now().strftime("%H:%M")
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

    # Mapeamento explícito de nomes de colunas para garantir compatibilidade
    col_rename = {
        'Estado': 'estado',
        'Município': 'municipio',
        'Cartório': 'cartorio',
        'Serviços': 'servicos',
        'Status do Cartório': 'statusdocartorio',
        'Tipo': 'tipo',
        'Escrivão Titular': 'escrivaotitular',
        'Data de Criação': 'datadecriacao',
        'CNS': 'cns'
    }
    # Renomeia apenas se a coluna original existir
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})




    # Função de normalização idêntica para ambos os lados
    def normalizar_nome_coluna(nome):
        nome = unicodedata.normalize('NFKD', str(nome))
        nome = ''.join([c for c in nome if not unicodedata.combining(c)])
        nome = nome.lower().replace(' ', '').replace('í','i').replace('ú','u').replace('é','e').replace('á','a').replace('ã','a').replace('ç','c').replace('ô','o').replace('ó','o').replace('ê','e').replace('â','a').replace('õ','o').replace('à','a')
        return nome
    df.columns = [normalizar_nome_coluna(col) for col in df.columns]
    df['estado'] = df['estado'].str.upper()
    # Garante que todas as colunas de comparação existam no arquivo
    for col in ['municipio', 'cartorio', 'tipo', 'cns', 'escrivaotitular']:
        if col not in df.columns:
            df[col] = 'Não informado'
    # Normaliza campos de comparação no arquivo
    df['municipio_norm'] = df['municipio'].apply(lambda x: normalize_nome(x))
    df['cartorio_norm'] = df['cartorio'].apply(lambda x: normalize_nome(x))
    df['tipo_norm'] = df['tipo'].apply(lambda x: normalize_nome(x))
    df['cns_norm'] = df['cns'].apply(lambda x: normalize_cns(x))
    df['escrivaotitular_norm'] = df['escrivaotitular'].apply(lambda x: normalize_nome(x))

    # Filtra apenas o tipo predominante do arquivo (ex: Cartório ou Vara)
    tipo_predominante = df['tipo_norm'].mode()[0] if not df['tipo_norm'].empty else None
    if tipo_predominante:
        df = df[df['tipo_norm'] == tipo_predominante].copy()

    # Detecta automaticamente os estados presentes no arquivo
    estados_comparar = sorted(df['estado'].dropna().unique())

    # Agregar todos os dados do site
    dados_site_total = []
    for idx_estado, estado in enumerate(estados_comparar, 1):
        print(f"\nValidando {estado} [{str(idx_estado).zfill(2)}/{str(len(estados_comparar)).zfill(2)}] no site...")
        url_estado = f"https://cartorios.info/cartorios-{estado.lower()}.html"
        response = requests.get(url_estado)
        soup = BeautifulSoup(response.content, 'html.parser')
        cidades_div = soup.find('div', id='cidades')
        cidades = cidades_div.find_all('div', class_='cidades') if cidades_div else []
        total_municipios = len(cidades)
        resultado_estado = []

        def processa_municipio(cidade, estado):
            import time
            a_tag = cidade.find('a', href=True)
            if not a_tag:
                return []
            link = a_tag['href']
            url_municipio = f"https://cartorios.info/{link}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
            # Função de retry para requisições
            def get_with_retry(url, headers, max_retries=3, delay=3):
                for attempt in range(max_retries):
                    try:
                        resp = requests.get(url, headers=headers, timeout=20)
                        resp.raise_for_status()
                        return resp
                    except RequestException as e:
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                        else:
                            print(f"\n[ERRO] Falha ao acessar {url}: {e}")
                            return None
            resp = get_with_retry(url_municipio, headers)
            if resp is None:
                return []
            soup_mun = BeautifulSoup(resp.content, 'html.parser')
            time.sleep(1)  # Delay maior para evitar bloqueio
            # Extração padronizada do nome do município (breadcrumb, h1, url)
            municipio = None
            breadcrumb = soup_mun.select_one('ul.breadcrumbs li:last-child span[itemprop="name"]')
            if breadcrumb and breadcrumb.text.strip():
                municipio = breadcrumb.text.strip()
            else:
                h1_tag = soup_mun.find('h1')
                if h1_tag and 'de ' in h1_tag.text:
                    import re
                    m = re.search(r'de (.+?)( na | em | do | da | no |/|$)', h1_tag.text, re.IGNORECASE)
                    if m:
                        municipio = m.group(1).strip()
            if not municipio:
                path = link.split("cartorios-de-")[-1].split(f"-{estado.lower()}")[0]
                municipio = ' '.join([parte.capitalize() for parte in path.split('-')])
            municipio_norm = normalize_nome(municipio)
            registros = []
            div_cartorios = soup_mun.find('div', id='cartorios')
            if div_cartorios:
                blocos = div_cartorios.find_all('div', class_='row')
                for bloco in blocos:
                    nome_tag = bloco.find('h3')
                    nome = nome_tag.text.strip() if nome_tag else ''
                    cns = 'Não informado'
                    cns_tag = bloco.find('strong', string=lambda s: s and "CNS" in s)
                    if cns_tag:
                        cns_val = cns_tag.next_sibling
                        if cns_val:
                            cns = cns_val.strip()
                    # Busca escrivão titular (removendo 'desde ...')
                    escrivao = 'Não informado'
                    escrivao_tag = bloco.find('strong', string=lambda s: s and ("Escrivão Titular" in s or "Escrivao Titular" in s or "Escrivão" in s or "Escrivao" in s))
                    if escrivao_tag:
                        escrivao_val = escrivao_tag.next_sibling
                        if escrivao_val:
                            escrivao = escrivao_val.strip().split('desde')[0].strip()
                    tipo = 'Cartório'
                    registros.append({
                        'estado': estado,
                        'municipio': municipio,
                        'municipio_norm': municipio_norm,
                        'tipo': tipo,
                        'cartorio': nome,
                        'cns': cns,
                        'cns_norm': normalize_cns(cns),
                        'escrivaotitular': escrivao
                    })
            div_varas = soup_mun.find('div', id='varas')
            if div_varas:
                blocos = div_varas.find_all('div', class_='row')
                for bloco in blocos:
                    nome_tag = bloco.find('h3')
                    nome = nome_tag.text.strip() if nome_tag else ''
                    cns = 'Não informado'
                    cns_tag = bloco.find('strong', string=lambda s: s and "CNS" in s)
                    if cns_tag:
                        cns_val = cns_tag.next_sibling
                        if cns_val:
                            cns = cns_val.strip()
                    # Busca escrivão titular (removendo 'desde ...')
                    escrivao = 'Não informado'
                    escrivao_tag = bloco.find('strong', string=lambda s: s and ("Escrivão Titular" in s or "Escrivao Titular" in s or "Escrivão" in s or "Escrivao" in s))
                    if escrivao_tag:
                        escrivao_val = escrivao_tag.next_sibling
                        if escrivao_val:
                            escrivao = escrivao_val.strip().split('desde')[0].strip()
                    tipo = 'Vara'
                    registros.append({
                        'estado': estado,
                        'municipio': municipio,
                        'municipio_norm': municipio_norm,
                        'tipo': tipo,
                        'cartorio': nome,
                        'cns': cns,
                        'cns_norm': normalize_cns(cns),
                        'escrivaotitular': escrivao
                    })
            return registros

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futuros = {executor.submit(processa_municipio, cidade, estado): idx_mun for idx_mun, cidade in enumerate(cidades, 1)}
            for idx_mun, future in enumerate(concurrent.futures.as_completed(futuros), 1):
                registros = future.result()
                resultado_estado.extend(registros)
                print(f"- Municípios processados: {idx_mun}/{total_municipios}", end='\r')
        dados_site_total.extend(resultado_estado)
        print(f"- Municípios processados: {total_municipios}/{total_municipios} ✅")

    # Aqui você pode implementar apenas a exibição de divergências na tela, se desejar.
    # Exemplo: mostrar quantidade de registros divergentes
    df_arquivo = df.copy()
    df_site = pd.DataFrame(dados_site_total)
    # Garante que todas as colunas de comparação existam no site
    for col in ['municipio', 'cartorio', 'tipo', 'cns', 'escrivaotitular']:
        if col not in df_site.columns:
            df_site[col] = 'Não informado'
    # Normaliza campos de comparação no site
    df_site['estado'] = df_site['estado'].str.upper()
    df_site['municipio_norm'] = df_site['municipio'].apply(lambda x: normalize_nome(x))
    df_site['cartorio_norm'] = df_site['cartorio'].apply(lambda x: normalize_nome(x))
    df_site['tipo_norm'] = df_site['tipo'].apply(lambda x: normalize_nome(x))
    df_site['cns_norm'] = df_site['cns'].apply(lambda x: normalize_cns(x))
    df_site['escrivaotitular_norm'] = df_site['escrivaotitular'].apply(lambda x: normalize_nome(x))

    # Filtra o site para comparar apenas o mesmo tipo predominante do arquivo
    if tipo_predominante:
        df_site = df_site[df_site['tipo_norm'] == tipo_predominante].copy()
    # Chaves de comparação normalizadas (apenas estado, tipo_norm, cns_norm para comparar lado a lado mesmo com divergência no município)
    chaves = ['estado', 'tipo_norm', 'cns_norm']
    df_arquivo['origem'] = 'arquivo'
    df_site['origem'] = 'site'
    df_merge = pd.merge(
        df_arquivo,
        df_site,
        on=chaves,
        how='outer',
        suffixes=('_arquivo', '_site'),
        indicator=True
    )
    # Gera DataFrame de validação simplificado
    campos_validar = [
        ('municipio', 'municipio_arquivo', 'municipio_site', 'municipio_norm_arquivo', 'municipio_norm_site'),
        ('cartorio', 'cartorio_arquivo', 'cartorio_site', 'cartorio_norm_arquivo', 'cartorio_norm_site'),
        ('escrivaotitular', 'escrivaotitular_arquivo', 'escrivaotitular_site', 'escrivaotitular_norm_arquivo', 'escrivaotitular_norm_site'),
        ('tipo', 'tipo_arquivo', 'tipo_site', 'tipo_norm_arquivo', 'tipo_norm_site'),
        ('cns', 'cns_arquivo', 'cns_site', 'cns_norm_arquivo', 'cns_norm_site')
    ]
    linhas = []
    # Para busca eficiente dos registros originais
    df_arquivo_idx = df_arquivo.set_index(chaves, drop=False)
    df_site_idx = df_site.set_index(chaves, drop=False)

    def get_val_from_registro(registro, campo, df_ref=None, lado='arquivo'):
        # Busca o valor do campo exatamente como está no DataFrame de referência
        if registro is None or df_ref is None:
            return 'Não informado'
        if isinstance(registro, pd.DataFrame):
            registro = registro.iloc[0]
        # Busca o nome da coluna que termina com _arquivo ou _site
        possiveis = [campo, f'{campo}_{lado}', f'{campo}{lado.capitalize()}', f'{campo}_{lado.capitalize()}']
        for col in df_ref.columns:
            if col in possiveis or col.lower() == campo.lower() or col.replace('_','').lower() == campo.replace('_','').lower():
                val = registro[col] if col in registro else ''
                if pd.isna(val) or val == '':
                    return 'Não informado'
                return val
        # fallback: retorna 'Não informado'
        return 'Não informado'

    for _, row in df_merge.iterrows():
        linha = {'estado': row.get('estado', '')}
        status = 'Ok'
        origem_info = 'Ambos' if row['_merge'] == 'both' else ('Só no arquivo' if row['_merge'] == 'left_only' else 'Só no site')
        chave_tuple = tuple(row.get(k, '') for k in chaves)
        if row['_merge'] == 'both':
            for campo, campo_arq, campo_site, campo_norm_arq, campo_norm_site in campos_validar:
                val_arq = row.get(campo_arq, '')
                val_site = row.get(campo_site, '')
                val_norm_arq = row.get(campo_norm_arq, '')
                val_norm_site = row.get(campo_norm_site, '')
                if pd.isna(val_arq) or val_arq == '':
                    val_arq = 'Não informado'
                if pd.isna(val_site) or val_site == '':
                    val_site = 'Não informado'
                if pd.isna(val_norm_arq): val_norm_arq = ''
                if pd.isna(val_norm_site): val_norm_site = ''
                linha[f'{campo}_arquivo'] = val_arq
                linha[f'{campo}_site'] = val_site
                # Só marca como divergente se os valores normalizados forem diferentes E não forem ambos 'Não informado'
                if (val_norm_arq != val_norm_site) and not (
                    (val_arq.strip().lower() == 'não informado' and val_site.strip().lower() == 'não informado')
                ):
                    status = 'Divergente'
        elif row['_merge'] == 'left_only':
            registro_arq = df_arquivo_idx.loc[chave_tuple] if chave_tuple in df_arquivo_idx.index else None
            for campo, campo_arq, campo_site, campo_norm_arq, campo_norm_site in campos_validar:
                val_arq = get_val_from_registro(registro_arq, campo, df_arquivo, 'arquivo')
                linha[f'{campo}_arquivo'] = val_arq
                linha[f'{campo}_site'] = 'Não informado'
            status = 'Divergente'
        elif row['_merge'] == 'right_only':
            registro_site = df_site_idx.loc[chave_tuple] if chave_tuple in df_site_idx.index else None
            for campo, campo_arq, campo_site, campo_norm_arq, campo_norm_site in campos_validar:
                linha[f'{campo}_arquivo'] = 'Não informado'
                val_site = get_val_from_registro(registro_site, campo, df_site, 'site')
                linha[f'{campo}_site'] = val_site
            status = 'Divergente'
        linha['status'] = status
        linha['origem_info'] = origem_info
        linhas.append(linha)
    df_validacao = pd.DataFrame(linhas)

    # Marcar horários para log
    data_validacao = datetime.now().strftime("%d/%m/%Y")
    hora_fim = datetime.now().strftime("%H:%M")

    # Salva validação simplificada
    pasta_saida = os.path.join('data', 'validacao')
    os.makedirs(pasta_saida, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    nome_arquivo_original = os.path.splitext(os.path.basename(arquivo))[0]
    nome_arquivo_saida = f"{timestamp}_validacao_{nome_arquivo_original}.xlsx"
    caminho_saida = os.path.join(pasta_saida, nome_arquivo_saida)
    df_validacao.to_excel(caminho_saida, index=False)
    print(f"\n📅 Data de validacao: {data_validacao}")
    print(f"⏰ Hora de início: {hora_inicio}")
    print(f"⏰ Hora de fim: {hora_fim}")
    print("\n🏁 Validação concluída com sucesso.")
    print(f"\nArquivo de validação salvo em: {caminho_saida}")

