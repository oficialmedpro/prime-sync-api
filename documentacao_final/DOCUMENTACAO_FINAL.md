# DOCUMENTACAO FINAL - Sistema de Sincronizacao Firebird → Supabase

**Versao:** 2.0.0
**Data:** 24/10/2025
**Projeto:** Oficialmed - Sincronizacao Incremental Prime
**Status:** ✅ EM PRODUCAO

---

## 1. VISAO GERAL DO PROJETO

### 1.1 Objetivo
Sistema automatizado de sincronizacao incremental entre banco de dados Firebird (Prime) e PostgreSQL (Supabase), com cronjob executando a cada 30 minutos.

### 1.2 Tecnologias
- **Backend:** Python 3.x + Flask
- **Banco Origem:** Firebird 2.5+ (db.primesoftware.com.br)
- **Banco Destino:** PostgreSQL/Supabase (agdffspstbxeqhqtltvb.supabase.co)
- **Deploy:** Docker + Portainer
- **CI/CD:** GitHub Actions → Docker Hub
- **Automacao:** pg_cron (Supabase)

### 1.3 Status Atual
- ✅ API funcionando: https://sincro.oficialmed.com.br
- ✅ Cronjob ativo (a cada 30 minutos)
- ✅ Sincronizacao incremental funcionando
- ✅ 6 tipos de dados sincronizados

---

## 2. ARQUITETURA

### 2.1 Fluxo de Sincronizacao

```
┌─────────────────┐     Cronjob (30min)      ┌─────────────────┐
│   SUPABASE      │─────────────────────────→│   API Flask     │
│   (pg_cron)     │   POST /sync             │  sincro.oficial │
└─────────────────┘                          └─────────────────┘
                                                      │
                                    ┌─────────────────┴─────────────────┐
                                    ↓                                   ↓
                            ┌──────────────┐                   ┌──────────────┐
                            │  FIREBIRD    │                   │  SUPABASE    │
                            │  (Origem)    │                   │  (Destino)   │
                            │              │                   │              │
                            │ • CLIENTE    │──── Busca ────→   │ • prime_     │
                            │ • ATEND_A1   │     novos         │   clientes   │
                            │ • ATEND_A2   │     registros     │ • prime_     │
                            │ • ATEND_A3   │                   │   pedidos    │
                            │ • PROCESSO_  │                   │ • prime_     │
                            │   MANIPULAC  │                   │   formulas   │
                            │ • FORMA_     │                   │ • prime_     │
                            │   FARMAC..   │                   │   rastreab.  │
                            └──────────────┘                   └──────────────┘
```

### 2.2 Sincronizacao Incremental

A API busca o **ultimo codigo/ID** sincronizado no Supabase e busca apenas registros **MAIORES** no Firebird:

```sql
-- Exemplo: Clientes
SELECT MAX(codigo_cliente_original) FROM prime_clientes;  -- Ex: 9999999
SELECT * FROM CLIENTE WHERE CODIGO > 9999999;            -- Busca novos
```

---

## 3. ESTRUTURA DO PROJETO

### 3.1 Arvore de Arquivos (ESSENCIAIS)

```
Banco de Dados Prime/
│
├── sync-api/                          # ⭐ API EM PRODUCAO
│   ├── app.py                         # API Flask principal
│   ├── requirements.txt               # Dependencias Python
│   ├── Dockerfile                     # Build da imagem Docker
│   ├── docker-compose.yml             # Compose local
│   ├── stack-portainer.yml            # Stack Portainer
│   ├── supabase-cronjob.sql          # SQL do cronjob
│   ├── .github/workflows/
│   │   └── docker-build.yml          # CI/CD GitHub Actions
│   └── README.md                      # Documentacao da API
│
├── sql_supabase_rastreabilidade_completo.sql  # Schema Supabase
├── supabase_schema.sql                        # Schema completo
│
├── verificar_novos_registros.py      # ⭐ Script de validacao
├── validar_migracao_completa.py      # ⭐ Validacao com amostras
├── validar_status_atual.py           # ⭐ Status das tabelas
├── verificar_totais_rapido.py        # ⭐ Comparacao rapida
│
└── DOCUMENTACAO_FINAL.md             # 📄 Este arquivo
```

