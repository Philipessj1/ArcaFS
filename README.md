# ArcaFS

> A secure cloud file manager API built with Python, FastAPI, PostgreSQL, Docker, AWS S3 and DevOps-focused architecture.

O **ArcaFS (Ark File System)** é um gerenciador de arquivos em nuvem inspirado em soluções como Google Drive e Dropbox.

O projeto foi criado como portfólio para demonstrar conhecimentos práticos em desenvolvimento backend, bancos de dados relacionais, Docker, Cloud Computing, AWS, segurança, arquitetura de APIs, testes automatizados e práticas de DevOps.

## Objetivo

Construir uma aplicação completa de gerenciamento de arquivos que permita:

* cadastro e autenticação de usuários;
* upload, download e exclusão de arquivos;
* armazenamento de metadados em PostgreSQL;
* controle de acesso por usuário;
* compartilhamento temporário por links públicos;
* versionamento e restauração de arquivos;
* execução completa com Docker e Docker Compose;
* testes automatizados com banco de dados isolado;
* storage local em desenvolvimento;
* storage em AWS S3 via backend configurável;
* migração futura para AWS RDS, CloudWatch, CI/CD e infraestrutura como código.

## Tecnologias

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* SQLAlchemy
* PyJWT
* pwdlib + Argon2

### Banco de dados

* PostgreSQL 17
* Alembic
* psycopg2-binary

### Testes

* Pytest
* Starlette TestClient
* Banco PostgreSQL separado para testes
* Fixtures para isolamento de banco, autenticação e storage temporário
* Testes protegidos para sempre usarem storage local, mesmo quando o ambiente estiver configurado para S3

### Infraestrutura

* Docker
* Docker Compose
* Variáveis de ambiente com `.env`
* Container da API FastAPI
* Container do PostgreSQL
* Healthcheck do PostgreSQL
* Volume persistente para o banco
* Volume local para arquivos enviados em ambiente local

### Cloud / AWS

* AWS S3
* boto3
* IAM User com política de menor privilégio
* Bucket privado
* Upload de arquivos para S3
* Download de arquivos a partir do S3
* Exclusão de objetos no S3
* Cópia de objetos no S3 para restauração de versões
* Limpeza automática de arquivos temporários usados em downloads via S3

### Tecnologias planejadas

* React
* TypeScript
* Vite
* Tailwind CSS
* AWS RDS
* AWS EC2 ou ECS
* AWS CloudWatch
* GitHub Actions
* Terraform

## Arquitetura atual

```text
Cliente / Swagger
       │
       ▼
localhost:8000
       │
       ▼
Container FastAPI + Uvicorn
       │
       ├── JWT Authentication
       ├── SQLAlchemy ORM
       │       │
       │       ▼
       │   Container PostgreSQL
       │
       └── Storage Backend
               │
               ├── LocalStorage
               │   storage/uploads/<user_id>/
               │
               └── S3Storage
                   AWS S3 Bucket privado
```

## Arquitetura de testes

```text
Pytest
  │
  ▼
TestClient
  │
  ▼
FastAPI App
  │
  ├── Banco PostgreSQL de testes
  │       arcafs_test_db
  │
  └── Storage local temporário por teste
          tmp_path/uploads/
```

## Arquitetura planejada na AWS

```text
Frontend React
       │
       ▼
Nginx / Load Balancer
       │
       ▼
FastAPI em Docker
       │
       ├── PostgreSQL no AWS RDS
       ├── Arquivos no AWS S3
       └── Logs no AWS CloudWatch
```

## Funcionalidades implementadas

### Autenticação e usuários

* [x] Cadastro de usuários
* [x] Validação de e-mail
* [x] Senhas protegidas com Argon2
* [x] Login com JWT
* [x] Rota protegida para usuário autenticado
* [x] Configurações e secrets via variáveis de ambiente

### Arquivos

* [x] Upload autenticado
* [x] Organização de arquivos por usuário
* [x] UUIDs para evitar colisão de nomes
* [x] Listagem de arquivos do usuário autenticado
* [x] Download seguro
* [x] Exclusão de arquivo físico e metadados
* [x] Proteção contra acesso a arquivos de outros usuários
* [x] Validação de tipo de arquivo
* [x] Limite de upload de 10 MB

### Compartilhamento

