import os
import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime

# Funções de normalização (copiadas do validacaoqtd.py)
def normalize_nome(nome, estado=None):
    if not isinstance(nome, str):
        return ''
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

# Função para gerar log detalhado de divergências
def gerar_log_validacao(df_arquivo, df_site, caminho_log):
    chaves = ['estado', 'municipio_norm', 'tipo', 'cns_norm']
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

    def tipo_divergencia(row):
        if row['_merge'] == 'left_only':
            return 'Só no arquivo'
        elif row['_merge'] == 'right_only':
            return 'Só no site'
        else:
            diffs = []
            for campo in ['cartorio', 'cns']:
                val_arq = str(row.get(f'{campo}_arquivo', '')).strip()
                val_site = str(row.get(f'{campo}_site', '')).strip()
                if val_arq and val_site and val_arq != val_site:
                    diffs.append(campo)
            return 'Divergente: ' + ', '.join(diffs) if diffs else 'OK'
    df_merge['motivo'] = df_merge.apply(tipo_divergencia, axis=1)

    def tipo_div_final(row):
        tipos = set()
        if pd.notnull(row.get('tipo')):
            tipos.add(str(row['tipo']).lower())
        if pd.notnull(row.get('tipo_site')):
            tipos.add(str(row['tipo_site']).lower())
        if not tipos:
            return ''
        if len(tipos) == 1:
            return list(tipos)[0]
        return ' e '.join(sorted(tipos))
    df_merge['tipo_divergencia_final'] = df_merge.apply(tipo_div_final, axis=1)

    colunas_arquivo = ['estado', 'municipio', 'tipo', 'cartorio', 'cns']
    colunas_site = ['estado_site', 'municipio_site', 'tipo_site', 'cartorio_site', 'cns_site']
    colunas_log = colunas_arquivo + colunas_site + ['motivo', 'tipo_divergencia_final']

    for col in colunas_arquivo:
        if col not in df_merge:
            df_merge[col] = np.nan
    for col in colunas_site:
        if col not in df_merge:
            df_merge[col] = np.nan

    df_merge['estado_site'] = df_merge['estado'] if df_merge['origem_site'].notnull().any() else np.nan
    df_merge['municipio_site'] = df_merge['municipio_site'] if 'municipio_site' in df_merge else df_merge['municipio_norm']
    df_merge['tipo_site'] = df_merge['tipo_site'] if 'tipo_site' in df_merge else df_merge['tipo']
    df_merge['cartorio_site'] = df_merge['cartorio_site'] if 'cartorio_site' in df_merge else df_merge['cartorio']
    df_merge['cns_site'] = df_merge['cns_site'] if 'cns_site' in df_merge else df_merge['cns']

    df_merge[colunas_log].to_excel(caminho_log, index=False)
    print(f"Relatório detalhado de divergências salvo em: {caminho_log}")

if __name__ == "__main__":
    print("Informe o caminho do arquivo CSV/XLSX gerado para comparar:")
    arquivo = input("Arquivo: ").strip()
    if not arquivo:
        print("Arquivo não informado. Saindo.")
        exit()

    if arquivo.endswith('.csv'):
        df = pd.read_csv(arquivo)
    elif arquivo.endswith('.xlsx'):
        df = pd.read_excel(arquivo)
    else:
        print("Arquivo deve ser .csv ou .xlsx")
        exit()

    def normalizar_nome_coluna(nome):
        nome = unicodedata.normalize('NFKD', str(nome))
        nome = ''.join([c for c in nome if not unicodedata.combining(c)])
        nome = nome.lower().replace(' ', '').replace('í','i').replace('ú','u').replace('é','e').replace('á','a').replace('ã','a').replace('ç','c').replace('ô','o').replace('ó','o').replace('ê','e').replace('â','a').replace('õ','o').replace('à','a')
        return nome
    df.columns = [normalizar_nome_coluna(col) for col in df.columns]
    df['estado'] = df['estado'].str.upper()
    if 'municipio_norm' not in df.columns:
        df['municipio_norm'] = df['municipio'].apply(lambda x: normalize_nome(x))
    if 'cns_norm' not in df.columns:
        df['cns_norm'] = df['cns'].apply(lambda x: normalize_cns(x))

    print("Informe o caminho do arquivo de dados do site (CSV/XLSX):")
    arquivo_site = input("Arquivo site: ").strip()
    if not arquivo_site:
        print("Arquivo do site não informado. Saindo.")
        exit()
    if arquivo_site.endswith('.csv'):
        df_site = pd.read_csv(arquivo_site)
    elif arquivo_site.endswith('.xlsx'):
        df_site = pd.read_excel(arquivo_site)
    else:
        print("Arquivo do site deve ser .csv ou .xlsx")
        exit()
    df_site.columns = [normalizar_nome_coluna(col) for col in df_site.columns]
    df_site['estado'] = df_site['estado'].str.upper()
    if 'municipio_norm' not in df_site.columns:
        df_site['municipio_norm'] = df_site['municipio'].apply(lambda x: normalize_nome(x))
    if 'cns_norm' not in df_site.columns:
        df_site['cns_norm'] = df_site['cns'].apply(lambda x: normalize_cns(x))

    log_dir = os.path.join('data', 'log')
    os.makedirs(log_dir, exist_ok=True)
    datahora_log = datetime.now().strftime('%Y%m%d_%H%M')
    nome_base = os.path.splitext(os.path.basename(arquivo))[0]
    nome_log = f"{datahora_log}_log_{nome_base}.xlsx"
    caminho_log = os.path.join(log_dir, nome_log)

    gerar_log_validacao(df, df_site, caminho_log)