### 3.2 Arquivos por Categoria

#### **PRODUCAO (NAO REMOVER)** ⭐

| Arquivo | Descricao | Uso |
|---------|-----------|-----|
| `sync-api/app.py` | API Flask principal | Sincronizacao em producao |
| `sync-api/requirements.txt` | Dependencias | Build Docker |
| `sync-api/Dockerfile` | Imagem Docker | Deploy |
| `sync-api/supabase-cronjob.sql` | Cronjob config | Automacao |
| `verificar_novos_registros.py` | Valida sync | Monitoramento |
| `validar_migracao_completa.py` | Valida dados | Validacao |
| `verificar_totais_rapido.py` | Compara totais | Debug |

#### **DOCUMENTACAO (MANTER)** 📄

| Arquivo | Descricao |
|---------|-----------|
| `DOCUMENTACAO_FINAL.md` | Documentacao completa (este arquivo) |
| `sync-api/README.md` | Documentacao da API |
| `sync-api/DEPLOY.md` | Guia de deploy |
| `GUIA_IMPLEMENTACAO_SUPABASE.md` | Guia de implementacao |

#### **SCHEMAS SQL (MANTER)** 🗄️

| Arquivo | Descricao |
|---------|-----------|
| `sql_supabase_rastreabilidade_completo.sql` | Schema completo das tabelas |
| `supabase_schema.sql` | Schema alternativo |
| `supabase_schema_prime.sql` | Schema prime |

#### **TESTES E DESENVOLVIMENTO (PODEM SER REMOVIDOS)** 🗑️

**Total: ~150 arquivos de teste/desenvolvimento**

- `teste_*.py` (38 arquivos)
- `teste_*.sql` (20 arquivos)
- `testar_*.py` (10 arquivos)
- `exportar_*.py` (30 arquivos) - Scripts antigos de exportacao
- `executar_*.py` (12 arquivos) - Scripts antigos de execucao
- `migrar_*.py` (8 arquivos) - Scripts antigos de migracao
- `migracao_lote_*.sql` (28 arquivos) - Migracoes SQL antigas
- `analisar_*.sql` (15 arquivos) - Analises temporarias
- `investigar_*.py/.sql` (20 arquivos) - Investigacoes temporarias
- `buscar_*.py/.sql` (18 arquivos) - Buscas temporarias
- `verificar_*.sql` (25 arquivos) - Verificacoes antigas
- `dados_*.json/.txt` (5 arquivos) - Dados temporarios

---

## 4. API DE SINCRONIZACAO (sync-api/app.py)

### 4.1 Endpoints

