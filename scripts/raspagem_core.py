import requests
from bs4 import BeautifulSoup

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

def extrair_dados_municipio(url_municipio, sigla_estado):
    response = requests.get(url_municipio)
    soup = BeautifulSoup(response.content, 'html.parser')

    titulo = soup.find('h1')
    municipio = titulo.text.split(" de ")[-1].split(" no ")[0].strip() if titulo else 'Não informado'

    dados = []
    nomes_incluidos = set()

    # Extrair cartórios
    container_cartorios = soup.find('div', id='cartorios')
    if container_cartorios:
        blocos = container_cartorios.find_all('div', class_='row')
        for bloco in blocos:
            nome_tag = bloco.find('h3')
            if not nome_tag:
                continue

            nome = nome_tag.text.strip()
            if nome in nomes_incluidos:
                continue
            nomes_incluidos.add(nome)

            texto = bloco.get_text(separator="\n")
            status = 'Inativo' if 'Inativo' in texto else 'Ativo'

            servicos = []
            atrib_tag = bloco.find(string=lambda text: text and 'Atribuições:' in text)
            if atrib_tag:
                parent = atrib_tag.parent
                siblings = parent.find_next_siblings(string=True)
                for s in siblings:
                    if '•' in s:
                        servicos.extend([item.strip('• ').strip() for item in s.split('•') if item.strip()])
                        break
            servicos_str = '; '.join(servicos) if servicos else 'Não informado'

            dados.append({
                'Estado': sigla_estado,
                'Município': municipio,
                'Cartório': nome,
                'Serviços': servicos_str,
                'Status do Cartório': status,
                'Tipo': 'Cartório'
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
            if nome in nomes_incluidos:
                continue
            nomes_incluidos.add(nome)

            texto = bloco.get_text(separator="\n")
            status = 'Inativo' if 'Inativo' in texto else 'Ativo'

            dados.append({
                'Estado': sigla_estado,
                'Município': municipio,
                'Cartório': nome,
                'Serviços': 'Não informado',
                'Status do Cartório': status,
                'Tipo': 'Vara'
            })

    return dados