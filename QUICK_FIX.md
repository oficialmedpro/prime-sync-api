# ⚡ Quick Fix - Sincronização de Clientes

**⏱️ 5 minutos** | **🎯 Corrigir registro corrompido**

---

## 1️⃣ Supabase SQL Editor

https://supabase.com/dashboard → SQL Editor → New query

### Paste e Execute:

```sql
-- Deletar registro corrompido
DELETE FROM api.prime_clientes WHERE codigo_cliente_original = 9999999;

-- Remover duplicatas em tipos
WITH duplicados AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY codigo_tipo_original ORDER BY created_at) as rn
    FROM api.prime_tipos_processo
)
DELETE FROM api.prime_tipos_processo WHERE id IN (SELECT id FROM duplicados WHERE rn > 1);

-- Verificar correção
SELECT 
    'prime_clientes' as tabela,
    MAX(codigo_cliente_original) as ultimo_codigo,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as ultima_hora
FROM api.prime_clientes

UNION ALL

SELECT 
    'prime_tipos_processo',
    MAX(codigo_tipo_original),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour')
FROM api.prime_tipos_processo;
```

**✅ Resultado esperado:**
- `prime_clientes.ultimo_codigo` < 100000
- Sem erros ao executar

---

## 2️⃣ Reiniciar Serviço

### Via Portainer:
https://portainer.oficialmed.com.br

**Stacks** → **prime-sync-api** → **Editor** → **Update the stack** (botão azul no final)

### Ou via SSH:
```bash
docker service update --force prime-sync-api_prime-sync-api
```

---

## 3️⃣ Verificar Logs (2 min depois)

### Via Portainer:
**Containers** → `prime-sync-api_...` → **Logs**

### Ou via SSH:
```bash
docker service logs prime-sync-api_prime-sync-api --tail 50
```

### Procure por:
```
✅ Encontrados X clientes novos
📋 Clientes: {'inseridos': X, 'mensagem': 'X clientes sincronizados'}
```

---

## ✅ Done!

Se ver `inseridos > 0` → **Problema resolvido!** 🎉

Se ainda mostrar `inseridos: 0` → Consulte `PASSO_A_PASSO_CORRECAO.md`

---

## 📊 Monitorar (1x por semana)

```sql
SELECT 
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h
FROM api.prime_clientes;
```

Se `ultimas_24h = 0` → Há problema!

---

**Docs completas:** `INSTRUCOES_CORRECAO.md` | `PASSO_A_PASSO_CORRECAO.md`