#### `GET /health`
**Descricao:** Health check da API
**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T22:01:42.481063",
  "version": "2.0.0"
}
```

#### `POST /sync`
**Descricao:** Executa sincronizacao incremental de todos os tipos de dados
**Resposta:**
```json
{
  "sucesso": true,
  "timestamp": "2025-10-24T22:03:12.470884",
  "version": "2.0.0",
  "tempo_execucao_segundos": 85.83,
  "total_inseridos": 396,

  "clientes": {
    "inseridos": 0,
    "mensagem": "Nenhum cliente novo"
  },
  "pedidos": {
    "inseridos": 0,
    "mensagem": "Nenhum pedido novo"
  },
  "formulas": {
    "inseridos": 0,
    "mensagem": "Nenhuma formula nova"
  },
  "formulas_itens": {
    "inseridos": 0,
    "mensagem": "Nenhum item novo"
  },
  "rastreabilidade": {
    "inseridos": 396,
    "mensagem": "396 registros sincronizados"
  },
  "tipos_processo": {
    "inseridos": 0,
    "mensagem": "Nenhum tipo novo"
  }
}
```

### 4.2 Funcoes de Sincronizacao

#### `sync_clientes_novos()`
**Tabela Origem:** `CLIENTE`
**Tabela Destino:** `prime_clientes`
**Criterio:** `ATIVO = -1` (clientes ativos)
**Busca por:** `CODIGO > ultimo_codigo`

**Campos sincronizados:**
- codigo_cliente_original
- nome
- cpf_cnpj
- email
- telefone
- cidade
- uf
- ativo

#### `sync_pedidos_novos()`
**Tabela Origem:** `ATENDIMENTO_A1`
**Tabela Destino:** `prime_pedidos`
**Busca por:** `CODIGO > ultimo_codigo`

**Campos sincronizados:**
- codigo_orcamento_original
- codigo_cliente_original
- numero_orcamento
- data_cadastro
- data_aprovacao
- data_entrega
- valor_total
- status_pedido

#### `sync_formulas_novas()`
**Tabela Origem:** `ATENDIMENTO_A2`
**Tabela Destino:** `prime_formulas`
**Busca por:** `CODIGO_ATEND_A1 > ultimo_codigo`

**Campos sincronizados:**
- codigo_orcamento_original
- numero_formula
- descricao
- texto_rotulo
- quantidade
- valor_unitario

#### `sync_formulas_itens_novos()`
**Tabela Origem:** `ATENDIMENTO_A3`
**Tabela Destino:** `prime_formulas_itens`
**Busca por:** `CODIGO_ATEND_A1 > ultimo_codigo`

**Campos sincronizados:**
- codigo_atendimento_original
- codigo_produto
- nome_produto
- quantidade
- valor_custo
- valor_venda

#### `sync_rastreabilidade_nova()`
**Tabela Origem:** `PROCESSO_MANIPULACAO`
**Tabela Destino:** `prime_rastreabilidade`
**Busca por:** `CODIGO > ultimo_codigo`

**⚠️ IMPORTANTE:** Esta funcao faz **lookup de Foreign Keys**:
1. Busca `pedido_id` em `prime_pedidos` usando `codigo_orcamento_original`
2. Busca `tipo_processo_id` em `prime_tipos_processo` usando `codigo_tipo_original`
3. Pula registros que nao tenham relacionamentos validos

**Campos sincronizados:**
- codigo_processo_original
- pedido_id (FK)
- codigo_orcamento_original
- tipo_processo_id (FK)
- codigo_tipo_original
- tipo_movimento
- data_processo
- sequencia
- status_processo

#### `sync_tipos_processo_novos()`
**Tabela Origem:** `FORMAFARMACEUTICA_PROCESSO_TIPO`
**Tabela Destino:** `prime_tipos_processo`
**Busca por:** `CODIGO > ultimo_codigo`

**Campos sincronizados:**
- codigo_tipo_original
- nome_processo
- nome_ficha
- tipo_producao
- sequencia
- ativo
- processo_opcional
- pagar_comissao

---

## 5. CRONJOB AUTOMATICO (SUPABASE)

### 5.1 Configuracao Atual

**Nome do Job:** `prime-sync-api-cron`
**Frequencia:** `*/30 * * * *` (a cada 30 minutos)
**URL:** `https://sincro.oficialmed.com.br/sync`
**Metodo:** `POST`

**Comando SQL:**
```sql
SELECT net.http_post(
  url := 'https://sincro.oficialmed.com.br/sync',
  headers := jsonb_build_object(
    'Content-Type', 'application/json'
  ),
  body := '{}'::jsonb
);
```

### 5.2 Verificar Status do Cronjob

**Ver job ativo:**
```sql
SELECT
  jobid,
  jobname,
  schedule,
  command,
  active
FROM cron.job
WHERE jobname = 'prime-sync-api-cron';
```

**Ver ultimas execucoes:**
```sql
SELECT
  runid,
  status,
  return_message,
  start_time AT TIME ZONE 'America/Sao_Paulo' as horario_br,
  end_time AT TIME ZONE 'America/Sao_Paulo' as fim_br,
  EXTRACT(EPOCH FROM (end_time - start_time)) as duracao_seg
FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'prime-sync-api-cron')
ORDER BY start_time DESC
LIMIT 10;
```

