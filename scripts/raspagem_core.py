import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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

def extrair_nome_municipio(url_municipio, sigla_estado):
    path = urlparse(url_municipio).path
    nome_raw = path.split("cartorios-de-")[-1].split(f"-{sigla_estado.lower()}")[0]
    nome_formatado = ' '.join([parte.capitalize() for parte in nome_raw.split('-')])
    return nome_formatado

def extrair_dados_municipio(url_municipio, sigla_estado):
    response = requests.get(url_municipio)
    soup = BeautifulSoup(response.content, 'html.parser')
    municipio = extrair_nome_municipio(url_municipio, sigla_estado)
    dados = []

    # Extrair cartórios
    container_cartorios = soup.find('div', id='cartorios')
    if container_cartorios:
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