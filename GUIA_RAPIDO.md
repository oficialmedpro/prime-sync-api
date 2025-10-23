# 🚀 GUIA RÁPIDO DE DEPLOY - 5 MINUTOS

## Passo 1: Preparar Arquivos (1 min)

Copie a pasta `sync-api` completa para o servidor onde está o Portainer.

```bash
# Via SCP/SFTP
scp -r sync-api/ usuario@servidor:/home/usuario/

# Ou via Git
cd /home/usuario
git clone seu-repo.git sync-api
```

---

## Passo 2: Deploy no Portainer (2 min)

1. Acesse Portainer: `https://seu-servidor:9443`
2. Vá em **Stacks** → **+ Add stack**
3. Nome: `prime-sync-api`
4. Build method: **Web editor**
5. Cole o conteúdo do arquivo `docker-compose.yml`
6. Clique em **Deploy the stack**

**Pronto!** Container está rodando.

---

## Passo 3: Verificar se Funciona (1 min)

```bash
# Health check
curl https://beta.oficialmed.com.br/health

# Deve retornar:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

---

## Passo 4: Configurar Cronjob no Supabase (1 min)

1. Acesse Supabase Dashboard
2. Vá em **SQL Editor**
3. Cole e execute o conteúdo do arquivo `supabase-cronjob.sql`
4. Aguarde mensagem de sucesso

**Pronto!** Sincronização automática configurada.

---

## Passo 5: Testar Manualmente (30 seg)

```bash
# Executar sincronização manual
curl -X POST https://beta.oficialmed.com.br/sync \
  -H "Authorization: Bearer prime-sync-2025"

# Deve retornar algo como:
# {
#   "sucesso": true,
#   "total_inseridos": 5,
#   "clientes": {"inseridos": 3},
#   "pedidos": {"inseridos": 2}
# }
```

---

## ✅ PRONTO!

Agora a sincronização roda automaticamente a cada 15 minutos!

---

## 🔍 Monitorar

### Ver logs do container:
```bash
docker logs prime-sync-api -f
```

### Ver logs no Supabase:
```sql
SELECT * FROM api.sync_logs ORDER BY timestamp DESC LIMIT 10;
```

### Ver cronjobs agendados:
```sql
SELECT * FROM cron.job;
```

---

## 🐛 Troubleshooting Rápido

### Container não inicia?
```bash
docker ps -a | grep prime-sync
docker logs prime-sync-api
```

### API não responde?
```bash
# Verificar porta
netstat -tulpn | grep 5000

# Reiniciar container
docker restart prime-sync-api
```

### Cronjob não executa?
```sql
-- Ver erros
SELECT * FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname LIKE '%sync-prime%')
ORDER BY start_time DESC LIMIT 5;
```

---

## 📞 Endpoints

- **Health**: `GET https://beta.oficialmed.com.br/health`
- **Sync**: `POST https://beta.oficialmed.com.br/sync`
- **Fallback**: `https://bi.oficialmed.com.br/*`

---

**Tempo total**: ~5 minutos
**Frequência**: A cada 15 minutos
**Performance**: ~100-500 registros/segundo