**Executar manualmente:**
```sql
SELECT net.http_post(
  url := 'https://sincro.oficialmed.com.br/sync',
  headers := jsonb_build_object(
    'Content-Type', 'application/json'
  ),
  body := '{}'::jsonb
);
```

---

## 6. DEPLOY E CI/CD

### 6.1 Repositorio GitHub

**URL:** https://github.com/oficialmedpro/prime-sync-api
**Branch:** master

### 6.2 Fluxo de Deploy

```
1. Commit local → Push para GitHub
2. GitHub Actions detecta push
3. Build da imagem Docker
4. Push para Docker Hub
5. Portainer pull da nova imagem
6. Restart do container
```

### 6.3 Deploy Manual via Portainer

1. Acesse Portainer
2. Va em **Stacks**
3. Selecione a stack da API
4. Clique em **"Update the stack"**
5. Marque **"Re-pull image"**
6. Clique em **"Update"**

### 6.4 Variaveis de Ambiente

Arquivo `.env` (nao versionado):
```env
FIREBIRD_HOST=db.primesoftware.com.br
FIREBIRD_DATABASE=oficialmed1250
FIREBIRD_USER=OFICIALMED
FIREBIRD_PASSWORD=Lt-@=waIh))Ql3~

SUPABASE_URL=https://agdffspstbxeqhqtltvb.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

PORT=5000
```

---

## 7. SCRIPTS DE VALIDACAO

### 7.1 verificar_novos_registros.py

**Funcao:** Compara ultimo codigo no Supabase vs Firebird
**Execucao:** `python verificar_novos_registros.py`

**O que faz:**
1. Conecta no Firebird e Supabase
2. Busca ultimo codigo em cada tabela do Supabase
3. Conta quantos registros novos existem no Firebird
4. Mostra exemplos de codigos novos

**Resultado esperado:**
```
VERIFICACAO DE NOVOS REGISTROS FIREBIRD vs SUPABASE
================================================================================

VERIFICANDO: CLIENTES
   Ultimo codigo no Supabase: 9,999,999
   ✅ Nenhum registro novo no Firebird

RESUMO DA VERIFICACAO
================================================================================
✅ OK | CLIENTES     | 0 novos registros
✅ OK | PEDIDOS      | 0 novos registros
✅ OK | FORMULAS     | 0 novos registros
✅ OK | ITENS        | 0 novos registros

✅ CONCLUSAO: Todos os registros estao sincronizados!
```

### 7.2 validar_migracao_completa.py

**Funcao:** Valida totais e amostras de dados
**Execucao:** `python validar_migracao_completa.py`

**O que faz:**
1. Conta totais no Firebird
2. Conta totais no Supabase
3. Compara os totais
4. Valida amostra de 5 registros de cada tipo
5. Compara campo a campo

### 7.3 verificar_totais_rapido.py

**Funcao:** Verificacao rapida de totais
**Execucao:** `python verificar_totais_rapido.py`

**O que faz:**
1. Conta registros no Firebird
2. Busca ultimo ID no Supabase
3. Mostra comparacao rapida

**Resultado esperado:**
```
TOTAIS NO FIREBIRD:
   Clientes: 37,271
   Pedidos: 16,844
   Formulas: 32,402
   Itens de Formulas: 348,280
   Tipos de Processo: 9
   Rastreabilidade: 208,902

ULTIMO ID NO SUPABASE:
   Clientes (ultimo codigo): 9999999
   Pedidos (ultimo codigo): 251003317
   Formulas (ultimo ID): 32199
   Rastreabilidade (ultimo ID): 206975
```

---

## 8. TABELAS DO SUPABASE

### 8.1 Estrutura das Tabelas

