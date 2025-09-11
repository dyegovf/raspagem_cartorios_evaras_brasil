## 🗂️ Cartórios e Varas Judiciais do Brasil — Web Scraper

Este projeto realiza a raspagem automatizada de dados públicos do site [cartorios.info](https://cartorios.info), extraindo informações detalhadas sobre todos os **cartórios extrajudiciais** e **varas judiciais** dos municípios brasileiros.

### Principais recursos

- 📌 Escolha do tipo de unidade: Cartório, Vara ou Ambos
- 📁 Escolha do formato de saída: CSV único, XLSX único, ou arquivos separados por estado
- 🌎 Escolha do(s) estado(s) a ser(em) processado(s): um específico ou todos os estados do Brasil
- 🗂️ Organização automática dos arquivos em subpastas dentro de `data/`, conforme suas escolhas
- 🏷️ Extração robusta do nome do município (breadcrumb, h1 ou URL)
- 🛡️ Preenchimento automático de campos ausentes com "Não informado"
- 🧪 Script de validação para comparar arquivos gerados com dados do site

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
| Escrivão Titular   | Nome do escrivão titular ou "Não informado"                 |
| Data de Criação    | Data de criação da serventia ou "Não informado"             |
| CNS                | Código Nacional de Serventia ou "Não informado"             |

---

### ⚙️ Requisitos

- Python 3.8+
- Bibliotecas:

  - `requests`
  - `beautifulsoup4`

  ## Instalação

  1. Clone o repositório:


      ```bash
      git clone https://github.com/dyegovf/raspagem_cartorios_evaras_brasil.git
      ```

  2. Crie e ative o ambiente virtual:


      ```bash
      python -m venv .venv
      # Ative no Windows:
      .venv\Scripts\activate
      # Ative no Linux/Mac:
      source .venv/bin/activate
      ```

  3. Instale as dependências:


      ```bash
      pip install -r requeriments.txt
      ```

  4. (Opcional) Instale o pacote localmente para desenvolvimento:


      ```bash
      python setup.py develop
      # ou
      python setup.py install
      ```

      > **Atenção:**
      > Se receber erro relacionado ao `setuptools`, siga estes passos:
      > 1. Certifique-se de ativar o ambiente virtual antes de rodar o setup.py.
      > 2. No VS Code, selecione o interpretador Python da `.venv` (Ctrl+Shift+P > Python: Select Interpreter).
      > 3. Instale o setuptools no ambiente virtual:
      >    ```bash
      >    pip install setuptools
      >    ```
      > 4. Feche e reabra o terminal integrado do VS Code após trocar o interpretador.

  5. Configure o arquivo `.env` conforme o exemplo fornecido.

  6. Execute os scripts conforme instruções abaixo.
     python main.py

```

Você será guiado por três etapas:

1. Escolher o tipo de unidade: Cartório, Vara ou Ambos
2. Escolher o formato de saída: CSV único, XLSX único, ou por estado
3. Escolher o(s) estado(s) (somente se o formato permitir)

> Se você escolher um formato único, o script processará automaticamente todos os estados.

---

### 🧠 Observações

- O script respeita o tempo de resposta do servidor com `time.sleep(0.2)` ou `time.sleep(0.3)` entre requisições
- Os dados são públicos e extraídos apenas para fins informativos e acadêmicos
- Todos os campos podem vir como "Não informado" caso não estejam disponíveis no site
- O campo "Tipo" permite distinguir entre cartórios extrajudiciais e varas judiciais
- O nome do município é extraído de forma robusta (breadcrumb, h1 ou URL)
- O script de validação compara os arquivos gerados com os dados do site e destaca divergências

---

### 📬 Contato

Desenvolvido por Dyegovf
📍 Brasília, Brasil
📧 dyegovf@gmail.com
```
