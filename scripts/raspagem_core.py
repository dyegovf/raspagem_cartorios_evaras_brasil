import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import unicodedata

# Função de normalização igual à da validação
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
    return ' '.join(nome.split())

def extrair_links_municipios(sigla_estado):
    url_estado = f"https://cartorios.info/cartorios-{sigla_estado.lower()}.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    response = requests.get(url_estado, headers=headers)
    time.sleep(0.2)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("cartorios-de-") and href.endswith(f"-{sigla_estado.lower()}.html"):
            links.append("https://cartorios.info/" + href)
    return links

def extrair_nome_municipio(url_municipio, sigla_estado):
    path = urlparse(url_municipio).path
    nome_raw = path.split("cartorios-de-")[-1].split(f"-{sigla_estado.lower()}")[0]
    nome_formatado = ' '.join([parte.capitalize() for parte in nome_raw.split('-')])
    return nome_formatado

def extrair_dados_municipio(url_municipio, sigla_estado):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    response = requests.get(url_municipio, headers=headers)
    time.sleep(1)
    soup = BeautifulSoup(response.content, 'html.parser')
    municipio = extrair_nome_municipio(url_municipio, sigla_estado)
    dados = []

    # Extrair cartórios
    container_cartorios = soup.find('div', id='cartorios')
    if container_cartorios:
        # Lógica híbrida: prioriza o id do container, mas faz fallback para breadcrumb ou <title> se o nome extraído for só uma palavra
        municipio_hibrido = None
        container_municipio = soup.find('div', class_='cidades')
        if container_municipio and container_municipio.has_attr('id'):
            municipio_id = container_municipio['id']
            partes = [parte for parte in municipio_id.split('-') if parte]
            municipio_nome = ' '.join([parte.capitalize() for parte in partes])
            # Se o nome extraído for só uma palavra, faz o fallback
            if len(partes) == 1:
                municipio_hibrido = None
            else:
                municipio_hibrido = municipio_nome
        if not municipio_hibrido:
            breadcrumb = soup.select_one('ul.breadcrumbs li:last-child span[itemprop="name"]')
            if breadcrumb:
                municipio_hibrido = breadcrumb.text.strip()
            else:
                titulo_tag = soup.find('title')
                if titulo_tag:
                    import re
                    m = re.search(r'de (.+?)/' + sigla_estado, titulo_tag.text)
                    if m:
                        municipio_hibrido = m.group(1).strip()
                    else:
                        municipio_hibrido = titulo_tag.text.strip()
                else:
                    municipio_hibrido = 'Não identificado'
        # Use o nome formatado com espaços, igual ao site
        municipio = municipio_hibrido if municipio_hibrido else municipio
    blocos = container_cartorios.find_all('div', class_='row')
    for bloco in blocos:
            nome_tag = bloco.find('h3')
            if not nome_tag:
                continue
            nome = nome_tag.text.strip()
            status = "Ativo"
            status_tag = bloco.find('strong', string=lambda s: s and "Situação do Cartório" in s)
            if status_tag:
                status_span = status_tag.find_next('span')
                if status_span:
                    status = status_span.text.strip()
                else:
                    status_b = status_tag.find_next('b')
                    if status_b:
                        status = status_b.text.strip()

            escrivao = "Não informado"
            escrivao_tag = bloco.find('strong', string=lambda s: s and "Escrivão" in s and "Titular" in s)
            if escrivao_tag:
                escrivao = escrivao_tag.next_sibling
                if escrivao:
                    escrivao = escrivao.strip()
                    escrivao = escrivao.split("desde")[0].strip()

            data_criacao = "Não informado"
            data_tag = bloco.find('strong', string=lambda s: s and "Data da Criação" in s)
            if data_tag:
                data_criacao = data_tag.next_sibling
                if data_criacao:
                    data_criacao = data_criacao.strip()

            cns = "Não informado"
            cns_tag = bloco.find('strong', string=lambda s: s and "CNS" in s)
            if cns_tag:
                cns = cns_tag.next_sibling
                if cns:
                    cns = cns.strip()

            servicos = "Não informado"
            atrib_tag = bloco.find('strong', string=lambda s: s and "Atribuições" in s)
            if atrib_tag:
                servicos = atrib_tag.next_sibling
                if servicos:
                    servicos = servicos.replace("•", ";").replace("&bull;", ";").strip(" ;\n\t")

            dados.append({
                'Estado': sigla_estado,
                'Município': municipio,
                'Cartório': nome,
                'Serviços': servicos,
                'Status do Cartório': status,
                'Tipo': 'Cartório',
                'Escrivão Titular': escrivao,
                'Data de Criação': data_criacao,
                'CNS': cns
            })

    # Extrair varas judiciais
    container_varas = soup.find('div', id='varas')
    if container_varas:
        blocos = container_varas.find_all('div', class_='row')
        for bloco in blocos:
            nome_tag = bloco.find('h3')
            if not nome_tag:
                continue
            nome = nome_tag.text.strip()
            status = "Ativo"
            status_tag = bloco.find('strong', string=lambda s: s and "Situação da Vara" in s)
            if status_tag:
                status_span = status_tag.find_next('span')
                if status_span:
                    status = status_span.text.strip()
                else:
                    status_b = status_tag.find_next('b')
                    if status_b:
                        status = status_b.text.strip()

            escrivao = "Não informado"
            escrivao_tag = bloco.find('strong', string=lambda s: s and "Escrivão" in s and "Titular" in s)
            if escrivao_tag:
                escrivao = escrivao_tag.next_sibling
                if escrivao:
                    escrivao = escrivao.strip()
                    escrivao = escrivao.split("desde")[0].strip()

            data_criacao = "Não informado"
            data_tag = bloco.find('strong', string=lambda s: s and "Data da Criação" in s)
            if data_tag:
                data_criacao = data_tag.next_sibling
                if data_criacao:
                    data_criacao = data_criacao.strip()

            cns = "Não informado"
            cns_tag = bloco.find('strong', string=lambda s: s and "CNS" in s)
            if cns_tag:
                cns = cns_tag.next_sibling
                if cns:
                    cns = cns.strip()

            servicos = "Não informado"
            atrib_tag = bloco.find('strong', string=lambda s: s and "Atribuições" in s)
            if atrib_tag:
                servicos = atrib_tag.next_sibling
                if servicos:
                    servicos = servicos.replace("•", ";").replace("&bull;", ";").strip(" ;\n\t")

            dados.append({
                'Estado': sigla_estado,
                'Município': municipio,
                'Cartório': nome,
                'Serviços': servicos,
                'Status do Cartório': status,
                'Tipo': 'Vara',
                'Escrivão Titular': escrivao,
                'Data de Criação': data_criacao,
                'CNS': cns
            })

    return dados