* [x] Criação de links públicos temporários
* [x] Tokens seguros para links compartilhados
* [x] Expiração configurável
* [x] Listagem de links por arquivo
* [x] Revogação de links
* [x] Proteção contra cache em downloads compartilhados

### Versionamento

* [x] Criação automática da versão inicial
* [x] Upload de novas versões
* [x] Histórico de versões
* [x] Download de versões antigas
* [x] Restauração de versões anteriores
* [x] Atualização do arquivo principal para apontar para a versão atual
* [x] Rollback e limpeza de arquivos físicos em caso de erro
* [x] Restauração usando cópia de arquivo no storage ativo

### Banco de dados

* [x] PostgreSQL rodando em Docker
* [x] SQLAlchemy ORM
* [x] Relacionamento entre usuários e arquivos
* [x] Relacionamento entre arquivos e compartilhamentos
* [x] Relacionamento entre arquivos e versões
* [x] Migrations com Alembic
* [x] Evolução de schema sem apagar dados
* [x] Banco separado para testes automatizados

### Testes automatizados

* [x] Testes de health check
* [x] Testes de cadastro de usuário
* [x] Testes de login
* [x] Testes de rota protegida `/users/me`
* [x] Testes de upload de arquivos
* [x] Testes de listagem por usuário
* [x] Testes de download seguro
* [x] Testes de exclusão segura
* [x] Testes de isolamento entre usuários
* [x] Testes de validação de upload
* [x] Testes de compartilhamento público
* [x] Testes de revogação de links
* [x] Testes de links expirados
* [x] Testes de versionamento de arquivos
* [x] Testes de restauração de versões antigas
* [x] Storage temporário isolado durante os testes
* [x] Proteção para testes não enviarem arquivos reais para AWS S3

### Docker

* [x] PostgreSQL em container
* [x] FastAPI em container
* [x] Docker Compose com API + banco
* [x] Volume persistente para PostgreSQL
* [x] Volume para uploads locais
* [x] Healthcheck do PostgreSQL
* [x] API aguardando banco saudável antes de iniciar
* [x] `.dockerignore` para imagem mais limpa

### Storage

* [x] Storage local em disco
* [x] Interface base `StorageBackend`
* [x] Provider de storage por variável de ambiente
* [x] `LocalStorage`
* [x] `S3Storage`
* [x] Upload para AWS S3
* [x] Download a partir da AWS S3
* [x] Exclusão de objetos no S3
* [x] Cópia de objetos no S3 para restauração de versões
* [x] Script de teste de conexão com S3
* [x] Limpeza automática de arquivos temporários em downloads via S3

### Refatoração e arquitetura interna

* [x] Rotas organizadas por domínio
* [x] Rotas de arquivos separadas por responsabilidade
* [x] Camada de services criada
* [x] `file_service.py`
* [x] `share_service.py`
* [x] `version_service.py`
* [x] Regras de negócio movidas das rotas para services

## Endpoints principais

### Health

```http
GET /
GET /health
GET /db-test
```

### Autenticação

```http
POST /auth/register
POST /auth/login
GET  /users/me
```

### Arquivos

```http
POST   /files/upload
GET    /files/
GET    /files/{file_id}/download
DELETE /files/{file_id}
```

### Compartilhamento

```http
POST   /files/{file_id}/share
GET    /files/{file_id}/shares
DELETE /files/{file_id}/shares/{share_id}

GET    /shared/{token}
```

### Versionamento

```http
POST /files/{file_id}/versions
GET  /files/{file_id}/versions
GET  /files/{file_id}/versions/{version_number}/download
POST /files/{file_id}/versions/{version_number}/restore
```

## Estrutura do projeto

```text
ArcaFS/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   ├── users.py
│   │   │   ├── shares.py
│   │   │   └── files/
│   │   │       ├── upload.py
│   │   │       ├── download.py
│   │   │       ├── management.py
│   │   │       ├── shares.py
│   │   │       └── versions.py
│   │   └── router.py
│   │
│   ├── auth/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── file_service.py
│   │   ├── share_service.py
│   │   └── version_service.py
│   │
│   ├── storage/
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── provider.py
│   │   ├── s3.py
│   │   └── temp.py
│   │
│   └── main.py
│
├── migrations/
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_files.py
│   ├── test_shares.py
│   └── test_versions.py
│
├── docs/
├── scripts/
│   ├── __init__.py
│   └── test_s3_connection.py
│
├── docker/
├── storage/
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .dockerignore
├── .env.example
└── README.md
```

