import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import unicodedata
import re

# Lista de estados brasileiros
estados = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO'
]

# Função para normalizar nomes de cidades para URL
def normalizar_cidade(nome):
    texto = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r"[']", "", texto)
    texto = re.sub(r"\s+", "-", texto)
    texto = re.sub(r"-{2,}", "-", texto)
    return texto.lower()

# Lista onde os dados serão armazenados
dados_cartorios = []

# Função para extrair links dos municípios
def extrair_links_municipios(sigla_estado):
    url_estado = f"https://cartorios.info/cartorios-{sigla_estado.lower()}.html"
    response = requests.get(url_estado)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("cartorios-de-") and href.endswith(f"-{sigla_estado.lower()}.html"):
            links.append("https://cartorios.info/" + href)
    return links

# Função para extrair dados dos cartórios de um município
def extrair_dados_municipio(url_municipio, sigla_estado):
    response = requests.get(url_municipio)
    soup = BeautifulSoup(response.content, 'html.parser')

    titulo = soup.find('h1')
    municipio = titulo.text.split(" de ")[-1].split(" no ")[0].strip() if titulo else 'Não informado'

    blocos = soup.find_all('div', class_='row')
    for bloco in blocos:
        nome_tag = bloco.find('h3')
        if not nome_tag:
            continue
        nome = nome_tag.text.strip()

        texto = bloco.get_text(separator="\n")

        status = 'Inativo' if 'Inativo' in texto else 'Ativo'

        servicos = []
        if 'Atribuições:' in texto:
            servico_bruto = texto.split('Atribuições:')[1].split('\n')[0]
            servicos = [s.strip('• ').strip() for s in servico_bruto.split('•') if s.strip()]
        servicos_str = ', '.join(servicos) if servicos else 'Não informado'

        endereco = ''
        if 'Endereço:' in texto:
            endereco = texto.split('Endereço:')[1].split('\n')[0].strip()

        telefone = ''
        if 'Telefone(s):' in texto:
            telefone = texto.split('Telefone(s):')[1].split('\n')[0].strip()

        horario = ''
        if 'Horário de funcionamento:' in texto:
            horario = texto.split('Horário de funcionamento:')[1].split('\n')[0].strip()

        cns = ''
        if 'CNS:' in texto:
            cns = texto.split('CNS:')[1].split('\n')[0].strip()

        email_tag = bloco.find('span', class_='__cf_email__')
        email = email_tag.get('data-cfemail') if email_tag else 'Não informado'

        dados_cartorios.append({
            'Estado': sigla_estado,
            'Município': municipio,
            'Cartório': nome,
            'Serviços': servicos_str,
            'Status do Cartório': status,
            'Endereço': endereco,
            'Telefone': telefone,
            'Email (ofuscado)': email,
            'Horário': horario,
            'CNS': cns
        })

# Loop principal
for estado in estados:
    print(f"🔍 Buscando municípios de {estado}...")
    try:
        links_municipios = extrair_links_municipios(estado)
        for url_municipio in links_municipios:
            print(f"   ➤ Extraindo dados de {url_municipio}")
            extrair_dados_municipio(url_municipio, estado)
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Erro ao processar {estado}: {e}")

# Criar DataFrame e salvar como planilha
df = pd.DataFrame(dados_cartorios)
df.to_excel("cartorios_brasil_completo.xlsx", index=False)

print("✅ Raspagem concluída e planilha gerada com sucesso!")