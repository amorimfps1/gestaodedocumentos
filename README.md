# 📁 Sistema de Gestão Documental

> Solução web moderna, centralizada e intuitiva para armazenamento, organização, consulta, categorização e anotações em documentos digitais.

---

## 📖 Sobre o Projeto

O **Sistema de Gestão Documental** é uma aplicação web desenvolvida para simplificar e agilizar o fluxo de armazenamento e controle de arquivos e documentos em equipes e organizações. Com uma interface de página única (*Single-Page Application* - SPA), o sistema oferece uma experiência fluida para upload de arquivos, categorização por tipo, consulta com filtros em tempo real, visualização/download de anexos e histórico de anotações colaborativas.

Além da interface web responsiva, o sistema conta com uma **API REST completa** acompanhada de documentação interativa via **Swagger (OpenAPI)** integrada com **Flask-RESTX**.

> ⚠️ **Aviso de Protótipo / MVP**: Este projeto é um protótipo funcional / Produto Mínimo Viável (MVP). Desenvolvido para validação de fluxo e arquitetura, recomenda-se a inclusão de camadas adicionais de autenticação/autorização (JWT, RBAC), criptografia em repouso e conformidade com a LGPD antes de implantação em ambientes corporativos de produção.

---

## ✨ Funcionalidades

- 📤 **Upload e Categorização de Documentos**:
  - Suporte aos formatos **PDF**, **JPG** e **PNG**.
  - Validação de integridade e limite de tamanho de até **16 MB** por arquivo.
  - Categorização por tipo de documento (`geral`, `contrato`, `procuração`, `petição`, `certidão`, `outro`).
  - Geração de nomes únicos no disco através de identificadores UUID (`uuid4`) e higienização via `secure_filename`, impedindo sobrescritas acidentais.
- 📊 **Painel de Métricas (Dashboard)**:
  - Contadores rápidos com total de documentos, distribuição por formato (PDF, imagens) e total de armazenamento utilizado em bytes.
- 📋 **Listagem, Busca e Filtros**:
  - Modos de visualização alternáveis entre **Lista** e **Grade**.
  - Filtro rápido por tipo de arquivo (Todos, PDF, JPG, PNG).
  - Campo de busca instantânea filtrando por título e descrição.
  - Ordenação automática decrescente por data de envio.
- 👁️ **Visualização e Download**:
  - Acesso direto aos arquivos salvos através de endpoint dedicado (`/uploads/<nome_arquivo>`).
- 💬 **Anotações e Comentários**:
  - Registro de observações, pareceres e anotações atreladas diretamente a cada documento.
  - Histórico cronológico decrescente com carimbo de data e hora.
- 🗑️ **Exclusão Segura e Limpeza Física**:
  - Modal de confirmação para prevenir exclusões acidentais.
  - Exclusão do registro no banco com deleção simultânea do arquivo físico correspondente no disco.
  - Exclusão em cascata relacional dos comentários atrelados.
