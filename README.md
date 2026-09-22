# Sistema de Gestão Documental

Solução web para armazenamento, categorização, gerenciamento e consulta de documentos digitais, integrando interface de usuário em página única (SPA) e API REST documentada via OpenAPI/Swagger.

---

## 🌐 Acesso Online (Deploy Público & Documentação)

| Recurso | Link de Acesso | Descrição |
| :--- | :--- | :--- |
| **Aplicação Web (Produção)** | [gestao-documental.onrender.com](https://gestao-documental.onrender.com) | Interface SPA para upload, consulta e anotações |
| **Swagger UI (API Docs)** | [gestao-documental.onrender.com/docs](https://gestao-documental.onrender.com/docs) | Documentação interativa OpenAPI dos endpoints REST |
| **Repositório GitHub** | [https://github.com/amorimfps1/gestaodedocumentos](https://github.com/amorimfps1/gestaodedocumentos) | Código-fonte versionado e documentado |

---

## Sumário

- [Acesso Online (Deploy Público)](#-acesso-online-deploy-público--documentação)
- [Visão Geral](#visão-geral)
- [Arquitetura e Tecnologias](#arquitetura-e-tecnologias)
- [Funcionalidades](#funcionalidades)
- [Modelagem do Banco de Dados](#modelagem-do-banco-de-dados)
- [Documentação da API REST](#documentação-da-api-rest)
- [Instalação e Execução Local](#instalação-e-execução-local)
- [Instruções de Deploy no Render](#instruções-de-deploy-no-render)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Recomendações para Produção e Segurança](#recomendações-para-produção-e-segurança)
- [Licença](#licença)

---

## Visão Geral

O Sistema de Gestão Documental é uma aplicação desenvolvida para centralizar e organizar o fluxo operacional de arquivos e registros em equipes e departamentos. Com arquitetura baseada em Single-Page Application (SPA), a aplicação proporciona uma experiência ágil para upload de documentos, categorização temática, busca com filtragem instantânea em memória, visualização/download de anexos e gestão de anotações colaborativas.

Além da interface web responsiva, o sistema disponibiliza uma API REST padronizada, documentada interativamente através de Swagger UI via Flask-RESTX.

---

## Arquitetura e Tecnologias

- Backend: Python 3.8+ / Python 3.11+
- Microframework Web: Flask 3.x
- Servidor WSGI de Produção: Gunicorn
- Padronização e Documentação de API: Flask-RESTX (OpenAPI / Swagger UI)
- Banco de Dados Relacional: SQLite3 com integridade referencial habilitada (PRAGMA foreign_keys = ON)
- Frontend: HTML5 semântico, CSS3 com variáveis customizadas, Vanilla JavaScript assíncrono (Fetch API)
- Sanitização e Armazenamento Seguro: Werkzeug (`secure_filename`) e identificadores únicos `uuid4`

---

## Funcionalidades

### 1. Upload e Classificação de Arquivos
- Suporte aos formatos PDF, JPG e PNG.
- Validação estrita de extensões e limite máximo de tamanho de 16 MB por arquivo.
- Categorização pré-definida por tipo (geral, contrato, procuração, petição, certidão, outro).
- Prevenção de colisões e sobreescritas através da geração de identificadores UUID (`uuid4`) atrelados aos nomes higienizados dos arquivos.

### 2. Painel de Métricas (Dashboard)
- Contadores consolidados com total de documentos cadastrados.
- Distribuição quantitativa por tipo e formato (PDF e imagens).
- Medição e exibição do volume total de armazenamento utilizado em bytes.

### 3. Pesquisa, Filtros e Modos de Exibição
- Busca em tempo real aplicada a título, descrição e tipo de documento.
- Filtros rápidos por formato de arquivo (Todos, PDF, JPG, PNG).
- Filtros rápidos por tipo/categoria de documento (Todos, Geral, Contrato, Procuração, Petição, Certidão, Outro).
- Filtragem combinada (ex: exibir apenas contratos em formato PDF) com opção de limpeza rápida de filtros.
- Badges visuais coloridos para identificação imediata de tipo e formato nos cards de documento.
- Alternância de visualização entre formatos de Lista e Grade (Cards).
- Ordenação cronológica decrescente automática com base na data de envio.

### 4. Gestão de Anotações e Pareceres
- Registro de comentários cronológicos vinculados a cada documento.
- Histórico completo com data e hora de inclusão.

### 5. Exclusão Segura e Limpeza Física
- Janela modal de confirmação para evitar exclusões involuntárias.
- Exclusão atômica: remove o registro do banco de dados, deleta os comentários em cascata e apaga o arquivo físico correspondente no disco.

### 6. Documentação Interativa via Swagger
- Interface gráfica Swagger UI para inspeção de esquemas, rotas, tipos de dados e teste de endpoints diretamente pelo navegador.

---

## Modelagem do Banco de Dados

A persistência relacional é gerenciada pelo SQLite3 (`app.db`), configurado com foco em consistência de dados:

1. Integridade Referencial: A diretiva `PRAGMA foreign_keys = ON` é executada explicitamente na criação das tabelas e em todas as conexões abertas pela aplicação através de um context manager (`get_db_connection`).
2. Deleção em Cascata (`ON DELETE CASCADE`): A chave estrangeira na tabela `comentarios` garante que a exclusão de um registro na tabela `documentos` propague a remoção imediata de todas as suas anotações vinculadas.
3. Indexação para Otimização: Índice dedicado `idx_comentarios_documento` na coluna `documento_id` para acelerar consultas e agrupamentos de comentários.
4. Gerenciamento Seguro de Conexões: Implementação do padrão Python `@contextmanager` para abertura, configuração de `row_factory = sqlite3.Row` e encerramento determinístico das conexões.

### Esquema Relacional (DDL)

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

-- Índice de Desempenho
CREATE INDEX IF NOT EXISTS idx_comentarios_documento 
ON comentarios(documento_id);
```

---

## Documentação da API REST

A API disponibiliza endpoints REST sob o prefixo `/api/documentos`. A interface interativa Swagger UI pode ser acessada em `/docs`.

### Tabela de Endpoints

| Método | Endpoint | Descrição | Entrada / Parâmetros | Código Sucesso |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/` | Interface web principal (SPA) | Nenhuma | 200 OK |
| GET | `/docs` | Documentação interativa Swagger UI | Nenhuma | 200 OK |
| GET | `/api/documentos` | Retorna a listagem de documentos (com filtros opcionais) | Query params opcionais:<br>- `tipo`: String (ex: `contrato`)<br>- `ext`: String (ex: `pdf`) | 200 OK |
| POST | `/api/documentos` | Realiza o upload de um novo documento | `multipart/form-data`<br>- `arquivo`: Arquivo (PDF, JPG, PNG)<br>- `titulo`: String (obrigatório)<br>- `descricao`: String (opcional)<br>- `tipo`: String (opcional, padrão `geral`) | 201 Created |
| GET | `/api/documentos/<id>` | Retorna os detalhes de um documento específico | Parâmetro de rota: `id` (int) | 200 OK |
| DELETE | `/api/documentos/<id>` | Deleta o documento, arquivo físico e comentários | Parâmetro de rota: `id` (int) | 200 OK |
| GET | `/uploads/<nome_arquivo>` | Serve o arquivo salvo para leitura ou download | Parâmetro de rota: `nome_arquivo` (string) | 200 OK |
| GET | `/api/documentos/<id>/comentarios` | Lista os comentários de um documento | Parâmetro de rota: `id` (int) | 200 OK |
| POST | `/api/documentos/<id>/comentarios` | Insere novo comentário em um documento | `application/json`<br>`{ "texto": "Texto do comentário" }` | 201 Created |

### Códigos de Status HTTP

- 200 OK: Requisição processada com êxito.
- 201 Created: Recurso cadastrado com sucesso.
- 400 Bad Request: Dados obrigatórios ausentes, extensão inválida ou carga incompatível.
- 404 Not Found: Registro ou documento não localizado.
- 413 Payload Too Large: Tamanho do arquivo excede o limite estipulado de 16 MB.
- 500 Internal Server Error: Falha interna não tratada no servidor.

---

## Instalação e Execução Local

### Pré-requisitos
- Python 3.8 ou superior instalado.
- Gerenciador de pacotes pip atualizado.

### 1. Clonar ou Acessar o Diretório do Projeto
```bash
cd sistemadegestaodedocumentos
```

### 2. Configurar o Ambiente Virtual
- No Windows (PowerShell):
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- No Windows (Prompt de Comando):
  ```cmd
  python -m venv venv
  .\venv\Scripts\activate.bat
  ```
- No Linux ou macOS (Bash/Zsh):
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o Servidor Local
- Modo de Desenvolvimento:
  ```bash
  python app.py
  ```
- Modo de Produção Local (Gunicorn em ambientes Linux/WSL):
  ```bash
  gunicorn app:app --bind 0.0.0.0:5000
  ```

### 5. Acessar a Aplicação
- Aplicação Web: `http://localhost:5000/`
- Documentação Swagger: `http://localhost:5000/docs`

---

## Instruções de Deploy no Render

O projeto está preparado para deploy no serviço de hospedagem em nuvem Render como um Web Service.

### Passo a Passo no Painel do Render

1. Crie uma conta no [Render](https://render.com/) e acerte a conexão com seu repositório Git (GitHub ou GitLab).
2. Clique em **New +** e selecione **Web Service**.
3. Selecione o repositório deste projeto.
4. Preencha as configurações fundamentais:
   - **Name**: `sistema-gestao-documental` (ou o nome de sua preferência)
   - **Language / Runtime**: `Python`
   - **Branch**: `main` (ou a branch de publicação correspondente)
   - **Region**: Selecione a região geográfica mais próxima do seu público
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app
     ```
5. Clique em **Deploy Web Service** para iniciar a compilação e publicação.

### Variáveis de Ambiente Recomendadas

Na aba **Environment** do serviço no Render:
- `PYTHON_VERSION`: `3.11.0` (ou versão correspondente do ambiente)
- `FLASK_DEBUG`: `false`

### Considerações sobre Persistência de Dados no Render

Por padrão, instâncias gratuitas em plataformas como o Render utilizam sistemas de arquivos efêmeros (*ephemeral filesystem*), o que implica que novos deploys ou reinicializações do contêiner redefinem arquivos locais gerados em tempo de execução.

Para implantações definitivas em produção, considere as seguintes práticas:
- **Armazenamento de Anexos**: Configurar um Render Persistent Disk montado no diretório `uploads/` ou integrar o backend a serviços de armazenamento em nuvem de objetos (Amazon S3, Cloudflare R2 ou Google Cloud Storage).
- **Banco de Dados**: Manter o arquivo SQLite (`app.db`) no Render Disk persistente ou migrar o acesso a dados para um banco de dados relacional gerenciado como PostgreSQL.

---

## Estrutura do Projeto

```text
sistemadegestaodedocumentos/
|-- app.py                 # Aplicação Flask, rotas web, blueprint Flask-RESTX e API
|-- database.py            # Inicialização DDL, conexão e gerenciamento de banco de dados
|-- requirements.txt       # Relação de dependências do projeto com suporte a Gunicorn
|-- .gitignore             # Arquivos e diretórios excluídos do controle de versão
|-- README.md              # Documentação técnica do projeto
|-- templates/
|   `-- index.html         # Interface SPA completa com estilos CSS e scripts embutidos
`-- uploads/               # Diretório local para gravação física dos arquivos enviados
```

---

## Recomendações para Produção e Segurança

- Autenticação e Autorização: Recomenda-se implementar autenticação via tokens (JWT) e controle de acesso baseado em papéis (RBAC) antes de disponibilizar o sistema em ambientes corporativos abertos.
- Criptografia: Assegurar tráfego exclusivo sob protocolo HTTPS/TLS e aplicar criptografia para arquivos confidenciais em repouso.
- Conformidade Regulatória: Adequar a coleta e retenção de arquivos com dados pessoais às diretrizes da LGPD (Lei Geral de Proteção de Dados).

---

## Licença

Este projeto é disponibilizado sob os termos da licença [MIT](https://opensource.org/licenses/MIT).
