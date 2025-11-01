# 🚀 GUIA RÁPIDO - DEPLOY NO PORTAINER

**Data:** 01/11/2025  
**Versão:** 2.0.1  
**Commit:** `b3ebc8a`  
**Status:** ✅ Pronto para deploy

---

## 📋 Passos para Deploy

### 1. **No Portainer**

1. Acesse o Portainer
2. Vá em **Stacks** → Procure por `prime-sync-api`
3. Clique no stack

### 2. **Atualizar Imagem**

**Opção A: GitHub Container Registry (Recomendado)**

1. No editor do `docker-compose.yml`, procure por:
   ```yaml
   prime-sync-api:
     build: .
   ```

2. Substitua por:
   ```yaml
   prime-sync-api:
     image: ghcr.io/oficialmedpro/prime-sync-api:latest
   ```

**Opção B: Rebuild Local**

1. Se você usa `build: .`, clique em **Editor**
2. Salve qualquer alteração pequena no `docker-compose.yml`
3. Clique em **Update the stack**

### 3. **Recreate Container**

1. Clique no nome do container: `prime-sync-api`
2. Clique em **Recreate** 🔄
3. Marque a opção: **Pull latest image**
4. Confirme

### 4. **Verificar Logs**

1. Clique em **Logs** no container
2. Procure por: `version: 2.0.1`
3. Deve mostrar: `✅ SINCRONIZAÇÃO INCREMENTAL V2.0 - COM AUDITORIA`

---

## 🧪 Teste Após Deploy

### 1. Health Check

```bash
curl https://beta.oficialmed.com.br/health
# ou
curl https://bi.oficialmed.com.br/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-29T12:00:00",
  "version": "2.0.1"
}
```

### 2. Verificar Sincronização Automática

A sincronização roda automaticamente a cada **15 minutos** via cron do Supabase.

Você pode testar manualmente:

```bash
curl -X POST https://beta.oficialmed.com.br/sync \
  -H "Content-Type: application/json"
```

---

## 🎯 Verificar Novos Recursos

### Logs Melhorados

Após o deploy, os logs devem mostrar:

```
======================================================================
🚀 SINCRONIZAÇÃO INCREMENTAL V2.0 - COM AUDITORIA
======================================================================

======================================================================
1️⃣ SINCRONIZANDO CLIENTES (ordem: 1/6)
======================================================================
📊 Clientes - Último código: 37484
✅ Encontrados 5 clientes novos

======================================================================
2️⃣ SINCRONIZANDO PEDIDOS (ordem: 2/6)
======================================================================
📊 Pedidos - Último código: 17646
✅ Encontrados 3 pedidos novos
```

### Tratamento de Erros

Se houver erro em uma etapa, a sincronização **continua**:

```
⚠️ Erro em pedidos (continuando): HTTP 429
⚠️ CONCLUÍDO COM AVISOS - Total: 5 registros em 2.5s
   Avisos: 1 tabela(s) com problemas
```

---

## ⚠️ Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker logs prime-sync-api
```

### Erro de conexão Firebird

Verifique variáveis de ambiente no Portainer:
- `FIREBIRD_HOST`
- `FIREBIRD_DB`
- `FIREBIRD_USER`
- `FIREBIRD_PASS`

### Health check falhando

Verifique se:
- Porta 5000 está exposta
- Firewall permite conexão
- Traefik está configurado corretamente

---

## 📊 Monitoramento

### Ver última sincronização

```bash
curl https://beta.oficialmed.com.br/auditoria/historico?limite=1
```

### Verificar integridade

```bash
curl https://beta.oficialmed.com.br/auditoria/verificar
```

---

## ✅ Checklist Pós-Deploy

- [ ] Container rodando (green no Portainer)
- [ ] Health check retorna 200
- [ ] Logs mostram versão 2.0.1
- [ ] Sem erros nos primeiros 10 minutos
- [ ] Primeira sincronização automática concluída

---

**Última atualização:** 29/10/2025  
**Próxima revisão:** Acompanhar logs por 24h


