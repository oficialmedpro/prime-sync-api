# 🚀 GUIA COMPLETO DE DEPLOY

## ⚠️ **ALERTA CRÍTICO - DEPLOY NO EASYPANEL** ⚠️

### 🔴 **PROBLEMA CONHECIDO: EasyPanel NÃO atualiza containers automaticamente!**

O EasyPanel **builda a nova imagem Docker**, mas **NÃO atualiza os containers** para usar a nova imagem. Os containers continuam rodando a imagem antiga, mesmo após múltiplos deploys.

### ✅ **SOLUÇÃO OBRIGATÓRIA - Execute SEMPRE após deploy no EasyPanel:**

**No console do servidor, execute:**

```bash
docker service scale prime-sync-api_prime-sync=0 && \
sleep 5 && \
docker service update --image easypanel/prime-sync-api/prime-sync:latest prime-sync-api_prime-sync --force && \
docker service scale prime-sync-api_prime-sync=1
```

**📖 Documentação completa:** [`SOLUCAO_DEPLOY_EASYPANEL.md`](./SOLUCAO_DEPLOY_EASYPANEL.md)

---

## Pré-requisitos

- [x] Domínio `sincro.oficialmed.com.br` apontando para o servidor
- [x] Portainer instalado e funcionando
- [x] Traefik configurado (com Let's Encrypt)
- [x] Network `OficialMed` criada
- [x] Docker Hub account: `oficialmedpro`

---

## PARTE 1: Setup GitHub (5 min)

### 1.1 Criar Repositório

```bash
# No GitHub, criar novo repositório
Nome: prime-sync-api
Visibilidade: Private (recomendado)
```

### 1.2 Adicionar Secret do Docker Hub

1. GitHub → Seu repositório → **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret**
3. **Name**: `DOCKER_HUB_TOKEN`
4. **Value**: [Token do Docker Hub]

**Como gerar token do Docker Hub:**
1. Docker Hub → Account Settings → Security → New Access Token
2. Description: `GitHub Actions - prime-sync-api`
3. Access permissions: `Read, Write, Delete`
4. Copie o token (aparece apenas uma vez!)

### 1.3 Push do Código

```bash
# No seu computador local
cd sync-api

# Inicializar Git (se ainda não foi)
git init

# Adicionar remote
git remote add origin https://github.com/oficialmedpro/prime-sync-api.git

# Commit inicial
git add .
git commit -m "Initial commit: Prime Sync API"

# Push
git push -u origin main
```

🎉 **Pronto!** GitHub Actions vai automaticamente:
- Fazer build da imagem Docker
- Fazer push para `oficialmedpro/prime-sync-api:latest`
- Demorar ~2-3 minutos

Acompanhe em: **Actions** tab no GitHub

---

## PARTE 2: Setup Portainer (10 min)

### 2.1 Criar Secrets

Acesse: **Portainer** → **Secrets** → **+ Add secret**

Criar os 4 secrets (veja valores em `SECRETS.md`):

1. **FIREBIRD_PASS**
   ```
   [senha do Firebird OFICIALMED]
   ```

2. **SUPABASE_URL**
   ```
   https://xxxxxxxxxxxxx.supabase.co
   ```

3. **SUPABASE_SERVICE_KEY**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...
   ```

4. **PRIME_SYNC_API_TOKEN**
   ```
   [gere um token seguro - veja SECRETS.md]
   ```

### 2.2 Deploy Stack

1. Portainer → **Stacks** → **+ Add stack**
2. **Name**: `prime-sync-api`
3. **Build method**: Web editor
4. Cole o conteúdo de `stack-portainer.yml`
5. **Deploy the stack**

⏳ Aguarde ~30 segundos para o container iniciar.

### 2.3 Verificar Deploy

```bash
# Ver container rodando
docker ps | grep prime-sync

# Ver logs
docker logs prime-sync-api -f
```

**Deve mostrar:**
```
[2025-10-23 10:00:00] INFO - Starting gunicorn 21.2.0
[2025-10-23 10:00:00] INFO - Listening at: http://0.0.0.0:5000
[2025-10-23 10:00:00] INFO - Using worker: sync
[2025-10-23 10:00:00] INFO - Booting worker with pid: 7
```

---

## PARTE 3: Testar API (2 min)

### 3.1 Health Check

```bash
curl https://sincro.oficialmed.com.br/health
```

**Esperado:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T10:00:00.000000",
  "version": "1.0.0"
}
```

### 3.2 Sync Manual

```bash
curl -X POST https://sincro.oficialmed.com.br/sync \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Esperado:**
```json
{
  "sucesso": true,
  "timestamp": "2025-10-23T10:00:00.000000",
  "tempo_execucao_segundos": 2.5,
  "clientes": {
    "inseridos": 5,
    "mensagem": "5 clientes novos sincronizados"
  },
  "pedidos": {
    "inseridos": 3,
    "mensagem": "3 pedidos novos sincronizados"
  },
  "total_inseridos": 8
}
```

---

## PARTE 4: Setup Supabase Cronjob (3 min)

### 4.1 Executar SQL

1. Supabase Dashboard → **SQL Editor**
2. Abra o arquivo `supabase-cronjob.sql`
3. **Cole todo o conteúdo**
4. Clique em **Run**

⚠️ **IMPORTANTE**: Atualize a URL e o token no SQL:

```sql
-- Linha 22: Atualizar URL
v_url := 'https://sincro.oficialmed.com.br/sync';

-- Linha 30: Atualizar token
http_header('Authorization', 'Bearer SEU_TOKEN_AQUI')
```

### 4.2 Verificar Cronjob

```sql
-- Ver jobs agendados
SELECT * FROM cron.job;
```

**Esperado:**
```
jobid | jobname                          | schedule      | active
------|----------------------------------|---------------|-------
1     | sync-prime-incremental-15min     | */15 * * * *  | t
```

### 4.3 Teste Manual

```sql
-- Executar sincronização manualmente
SELECT api.sync_prime_with_log();
```

### 4.4 Ver Logs

```sql
-- Ver últimos logs
SELECT
  timestamp,
  sucesso,
  total_inseridos,
  resultado->>'tempo_execucao_segundos' as tempo_seg,
  erro
FROM api.sync_logs
ORDER BY timestamp DESC
LIMIT 10;
```

---

## PARTE 5: Monitoramento (Opcional)

### Dashboard Supabase (últimas 24h)

```sql
SELECT
  date_trunc('hour', timestamp) as hora,
  COUNT(*) as execucoes,
  SUM(CASE WHEN sucesso THEN 1 ELSE 0 END) as sucessos,
  SUM(total_inseridos) as total_inseridos,
  ROUND(AVG((resultado->>'tempo_execucao_segundos')::numeric), 2) as tempo_medio
FROM api.sync_logs
WHERE timestamp >= now() - interval '24 hours'
GROUP BY date_trunc('hour', timestamp)
ORDER BY hora DESC;
```

### Alertas (Opcional)

Criar alerta se taxa de sucesso < 90% (usar Supabase Webhooks ou outro serviço)

---

## PARTE 6: Atualizar Código (Futuro)

### Quando precisar fazer mudanças:

```bash
# 1. Editar código localmente
code app.py

# 2. Commit e push
git add .
git commit -m "feat: adicionar nova funcionalidade"
git push

# 3. GitHub Actions faz build automaticamente
# Acompanhe em: https://github.com/oficialmedpro/prime-sync-api/actions

# 4. Atualizar container no Portainer
# Opção A: Via Portainer UI
Portainer → Stacks → prime-sync-api → Update the stack → Pull latest image

# Opção B: Via CLI
docker service update --image oficialmedpro/prime-sync-api:latest prime-sync-api_prime-sync-api
```

---

## Checklist Final

### GitHub
- [ ] Repositório criado
- [ ] Secret `DOCKER_HUB_TOKEN` configurado
- [ ] Código commitado e pushed
- [ ] GitHub Actions executou com sucesso
- [ ] Imagem disponível no Docker Hub

### Portainer
- [ ] 4 secrets criados
- [ ] Stack `prime-sync-api` deployada
- [ ] Container rodando
- [ ] Logs sem erros

### API
- [ ] Health check responde: `https://sincro.oficialmed.com.br/health`
- [ ] Sync manual funciona: `POST /sync`
- [ ] Retorna dados corretos

### Supabase
- [ ] SQL executado com sucesso
- [ ] Cronjob criado (visualizar em `cron.job`)
- [ ] Teste manual funcionou
- [ ] Logs sendo salvos em `api.sync_logs`

### DNS/Traefik
- [ ] Domínio `sincro.oficialmed.com.br` aponta para servidor
- [ ] HTTPS funcionando (certificado Let's Encrypt)
- [ ] Redirecionamento HTTP → HTTPS funcionando

---

## Troubleshooting

### Container não inicia
```bash
# Ver logs
docker logs prime-sync-api

# Verificar secrets
docker secret ls

# Verificar stack
docker stack ps prime-sync-api --no-trunc
```

### Erro 502 Bad Gateway
```bash
# Verificar se container está rodando
docker ps | grep prime-sync

# Verificar porta
netstat -tulpn | grep 5000

# Verificar logs do Traefik
docker logs traefik
```

### Cronjob não executa
```sql
-- Ver erros do cronjob
SELECT * FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname LIKE '%sync-prime%')
ORDER BY start_time DESC LIMIT 5;
```

### Dados não sincronizam
```bash
# Testar conexão Firebird
docker exec -it prime-sync-api python -c "import fdb; print('OK')"

# Testar conexão Supabase
curl -H "apikey: SUA_KEY" https://SEU_PROJETO.supabase.co/rest/v1/
```

---

## Suporte

**Documentação:**
- `README.md` - Documentação completa
- `GUIA_RAPIDO.md` - Guia rápido de 5 minutos
- `ESTRUTURA.md` - Arquitetura e estrutura
- `SECRETS.md` - Detalhes dos secrets

**Logs:**
- Container: `docker logs prime-sync-api -f`
- Supabase: `SELECT * FROM api.sync_logs ORDER BY timestamp DESC;`

**Endpoints:**
- Health: `https://sincro.oficialmed.com.br/health`
- Sync: `https://sincro.oficialmed.com.br/sync`

---

**Criado**: 23/10/2025
**Versão**: 1.0.0
**Tempo estimado**: ~20 minutos
**Autor**: Claude Code