#### `prime_clientes`
```sql
CREATE TABLE api.prime_clientes (
  id BIGSERIAL PRIMARY KEY,
  codigo_cliente_original INTEGER UNIQUE NOT NULL,
  nome VARCHAR(255) NOT NULL,
  cpf_cnpj VARCHAR(20),
  email VARCHAR(255),
  telefone VARCHAR(20),
  cidade VARCHAR(100),
  uf VARCHAR(2),
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `prime_pedidos`
```sql
CREATE TABLE api.prime_pedidos (
  id BIGSERIAL PRIMARY KEY,
  codigo_orcamento_original INTEGER UNIQUE NOT NULL,
  cliente_id BIGINT REFERENCES api.prime_clientes(id),
  codigo_cliente_original INTEGER,
  numero_orcamento VARCHAR(50),
  data_cadastro DATE,
  data_aprovacao DATE,
  data_entrega DATE,
  valor_total NUMERIC(15,2),
  status_pedido VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `prime_formulas`
```sql
CREATE TABLE api.prime_formulas (
  id BIGSERIAL PRIMARY KEY,
  pedido_id BIGINT REFERENCES api.prime_pedidos(id),
  codigo_orcamento_original INTEGER,
  numero_formula INTEGER,
  descricao TEXT,
  texto_rotulo TEXT,
  quantidade NUMERIC(10,2),
  valor_unitario NUMERIC(15,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `prime_formulas_itens`
```sql
CREATE TABLE api.prime_formulas_itens (
  id BIGSERIAL PRIMARY KEY,
  formula_id BIGINT REFERENCES api.prime_formulas(id),
  codigo_atendimento_original INTEGER,
  codigo_produto INTEGER,
  nome_produto VARCHAR(255),
  quantidade NUMERIC(10,4),
  valor_custo NUMERIC(15,2),
  valor_venda NUMERIC(15,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `prime_tipos_processo`
```sql
CREATE TABLE api.prime_tipos_processo (
  id BIGSERIAL PRIMARY KEY,
  codigo_tipo_original INTEGER UNIQUE NOT NULL,
  nome_processo VARCHAR(100),
  nome_ficha VARCHAR(100),
  tipo_producao INTEGER,
  sequencia INTEGER,
  ativo BOOLEAN DEFAULT true,
  processo_opcional BOOLEAN DEFAULT false,
  pagar_comissao BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `prime_rastreabilidade`
```sql
CREATE TABLE api.prime_rastreabilidade (
  id BIGSERIAL PRIMARY KEY,
  codigo_processo_original INTEGER UNIQUE NOT NULL,
  pedido_id BIGINT REFERENCES api.prime_pedidos(id),
  codigo_orcamento_original INTEGER,
  tipo_processo_id BIGINT REFERENCES api.prime_tipos_processo(id),
  codigo_tipo_original INTEGER,
  tipo_movimento INTEGER,
  codigo_funcionario INTEGER,
  data_processo DATE,
  hora_processo TIME,
  sequencia INTEGER,
  status_processo VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### 8.2 Indices para Performance

```sql
-- Clientes
CREATE INDEX idx_prime_clientes_codigo ON api.prime_clientes(codigo_cliente_original);
CREATE INDEX idx_prime_clientes_cpf ON api.prime_clientes(cpf_cnpj);

-- Pedidos
CREATE INDEX idx_prime_pedidos_codigo ON api.prime_pedidos(codigo_orcamento_original);
CREATE INDEX idx_prime_pedidos_cliente ON api.prime_pedidos(cliente_id);
CREATE INDEX idx_prime_pedidos_data ON api.prime_pedidos(data_cadastro);

-- Rastreabilidade
CREATE INDEX idx_prime_rastreabilidade_codigo ON api.prime_rastreabilidade(codigo_processo_original);
CREATE INDEX idx_prime_rastreabilidade_pedido ON api.prime_rastreabilidade(pedido_id);
CREATE INDEX idx_prime_rastreabilidade_data ON api.prime_rastreabilidade(data_processo);
```

---

## 9. MONITORAMENTO E LOGS

### 9.1 Verificar Status da API

```bash
# Health check
curl https://sincro.oficialmed.com.br/health

# Executar sync manualmente
curl https://sincro.oficialmed.com.br/sync
```

### 9.2 Logs do Container (Portainer)

1. Acesse Portainer
2. Va em **Containers**
3. Clique no container da API
4. Clique em **"Logs"**
5. Veja logs em tempo real

### 9.3 Metricas de Performance

**Tempo medio de execucao:**
- Com novos registros: 60-90 segundos
- Sem novos registros: 0.5-2 segundos

**Volume de dados:**
- Clientes: ~100-200 novos/mes
- Pedidos: ~500-1000 novos/mes
- Formulas: ~800-1500 novas/mes
- Rastreabilidade: ~2000-3000 novos/mes

---

## 10. TROUBLESHOOTING

### 10.1 API nao responde

**Verificar:**
1. Container esta rodando no Portainer
2. Porta 5000 esta exposta
3. Firewall permite conexoes

**Solucao:**
```bash
# Restart do container
docker restart sync-api
```

### 10.2 Cronjob nao esta executando

**Verificar:**
```sql
-- Ver se job esta ativo
SELECT * FROM cron.job WHERE jobname = 'prime-sync-api-cron';

-- Ver historico
SELECT * FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'prime-sync-api-cron')
ORDER BY start_time DESC LIMIT 5;
```

**Solucao:**
```sql
-- Reagendar job
SELECT cron.unschedule('prime-sync-api-cron');
SELECT cron.schedule(
  'prime-sync-api-cron',
  '*/30 * * * *',
  $$SELECT net.http_post(...)$$
);
```

### 10.3 Erro HTTP 400 em rastreabilidade

**Causa:** Foreign Keys nao encontradas (pedido_id ou tipo_processo_id)

**Verificar:**
```sql
-- Ver pedidos sem registros no Supabase
SELECT PM.CODIGO_MOV
FROM PROCESSO_MANIPULACAO PM
WHERE PM.CODIGO_MOV NOT IN (
  SELECT codigo_orcamento_original FROM prime_pedidos
);
```

**Solucao:** Sincronizar pedidos primeiro, depois rastreabilidade

### 10.4 Erro HTTP 409 em tipos_processo

**Causa:** Registro duplicado (ja existe no Supabase)

**Verificar:**
```sql
SELECT * FROM prime_tipos_processo;
```

**Solucao:** Nao e um problema, significa que o registro ja existe. Ignora o erro.

---

## 11. PROXIMOS PASSOS / MELHORIAS

### 11.1 Curto Prazo
- [ ] Adicionar autenticacao por token nos endpoints
- [ ] Criar dashboard de monitoramento
- [ ] Implementar retry automatico em caso de falha
- [ ] Adicionar alertas por email em caso de erro

### 11.2 Medio Prazo
- [ ] Adicionar sincronizacao de produtos
- [ ] Implementar sincronizacao bidirecional
- [ ] Criar API de consulta de dados
- [ ] Adicionar cache para melhorar performance

### 11.3 Longo Prazo
- [ ] Migrar para arquitetura serverless
- [ ] Implementar CDC (Change Data Capture)
- [ ] Criar data warehouse para analytics
- [ ] Integrar com ferramentas de BI

---

## 12. CONTATOS E SUPORTE

**Desenvolvedor:** Claude Code + Equipe Oficialmed
**Repositorio:** https://github.com/oficialmedpro/prime-sync-api
**API:** https://sincro.oficialmed.com.br
**Supabase:** https://supabase.com/dashboard/project/agdffspstbxeqhqtltvb

---

## 13. CHANGELOG

### v2.0.0 (24/10/2025)
- ✅ Corrigido erro HTTP 400 em rastreabilidade (lookup de FKs)
- ✅ Corrigido erro SQL em tipos_processo (nomes de colunas)
- ✅ Adicionado lookup de pedido_id e tipo_processo_id
- ✅ Melhorado tratamento de erros com logs detalhados
- ✅ Deploy em producao via Portainer
- ✅ Cronjob ativo (30 minutos)
- ✅ Documentacao completa

### v1.0.0 (23/10/2025)
- Versao inicial da API
- Sincronizacao basica de clientes, pedidos e formulas

---

**FIM DA DOCUMENTACAO**
