Este projeto realiza a raspagem automatizada de dados públicos do site [cartorios.info](https://cartorios.info), extraindo informações detalhadas sobre todos os **cartórios extrajudiciais** e **varas judiciais** dos municípios brasileiros.

Você pode escolher:

- 📌 O tipo de unidade: apenas cartórios, apenas varas ou ambos
- 📁 O formato de saída: CSV único ou XLSX por estado
- 🌎 O estado a ser processado: um específico ou todos de uma vez

Os arquivos gerados são organizados automaticamente em subpastas dentro de `data/`, conforme suas escolhas.

---

### 📌 Funcionalidades

- ✅ Extração de dados de todos os estados e municípios do Brasil
- ✅ Captura separada de cartórios e varas judiciais
- ✅ Identificação do tipo de unidade (Cartório ou Vara)
- ✅ Filtro por tipo de unidade e estado
- ✅ Geração de arquivos em dois formatos:
  - Um único `.csv` consolidado por estado
  - Um `.xlsx` por estado
- ✅ Organização automática dos arquivos em subpastas específicas
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

> Substitua `CAMINHO_DA_PASTA_DE_DESTINO` pelo caminho desejado no seu sistema.  
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
2. Escolher o formato de saída: CSV único ou XLSX por estado
3. Escolher o estado: sigla (ex: SP) ou "TODOS" para o Brasil inteiro

Os arquivos serão salvos automaticamente em subpastas como:

```
data/
├── cartorio_csv_unico/
├── vara_xls_porArquivo/
├── ambos_csv_unico/
...
```

---

### 🧠 Observações

- O script respeita o tempo de resposta do servidor com `time.sleep(1)` entre requisições
- Os dados são públicos e extraídos apenas para fins informativos e acadêmicos
- O campo "Serviços" pode vir como "Não informado" em varas judiciais ou cartórios sem atribuições listadas
- O campo "Tipo" permite distinguir entre cartórios extrajudiciais e varas judiciais

---

### 📬 Contato

Desenvolvido por Dyego  
📍 Brasília, Brasil  
📧 dyego@[seu-email].com

---
