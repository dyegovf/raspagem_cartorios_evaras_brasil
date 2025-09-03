## 🗂️ Cartórios e Varas Judiciais do Brasil — Web Scraper

Este projeto realiza a raspagem automatizada de dados públicos do site [cartorios.info](https://cartorios.info), extraindo informações detalhadas sobre todos os **cartórios extrajudiciais** e **varas judiciais** dos municípios brasileiros.

Você pode escolher:

- 📌 O tipo de unidade: Cartório, Vara ou Ambos
- 📁 O formato de saída: CSV único, XLSX único, ou arquivos separados por estado
- 🌎 O estado a ser processado: um específico ou todos os estados do Brasil

Os arquivos gerados são organizados automaticamente em subpastas dentro de `data/`, conforme suas escolhas.

---

### 📌 Funcionalidades

- ✅ Extração de dados de todos os estados e municípios do Brasil
- ✅ Captura separada de cartórios e varas judiciais
- ✅ Identificação do tipo de unidade (Cartório ou Vara)
- ✅ Filtro por tipo de unidade e estado
- ✅ Geração de arquivos em quatro formatos:
  - Um único `.csv` consolidado
  - Um único `.xlsx` consolidado
  - Um `.csv` por estado
  - Um `.xlsx` por estado
- ✅ Organização automática dos arquivos em subpastas específicas
- ✅ Correção robusta na extração do nome do município (via URL)
- ✅ Configuração segura da pasta de destino via `.env`

---

### 📄 Dados extraídos

Cada linha contém:

| Coluna             | Descrição                                                   |
| ------------------ | ----------------------------------------------------------- |
| Estado             | Sigla do estado (ex: SP, RJ, BA)                            |
| Município          | Nome do município                                           |
| Cartório           | Nome da serventia ou vara judicial                          |
| Serviços           | Lista de serviços prestados (separados por ponto e vírgula) |
| Status do Cartório | Ativo ou Inativo                                            |
| Tipo               | Cartório ou Vara                                            |

---

### ⚙️ Requisitos

- Python 3.8+
- Bibliotecas:
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `python-dotenv`

Instale com:

```bash
pip install -r requirements.txt
```

---

### 🚀 Como usar

#### 1. Configure a pasta de destino

Crie um arquivo `.env` na raiz do projeto com:

```
PASTA_CARTORIO=CAMINHO_DA_PASTA_DE_DESTINO
```

> Exemplo: `PASTA_CARTORIO=./data`

Adicione `.env` ao seu `.gitignore`:

```
.env
```

#### 2. Execute o script principal

```bash
python main.py
```

Você será guiado por três etapas:

1. Escolher o tipo de unidade: Cartório, Vara ou Ambos
2. Escolher o formato de saída: CSV único, XLSX único, ou por estado
3. Escolher o estado (somente se o formato permitir)

> Se você escolher um formato único, o script processará automaticamente todos os estados.

---

### 🧠 Observações

- O script respeita o tempo de resposta do servidor com `time.sleep(1)` entre requisições
- Os dados são públicos e extraídos apenas para fins informativos e acadêmicos
- O campo "Serviços" pode vir como "Não informado" em varas judiciais ou cartórios sem atribuições listadas
- O campo "Tipo" permite distinguir entre cartórios extrajudiciais e varas judiciais
- O nome do município é extraído diretamente da URL, garantindo precisão mesmo em casos complexos como "Rio de Janeiro"

---

### 📬 Contato

Desenvolvido por Dyegovf  
📍 Brasília, Brasil  
📧 dyegovf@gmail.com
