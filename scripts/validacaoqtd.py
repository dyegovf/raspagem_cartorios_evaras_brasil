import sys
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup

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

print("\nDigite a sigla do estado para comparar (ex: SP, RJ, DF) ou 'TODOS' para comparar todos:")
uf = input("Estado: ").strip().upper()

if uf == "TODOS":
    estados_comparar = estados
    print("\nComparando todos os estados.")
elif uf in estados:
    estados_comparar = [uf]
    print(f"\nComparando apenas o estado: {uf}")
else:
    print("Estado inválido. Saindo.")
    exit()

# Leitura do arquivo
if arquivo.endswith('.csv'):
    df = pd.read_csv(arquivo)
elif arquivo.endswith('.xlsx'):
    df = pd.read_excel(arquivo)
else:
    print("Arquivo deve ser .csv ou .xlsx")
    exit()

if uf != "TODOS":
    df = df[df['Estado'] == uf]

total_arquivo = len(df)
total_cartorios_arquivo = len(df[df['Tipo'] == 'Cartório'])
total_varas_arquivo = len(df[df['Tipo'] == 'Vara'])

print(f"\nArquivo: {arquivo}")
print(f"Total no arquivo: {total_arquivo}")
print(f"Cartórios no arquivo: {total_cartorios_arquivo}")
print(f"Varas no arquivo: {total_varas_arquivo}")

# Validação independente: conta cartórios e varas direto do HTML do site
def contar_links_site(sigla_estado):
    url_estado = f"https://cartorios.info/cartorios-{sigla_estado.lower()}.html"
    response = requests.get(url_estado)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if f"cartorios-de-" in a['href']]
    total_cartorios = 0
    total_varas = 0

    for link in links:
        url_municipio = f"https://cartorios.info/{link}"
        resp = requests.get(url_municipio)
        soup_mun = BeautifulSoup(resp.content, 'html.parser')
        # Cartórios
        div_cartorios = soup_mun.find('div', id='cartorios')
        if div_cartorios:
            cartorios = div_cartorios.find_all('div', class_='row', id=True)
            total_cartorios += len(cartorios)
        # Varas
        div_varas = soup_mun.find('div', id='varas')
        if div_varas:
            varas = div_varas.find_all('div', class_='row', id=True)
            total_varas += len(varas)
    return total_cartorios, total_varas

total_cartorios_site = 0
total_varas_site = 0

for estado in estados_comparar:
    print(f"\nValidando {estado} no site (contagem independente)...")
    cartorios, varas = contar_links_site(estado)
    total_cartorios_site += cartorios
    total_varas_site += varas
    print(f"Cartórios encontrados no site ({estado}): {cartorios}")
    print(f"Varas encontradas no site ({estado}): {varas}")

total_site = total_cartorios_site + total_varas_site

print("\nContagem real do site (independente):")
print(f"Total no site: {total_site}")
print(f"Cartórios no site: {total_cartorios_site}")
print(f"Varas no site: {total_varas_site}")

print("\nDiferença (arquivo - site):")
print(f"Total: {total_arquivo - total_site}")
print(f"Cartórios: {total_cartorios_arquivo - total_cartorios_site}")
print(f"Varas: {total_varas_arquivo - total_varas_site}")