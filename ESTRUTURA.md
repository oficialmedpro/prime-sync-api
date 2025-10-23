# 📁 Estrutura do Projeto

```
sync-api/
│
├── app.py                    # 🐍 Aplicação Flask principal
├── requirements.txt          # 📦 Dependências Python
├── Dockerfile               # 🐳 Container Docker
├── docker-compose.yml       # 🔧 Orquestração Docker
├── .env.example             # 🔐 Exemplo de variáveis de ambiente
│
├── README.md                # 📖 Documentação completa
├── GUIA_RAPIDO.md          # 🚀 Guia rápido de 5 minutos
├── ESTRUTURA.md            # 📁 Este arquivo
│
└── supabase-cronjob.sql    # ⏰ Script SQL do cronjob
```

---

## 🎯 O que cada arquivo faz

### `app.py`
API Flask com endpoints:
- `/sync` - Sincronização incremental
- `/health` - Health check

**Funcionalidades**:
- Busca último ID no Supabase
- Consulta apenas registros novos no Firebird
- Insere em lote no Supabase
- Resolve foreign keys (cliente_id, pedido_id)

---

### `requirements.txt`
Dependências necessárias:
- **Flask** - Framework web
- **fdb** - Conector Firebird
- **requests** - Cliente HTTP
- **gunicorn** - Servidor WSGI para produção

---

### `Dockerfile`
Define a imagem Docker:
- Base: `python:3.11-slim`
- Instala dependências do Firebird
- Instala dependências Python
- Expõe porta 5000
- Healthcheck automático

---

### `docker-compose.yml`
Orquestração do container:
- Variáveis de ambiente
- Porta mapping (5000:5000)
- Healthcheck
- Restart policy
- Labels do Traefik (para proxy reverso)

---

### `.env.example`
Template de configuração:
- Credenciais Firebird
- URL e Key do Supabase
- Token de segurança da API
- Porta da aplicação

**⚠️ Criar `.env` copiando este arquivo!**

---

### `supabase-cronjob.sql`
Script SQL para Supabase:
- Habilita pg_cron e http extensions
- Cria função de sincronização
- Implementa failover automático (beta → bi)
- Cria tabela de logs
- Agenda execução a cada 15 min

---

## 🔄 Fluxo de Sincronização

```
┌─────────────────────┐
│  Supabase Cronjob   │ (A cada 15 min)
│   (pg_cron)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Tenta beta.oficialmed.com.br/sync     │
└──────────┬──────────────────────────────┘
           │
    ┌──────▼─────┐
    │  Sucesso?  │
    └──────┬─────┘
           │
    ┌──────▼──────┐
    │   SIM       │  NÃO ────┐
    │             │          │
    │  Retorna    │          │
    └─────────────┘          │
                             ▼
         ┌────────────────────────────────────┐
         │ Fallback: bi.oficialmed.com.br/sync│
         └────────────────────────────────────┘

```

---

## 📊 Arquitetura Técnica

### 1. API Flask
```
Flask App
  ├── /health (GET)
  │    └── Retorna: {status, timestamp, version}
  │
  └── /sync (POST/GET)
       ├── sync_clientes_novos()
       │    ├── get_ultimo_id_supabase('prime_clientes')
       │    ├── SELECT * FROM CLIENTE WHERE CODIGO > ultimo_id
       │    └── INSERT INTO prime_clientes
       │
       └── sync_pedidos_novos()
            ├── get_ultimo_id_supabase('prime_pedidos')
            ├── SELECT * FROM ATENDIMENTO_A1 WHERE CODIGO > ultimo_id
            ├── Resolve foreign keys (cliente_id)
            └── INSERT INTO prime_pedidos
```

### 2. Docker Container
```
Docker Container
  ├── Gunicorn (2 workers)
  │    └── Flask App
  │
  ├── Health Check (30s interval)
  │    └── curl http://localhost:5000/health
  │
  └── Environment Variables
       ├── FIREBIRD_* (conexão)
       └── SUPABASE_* (API)
```

### 3. Supabase Cronjob
```
pg_cron Job
  ├── Executa: SELECT api.sync_prime_with_log()
  │    └── Chama: SELECT api.sync_prime_incremental()
  │         ├── Tenta: beta.oficialmed.com.br
  │         └── Fallback: bi.oficialmed.com.br
  │
  └── Salva log em: api.sync_logs
       ├── timestamp
       ├── resultado (JSON)
       ├── sucesso (boolean)
       ├── total_inseridos
       └── erro (text)
```

---

## 🔐 Segurança

1. **API Token** - Protege o endpoint `/sync`
2. **HTTPS** - Comunicação criptografada
3. **Variáveis de Ambiente** - Credenciais não em código
4. **Docker Isolation** - Container isolado
5. **Firewall** - Recomendado limitar IPs

---

## 📈 Performance

- **Latência**: ~100-500ms por request
- **Throughput**: ~100-500 registros/segundo
- **Timeout**: 300 segundos (5 min)
- **Workers**: 2 processos Gunicorn
- **Batch Size**: Ilimitado (insere todos de uma vez)

---

## 🛠️ Manutenção

### Logs
```bash
# Container logs
docker logs prime-sync-api -f

# Supabase logs
SELECT * FROM api.sync_logs ORDER BY timestamp DESC;
```

### Atualizar
```bash
# Pull mudanças
git pull

# Rebuild container
docker-compose build

# Restart
docker-compose up -d
```

### Backup
Configurações importantes:
- `.env` - Variáveis de ambiente
- `docker-compose.yml` - Orquestração
- Dados em `api.sync_logs` (Supabase)

---

## 🆘 Suporte

**Troubleshooting**:
1. Verificar health: `curl https://beta.oficialmed.com.br/health`
2. Ver logs: `docker logs prime-sync-api`
3. Testar manual: `curl -X POST https://beta.oficialmed.com.br/sync`
4. Ver logs Supabase: `SELECT * FROM api.sync_logs`

---

**Criado**: 23/10/2025
**Versão**: 1.0.0
**Autor**: Claude Code