## Variáveis de ambiente

Exemplo de `.env.example`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DATABASE_NAME
TEST_DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/TEST_DATABASE_NAME
SECRET_KEY=replace-with-a-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

STORAGE_BACKEND=local

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=
```

### Storage local

Para desenvolvimento local padrão:

```env
STORAGE_BACKEND=local
```

Nesse modo, os arquivos são salvos em:

```text
storage/uploads/<user_id>/
```

### Storage AWS S3

Para testar o storage em S3:

```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=seu-bucket
```

O bucket deve ser privado. Os downloads continuam passando pela API, não por URL pública do S3.

## Como executar com Docker

### 1. Clone o repositório

```bash
git clone <repository-url>
cd ArcaFS
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Preencha o `.env` com os valores necessários.

Exemplo para rodar a API dentro do Docker Compose com PostgreSQL em container:

```env
DATABASE_URL=postgresql://arcafs:arcafs123@localhost:5432/arcafs_db
TEST_DATABASE_URL=postgresql://arcafs:arcafs123@localhost:5432/arcafs_test_db
SECRET_KEY=replace-with-a-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
STORAGE_BACKEND=local
```

O `docker-compose.yml` sobrescreve a `DATABASE_URL` dentro do container da API para usar o host interno `postgres`.

### 3. Suba a aplicação

```bash
docker compose up --build
```

A API estará disponível em:

```text
http://127.0.0.1:8000
```

A documentação interativa estará disponível em:

```text
http://127.0.0.1:8000/docs
```

### 4. Execute as migrations dentro do container

Em outro terminal:

```bash
docker compose exec api alembic upgrade head
```

### 5. Rodar em segundo plano

```bash
docker compose up -d --build
```

### 6. Ver logs

```bash
docker compose logs -f api
```

### 7. Parar containers

```bash
docker compose down
```

## Como executar localmente sem container da API

Também é possível rodar a API diretamente no ambiente local usando o venv.

### 1. Crie e ative o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o `.env`

Para rodar a API localmente fora do container, use `localhost` na URL do banco:

```env
DATABASE_URL=postgresql://arcafs:arcafs123@localhost:5432/arcafs_db
```

### 4. Suba o PostgreSQL

```bash
docker compose up -d postgres
```

### 5. Execute as migrations

```bash
alembic upgrade head
```

### 6. Inicie a API

```bash
uvicorn app.main:app --reload
```

A documentação interativa estará disponível em:

```text
http://127.0.0.1:8000/docs
```

## Como rodar os testes

Os testes usam um banco PostgreSQL separado para evitar apagar dados do ambiente principal.

### 1. Crie o banco de testes

```bash
docker exec -it arcafs-postgres psql -U arcafs -d postgres -c "CREATE DATABASE arcafs_test_db OWNER arcafs;"
```

### 2. Confirme a variável no `.env`

```env
TEST_DATABASE_URL=postgresql://arcafs:arcafs123@localhost:5432/arcafs_test_db
```

### 3. Rode os testes

```bash
pytest -v
```

Os testes criam e limpam as tabelas automaticamente no banco de testes.

Mesmo que o ambiente esteja configurado com:

```env
STORAGE_BACKEND=s3
```

os testes forçam o uso de storage local temporário para evitar envio de arquivos reais para a AWS.

## Como testar conexão com AWS S3

Antes de usar `STORAGE_BACKEND=s3` na aplicação, configure as variáveis AWS no `.env`:

```env
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=seu-bucket
```

Depois rode:

```bash
python -m scripts.test_s3_connection
```

Resultado esperado:

```text
S3 connection test passed
```

Esse script faz um upload simples para o bucket, verifica se o objeto existe e remove o objeto de teste.

## Como testar o ArcaFS com S3

### 1. Configure o `.env`

```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=seu-bucket
```

### 2. Suba a API

Localmente:

```bash
uvicorn app.main:app --reload
```

Ou via Docker:

```bash
docker compose down
docker compose up --build
```

### 3. Teste no Swagger

Acesse:

```text
http://127.0.0.1:8000/docs
```

Fluxo sugerido:

