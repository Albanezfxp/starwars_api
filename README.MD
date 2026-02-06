# Star Wars API (FastAPI) — Technical Test

API REST construída com **FastAPI** que consulta o upstream **SWAPI** e expõe endpoints para **Peoples, Films, Planets, Species, Vehicles e Starships**, com recursos adicionais como:

- **Paginação** (`page`, `limit`)
- **Busca** por texto (`q`, case-insensitive)
- **Ordenação** (`sort`, `order`)
- **Expansão de relacionamentos** (`expand`) — quando aplicável
- **Cache em memória (TTL)** para reduzir chamadas repetidas ao upstream
- **Autenticação opcional por API Key** via header `x-api-key`

> Este README foi pensado para rodar **localmente via Docker**, simulando “nuvem” (serviço isolado, configurável por env vars e porta exposta).

---

## Sumário
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Como rodar local](#como-rodar-local)
  - [Rodar com Docker](#rodar-com-docker)
  - [Rodar com Docker Compose](#rodar-com-docker-compose)
  - [Rodar sem Docker](#rodar-sem-docker)
- [Autenticação (API Key)](#autenticação-api-key)
- [Endpoints](#endpoints)
- [Query Params](#query-params)
- [Exemplos (curl)](#exemplos-curl)
- [Testes](#testes)
- [Troubleshooting](#troubleshooting)
- [Autor](#autor)

---

## Arquitetura

- **FastAPI** como camada HTTP
- **Routers por domínio** (`routers/*_router.py`) para manter separação de responsabilidades
- **Integração com SWAPI** via `requests`
- **Cache TTL em memória** para respostas de upstream (reduz latência e limita chamadas repetidas)
- **Middleware de API Key** que habilita/desabilita auth automaticamente conforme `API_KEY`

### Estrutura do projeto (visão geral)
```text
.
├── main.py
├── routers/
│   ├── peoples_router.py
│   ├── films_router.py
│   ├── planets_router.py
│   ├── species_router.py
│   ├── vehicles_router.py
│   ├── vehicles_router.py
│   └── starships_router.py
├── requirements.txt
├── Dockerfile
└── tests/ (se existir)
```
## Requisitos

### Para rodar com Docker
- Docker Desktop instalado e rodando

### Para rodar sem Docker
- Python 3.10+
- pip

---

## Como rodar local

## Rodar com Docker

#### 1) Build da imagem
Na raiz do projeto (onde está o `Dockerfile`):

```
docker build -t swapi-api .
```

Na raiz do projeto (onde está o Dockerfile):
```
docker build -t swapi-api .
```

#### 2) Subir o container
Atenção: 
se as portas 8080/8081 estiverem ocupadas por outros serviços, use outra porta externa (ex: 8082, 8083, etc.).
O container expõe internamente 8080. Você escolhe a porta externa no -p.

## Sem API Key (auth desligada)
```
docker run --rm -p 8082:8080 swapi-api
```

### Com API Key (auth ligada)
```
docker run --rm -p 8082:8080 -e API_KEY=starwars_secret_key swapi-api
```
#### 3) Acessar

##### Swagger UI: http://localhost:8082/docs

##### OpenAPI JSON: http://localhost:8082/openapi.json

###### Observação: se a API_KEY estiver ligada e o Swagger estiver retornando 401, veja a seção Troubleshooting.

Rodar com Docker Compose
Recomendado para simular “nuvem local” (serviço com restart policy, envs e portas padronizadas).

### Crie docker-compose.yml na raiz:

```
services:
  swapi-api:
    build: .
    container_name: swapi-api
    ports:
      - "8082:8080"
    environment:
      API_KEY: "starwars_secret_key"
    restart: unless-stopped
```
### Subir:
```
docker compose up -d --build
```

### Logs:

```
docker compose logs -f
```

### Parar:

```
docker compose down
```

### Rodar sem Docker

1) Criar/ativar ambiente virtual

```
python -m venv .venv
```

### Windows:

```
.venv\Scripts\activate
Linux/Mac:
```
```
source .venv/bin/activate
```

#### 2) Instalar dependências

```
pip install -r requirements.txt
```

#### 3) Subir a API
```

uvicorn main:app --host 0.0.0.0 --port 8080
```

### Swagger:

http://localhost:8080/docs

### Autenticação (API Key)
A autenticação é opcional e controlada por env var:

###### Se API_KEY não existir → autenticação desligada

###### Se API_KEY existir → é obrigatório enviar o header:
```
x-api-key: <valor-da-API_KEY>
```

### Exemplo:

API_KEY=starwars_secret_key

Header: x-api-key: starwars_secret_key

### Endpoints
Base URL (local): http://localhost:8082

#### Caminhos confirmados via /openapi.json.

```
Peoples
GET /peoples/

GET /peoples/{id}

Films
GET /films/

GET /films/{id}

Planets
GET /planets/

GET /planets/{planet_id}

Species
GET /species/

GET /species/{species_id}

Vehicles
GET /vehicles/

GET /vehicles/{vehicle_id}

Starships
GET /starships/

GET /starships/{starship_id}
```

### Query Params
##### Alguns endpoints suportam:

###### q (string): busca por nome/título (contém, case-insensitive)

###### page (int, min 1): número da página

###### limit (int, min 1, max 50): itens por página

###### sort (string): campo para ordenar (depende do recurso)

###### order (asc | desc): direção da ordenação

###### expand (string): expande relacionamentos (depende do recurso)

###### Consulte /docs para ver exatamente quais endpoints aceitam quais parâmetros e quais campos são suportados em sort/expand.

### Exemplos (curl)
##### Ajuste a porta conforme seu docker run (ex: 8082).

#### Listar peoples (com API Key)
```
curl -H "x-api-key: starwars_secret_key" http://localhost:8082/peoples/
```
#### People por ID
```
curl -H "x-api-key: starwars_secret_key" http://localhost:8082/peoples/1
```
#### Busca por nome (q)
```
curl -H "x-api-key: starwars_secret_key" "http://localhost:8082/peoples/?q=luke"
```
#### Paginação (page/limit)
```
curl -H "x-api-key: starwars_secret_key" "http://localhost:8082/films/?page=1&limit=5"
```

#### Ordenação (sort/order) — exemplo
```
curl -H "x-api-key: starwars_secret_key" "http://localhost:8082/starships/?sort=name&order=asc"
```
#### Sem header (deve retornar 401 quando API_KEY está ligada)
```
curl -i http://localhost:8082/films/
```
## Testes
#### Se o projeto tiver testes com pytest, rode:
```
pytest -q
```

#### Opcional (via Docker):
```
docker run --rm swapi-api pytest -q
```

### Porta já está em uso erro:
```
Bind for 0.0.0.0:8082 failed: port is already allocated
```
#### Solução: mude a porta externa.
```
docker run --rm -p 8083:8080 -e API_KEY=starwars_secret_key swapi-api
```

### Conflito de nome de container
Erro:

Conflict. The container name "/swapi-api" is already in use...

#### Solução:
```
docker rm -f swapi-api
```
## Swagger retorna 401
Se você ligou a API_KEY, o navegador não consegue enviar header sozinho ao abrir /docs. Você pode:

#### A) Rodar sem API_KEY só para visualizar docs

```
docker run --rm -p 8082:8080 swapi-api
```
#### B) Liberar docs/openapi no middleware (recomendado em dev)

##### Allowlist para:
```
/docs

/openapi.json

/docs/oauth2-redirect

/redoc (opcional)

```

#### C) Usar extensão no browser para injetar header

Ex: “ModHeader” adicionando x-api-key: starwars_secret_key.

404 em /
Se GET / 
retornar 404, é normal caso você não tenha rota raiz.
Use /docs ou os endpoints listados.

### Autor
## Gabriel Albanez
