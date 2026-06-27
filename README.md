# ArcaFS

> A secure cloud file manager API built with Python, FastAPI, PostgreSQL, Docker and AWS-focused architecture.

O **ArcaFS (Ark File System)** é um gerenciador de arquivos em nuvem inspirado em soluções como Google Drive e Dropbox.

O projeto foi criado como portfólio para demonstrar conhecimentos práticos em desenvolvimento backend, bancos de dados relacionais, Docker, Cloud Computing, AWS, segurança, arquitetura de APIs e práticas de DevOps.

## Objetivo

Construir uma aplicação completa de gerenciamento de arquivos que permita:

* cadastro e autenticação de usuários;
* upload, download e exclusão de arquivos;
* armazenamento de metadados em PostgreSQL;
* controle de acesso por usuário;
* compartilhamento temporário por links públicos;
* versionamento e restauração de arquivos;
* migração futura para AWS S3, RDS, CloudWatch e CI/CD.

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

### Infraestrutura

* Docker
* Docker Compose
* Variáveis de ambiente com `.env`

### Tecnologias planejadas

* React
* TypeScript
* Vite
* Tailwind CSS
* AWS S3
* AWS RDS
* AWS EC2 ou ECS
* AWS CloudWatch
* GitHub Actions
* Pytest
* Terraform

## Arquitetura atual

```text
Cliente / Swagger
       │
       ▼
FastAPI + Uvicorn
       │
       ├── JWT Authentication
       ├── SQLAlchemy ORM
       │       │
       │       ▼
       │   PostgreSQL em Docker
       │
       └── Storage local
           storage/uploads/<user_id>/
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

### Banco de dados

* [x] PostgreSQL rodando em Docker
* [x] SQLAlchemy ORM
* [x] Relacionamento entre usuários e arquivos
* [x] Relacionamento entre arquivos e compartilhamentos
* [x] Relacionamento entre arquivos e versões
* [x] Migrations com Alembic
* [x] Evolução de schema sem apagar dados

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
│   │   └── router.py
│   │
│   ├── auth/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── storage/
│   └── main.py
│
├── migrations/
├── tests/
├── docs/
├── scripts/
├── docker/
├── storage/
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Como executar localmente

### 1. Clone o repositório

```bash
git clone <repository-url>
cd ArcaFS
```

### 2. Crie e ative o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Preencha o `.env` com os valores locais necessários.

### 5. Suba o PostgreSQL

```bash
docker compose up -d
```

### 6. Execute as migrations

```bash
alembic upgrade head
```

### 7. Inicie a API

```bash
uvicorn app.main:app --reload
```

A documentação interativa estará disponível em:

```text
http://127.0.0.1:8000/docs
```

## Roadmap

### Próximas etapas

* [ ] Testes automatizados com Pytest
* [ ] Banco PostgreSQL separado para testes
* [ ] Paginação e busca de arquivos
* [ ] Filtros por tipo, data e tamanho
* [ ] Lixeira e restauração de arquivos excluídos
* [ ] Logs estruturados e auditoria
* [ ] Dockerização completa da API
* [ ] Containerização de FastAPI + PostgreSQL em um único ambiente
* [ ] Abstração de storage local e AWS S3
* [ ] Upload e download via AWS S3
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
* O frontend será desenvolvido após a consolidação das APIs principais.

## Autor

Desenvolvido por Philipe Mello como projeto de portfólio focado em Cloud, AWS, Backend Python e DevOps.