```text
POST /auth/register
POST /auth/login
POST /files/upload
GET  /files/
GET  /files/{file_id}/download
POST /files/{file_id}/share
GET  /shared/{token}
POST /files/{file_id}/versions
GET  /files/{file_id}/versions
POST /files/{file_id}/versions/{version_number}/restore
DELETE /files/{file_id}
```

No bucket S3, os objetos ficam organizados em uma estrutura parecida com:

```text
users/<user_id>/files/<uuid>.<extension>
```

## Configuração recomendada do bucket S3

Para ambiente de desenvolvimento, recomenda-se:

```text
Bucket privado
Block Public Access ativado
Object Ownership com ACLs desabilitadas
Criptografia padrão SSE-S3
Versionamento do bucket desativado inicialmente
```

O ArcaFS já possui versionamento próprio no banco de dados, então o versionamento nativo do bucket S3 pode ficar desativado no início.

## Permissões IAM mínimas para S3

Exemplo de policy para desenvolvimento:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ArcAFSListBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::SEU_BUCKET_AQUI"
    },
    {
      "Sid": "ArcAFSObjectAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::SEU_BUCKET_AQUI/*"
    }
  ]
}
```

Substitua `SEU_BUCKET_AQUI` pelo nome real do bucket.

## Roadmap

### Concluído

* [x] Setup inicial com FastAPI
* [x] PostgreSQL com Docker
* [x] SQLAlchemy ORM
* [x] Autenticação com JWT
* [x] Hash de senha com Argon2
* [x] Upload e download local
* [x] Exclusão de arquivos
* [x] Compartilhamento temporário com token
* [x] Versionamento de arquivos
* [x] Restauração de versões antigas
* [x] Migrations com Alembic
* [x] Refatoração das rotas de arquivos
* [x] Camada de services
* [x] Testes automatizados com Pytest
* [x] Banco PostgreSQL separado para testes
* [x] Dockerização da API
* [x] Docker Compose com FastAPI + PostgreSQL
* [x] Healthcheck do PostgreSQL
* [x] Abstração de storage
* [x] Storage local
* [x] Storage AWS S3
* [x] Script de teste de conexão com S3
* [x] Upload/download via AWS S3
* [x] Limpeza de arquivos temporários usados em downloads via S3

### Próximas etapas

* [ ] Testes unitários com mock para `S3Storage`
* [ ] Melhor tratamento de erros de S3
* [ ] Logs estruturados
* [ ] Auditoria de ações importantes
* [ ] Paginação e busca de arquivos
* [ ] Filtros por tipo, data e tamanho
* [ ] Lixeira e restauração de arquivos excluídos
* [ ] Padronização global de erros
* [ ] Frontend com React + TypeScript + Tailwind
* [ ] Deploy na AWS
* [ ] Banco de dados no AWS RDS
* [ ] Logs no AWS CloudWatch
* [ ] CI/CD com GitHub Actions
* [ ] Infraestrutura como código com Terraform

## Decisões técnicas

* O storage local foi escolhido para desenvolvimento inicial, permitindo validar o backend antes da integração com AWS S3.
* PostgreSQL foi escolhido por ser um banco relacional robusto e adequado para relacionamentos entre usuários, arquivos, compartilhamentos e versões.
* Alembic é usado para versionar mudanças no banco sem apagar dados existentes.
* JWT é usado para autenticação stateless.
* Argon2 protege senhas com hash moderno e resistente a ataques.
* Arquivos usam UUIDs internos para evitar colisão de nomes.
* Links compartilhados usam tokens aleatórios, expiração e headers de controle de cache.
* O versionamento mantém histórico imutável: restaurar uma versão antiga cria uma nova versão atual.
* A camada de services separa regras de negócio das rotas.
* A abstração de storage permite alternar entre storage local e AWS S3 usando variável de ambiente.
* Os testes usam banco e storage isolados para evitar interferência no ambiente real.
* Os testes forçam storage local para evitar envio acidental de arquivos para AWS.
* A API foi dockerizada para aproximar o ambiente local de um ambiente real de deploy.
* O bucket S3 permanece privado; a API é responsável por autenticar e entregar downloads.
* Downloads via S3 usam arquivo temporário local e limpeza automática após resposta.
* O frontend será desenvolvido após a consolidação das APIs principais.

## Autor

Desenvolvido por Philipe Mello como projeto de portfólio focado em Cloud, AWS, Backend Python e DevOps.