- 📚 **Documentação Interativa Swagger**:
  - Interface Swagger UI disponível para consulta dos esquemas, rotas, payloads e realização de testes de requisições diretamente pelo navegador.

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: [Python 3.8+](https://www.python.org/)
- **Microframework Web**: [Flask 3.x](https://flask.palletsprojects.com/)
- **API REST & Swagger**: [Flask-RESTX](https://flask-restx.readthedocs.io/) (Swagger UI / OpenAPI)
- **Banco de Dados**: [SQLite3](https://www.sqlite.org/) (com integridade referencial via Foreign Keys ativadas, índices e context manager)
- **Frontend**: HTML5 semântico, CSS3 moderno (design responsivo com variáveis CSS e componentes flexíveis) e Vanilla JavaScript (Fetch API assíncrona)
- **Servidor Web**: Servidor embutido Werkzeug / Flask

---

## 🗄️ Banco de Dados e Modelagem

O sistema utiliza o **SQLite3** (`app.db`), configurado com foco em consistência relacional e desempenho.

### Melhorias e Ajustes Implementados no DB

1. **Classificação por Tipo de Documento**:
   - Adicionada a coluna `tipo` na tabela `documentos`, permitindo categorizar cada arquivo (ex: `contrato`, `procuração`, `certidão`, `geral`).
2. **Controle Físico e Métricas de Armazenamento**:
   - Registro de `caminho_arquivo` e `tamanho_bytes` diretamente na tabela `documentos`, viabilizando o cálculo exato do espaço consumido e garantindo a localização física do arquivo para remoção segura.
3. **Integridade Referencial com Chaves Estrangeiras (`PRAGMA foreign_keys = ON`)**:
   - No SQLite, chaves estrangeiras são desativadas por padrão. A integridade referencial foi ativada explicitamente tanto no momento da criação das tabelas (`init_db`) quanto em cada conexão aberta pela aplicação (`get_db_connection`).
4. **Deleção em Cascata (`ON DELETE CASCADE`)**:
   - A tabela `comentarios` possui a restrição `FOREIGN KEY (documento_id) REFERENCES documentos(id) ON DELETE CASCADE`. Ao excluir um documento, todos os comentários relacionados a ele são excluídos automaticamente, evitando registros órfãos.
5. **Índice de Desempenho (`idx_comentarios_documento`)**:
   - Criação do índice `idx_comentarios_documento` na coluna `documento_id` da tabela `comentarios`, otimizando leituras e agregações de comentários por documento.
6. **Gerenciador de Contexto (`get_db_connection`)**:
   - Implementado com `@contextmanager` do Python para garantir abertura, configuração de `row_factory = sqlite3.Row`, ativação de PRAGMA e encerramento seguro de conexões, mesmo em casos de exceção.

### Estrutura das Tabelas (DDL)

```sql
-- Tabela de Documentos
CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    tipo TEXT DEFAULT 'geral',
    nome_arquivo TEXT NOT NULL,
    caminho_arquivo TEXT NOT NULL,
    tamanho_bytes INTEGER,
    data_upload DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Comentários / Anotações
CREATE TABLE IF NOT EXISTS comentarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL,
    texto TEXT NOT NULL,
    data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documentos(id) ON DELETE CASCADE
);

-- Índice de Otimização
CREATE INDEX IF NOT EXISTS idx_comentarios_documento 
ON comentarios(documento_id);
```

---

## 📖 Documentação da API com Swagger

A API foi padronizada utilizando a biblioteca **Flask-RESTX**, que gera automaticamente a documentação OpenAPI e fornece a interface interativa do **Swagger UI**.

### Como Acessar o Swagger UI

Com a aplicação em execução, acesse pelo navegador:

```
http://localhost:5000/docs
```
*(ou `http://127.0.0.1:5000/docs`)*

### Recursos do Swagger

- **Exploração Interativa ("Try it out")**: Teste requisições `GET`, `POST` e `DELETE` diretamente no navegador.
- **Upload via Multipart**: O Swagger está configurado com um parser para upload de arquivos (`multipart/form-data`), permitindo enviar o arquivo físico junto com título e descrição direto pela interface de teste.
- **Modelos de Dados (DTO / Schemas)**:
  - `Documento`: Estrutura de retorno dos dados de um documento.
  - `ComentarioInput`: Schema de entrada para novos comentários (`{"texto": "..."}`).
  - `Comentario`: Estrutura de dados de comentários retornados.
  - `MensagemSucesso` e `MensagemErro`: Respostas padrão de confirmação ou erro da API.
- **Códigos de Resposta Documentados**: Demonstração de retornos `200 OK`, `201 Created`, `400 Bad Request` e `404 Not Found`.

---

## 📋 Pré-requisitos

- **Python 3.8** ou superior instalado na máquina.
- Gerenciador de pacotes **pip** atualizado.
- Navegador web moderno (Chrome, Edge, Firefox, Safari).

---

## 🚀 Instalação e Execução

### 1. Clonar ou Acessar a Pasta do Projeto

Navegue até o diretório onde o projeto está localizado:

```bash
cd sistemadegestaodedocumentos
```

### 2. Criar e Ativar o Ambiente Virtual

- **No Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

- **No Windows (Prompt de Comando - CMD):**
  ```cmd
  python -m venv venv
  .\venv\Scripts\activate.bat
  ```

- **No Linux / macOS (Bash / Zsh):**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar as Dependências

Instale todos os pacotes necessários através do arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

As dependências principais incluem:
- `Flask`
- `flask-restx`
- `Werkzeug`

### 4. Executar a Aplicação

Inicie o servidor localmente:

```bash
python app.py
```

Durante a inicialização, o sistema realiza automaticamente:
1. A verificação e criação da pasta `uploads/` se ela não existir.
2. A inicialização do banco de dados SQLite (`app.db`) e de suas tabelas e índices via `init_db()`.

### 5. Acessar a Aplicação

- **Interface Web Principal (SPA)**:
  ```
  http://localhost:5000/
  ```

- **Documentação Interativa Swagger**:
  ```
  http://localhost:5000/docs
  ```

---

## 📁 Estrutura do Projeto

```text
sistemadegestaodedocumentos/
├── app.py                 # Aplicação Flask, Blueprint Flask-RESTX e controladores REST
├── database.py            # Configuração, inicialização DDL e conexão com SQLite
├── requirements.txt       # Dependências do projeto (Flask, flask-restx, Werkzeug, etc.)
├── .gitignore             # Arquivos e pastas ignorados no controle de versão
├── README.md              # Documentação completa do projeto
├── templates/
│   └── index.html         # Interface SPA completa (HTML5, CSS3 e JavaScript)
└── uploads/               # Diretório onde os arquivos enviados são salvos fisicamente
```

---

## 🔌 Endpoints da API REST

Todas as rotas da API estão organizadas sob o namespace `/api/documentos`:

| Método | Rota | Descrição | Parâmetros / Corpo | Código Sucesso |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Interface principal do sistema (SPA) | Nenhum | `200 OK` |
| `GET` | `/docs` | Documentação interativa Swagger UI | Nenhum | `200 OK` |
| `GET` | `/api/documentos` | Retorna a listagem de todos os documentos | Nenhum | `200 OK` |
| `POST` | `/api/documentos` | Realiza o upload de um novo documento | `multipart/form-data`<br>• `arquivo`: Arquivo (PDF, JPG, PNG)<br>• `titulo`: String (obrigatório)<br>• `descricao`: String (opcional) | `201 Created` |
| `GET` | `/api/documentos/<id>` | Retorna os detalhes de um documento específico | Parâmetro de rota: `id` (int) | `200 OK` |
| `DELETE` | `/api/documentos/<id>` | Deleta o documento, arquivo no disco e comentários associados | Parâmetro de rota: `id` (int) | `200 OK` |
| `GET` | `/uploads/<nome_arquivo>` | Serve o arquivo físico para visualização ou download | Parâmetro de rota: `nome_arquivo` (string) | `200 OK` |
| `GET` | `/api/documentos/<id>/comentarios` | Lista os comentários de um documento | Parâmetro de rota: `id` (int) | `200 OK` |
| `POST` | `/api/documentos/<id>/comentarios` | Adiciona um novo comentário ao documento | `application/json`<br>`{ "texto": "Texto do comentário" }` | `201 Created` |

### Tratamento e Códigos de Status HTTP

- `200 OK`: Requisição processada com sucesso.
- `201 Created`: Recurso criado com sucesso (upload ou comentário).
- `400 Bad Request`: Dados inválidos, parâmetros ausentes ou formato de arquivo não suportado.
- `404 Not Found`: Documento ou recurso solicitado não encontrado.
- `413 Payload Too Large`: Arquivo excede o limite máximo permitido de 16 MB.
- `500 Internal Server Error`: Erro inesperado durante o processamento no servidor.

---

## 📄 Licença

Este projeto está distribuído sob a licença [MIT](https://opensource.org/licenses/MIT).
