# 🔧 Instruções para Corrigir Sincronização de Clientes

**Data:** 27/10/2025  
**Problema:** Registro corrompido com `codigo_cliente_original = 9999999` impedindo sincronização

---

## 📋 Problema Identificado

### ❌ O que estava acontecendo:
- **prime_clientes** NÃO sincronizava (última inserção: 22/10/2025)
- **prime_tipos_processo** erro HTTP 409 (duplicatas)
- Logs mostravam: `📊 Clientes - Último código: 9999999`

### 🔍 Causa Raiz:
1. **Clientes:** Registro com código 9999999 no Supabase (valor absurdo)
2. **Tipos:** Tentativa de reinserir registros duplicados

---

## ✅ Solução Passo a Passo

### **1️⃣ Acessar o Supabase SQL Editor**
- URL: https://supabase.com/dashboard/project/[seu-projeto]/sql
- Ou: Dashboard → SQL Editor

### **2️⃣ Executar correção de CLIENTES**

Copie e execute o conteúdo de: `corrigir_cliente_corrompido.sql`

```sql
-- Verificar o problema
SELECT codigo_cliente_original, nome, created_at 
FROM api.prime_clientes 
WHERE codigo_cliente_original > 500000;

-- Deletar registro corrompido
DELETE FROM api.prime_clientes
WHERE codigo_cliente_original = 9999999;

-- Confirmar correção
SELECT MAX(codigo_cliente_original) FROM api.prime_clientes;
```

**Resultado esperado:** Deve retornar um código normal (ex: 45678)

---

### **3️⃣ Executar correção de TIPOS_PROCESSO**

Copie e execute o conteúdo de: `corrigir_tipos_processo_duplicados.sql`

```sql
-- Verificar duplicatas
SELECT codigo_tipo_original, COUNT(*) 
FROM api.prime_tipos_processo 
GROUP BY codigo_tipo_original 
HAVING COUNT(*) > 1;

-- Deletar duplicatas (mantém apenas o mais antigo)
WITH duplicados AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY codigo_tipo_original ORDER BY created_at) as rn
    FROM api.prime_tipos_processo
)
DELETE FROM api.prime_tipos_processo
WHERE id IN (SELECT id FROM duplicados WHERE rn > 1);
```

---

### **4️⃣ Reiniciar o serviço no servidor**

**Opção A - Via Portainer (Recomendado):**
1. Acesse: https://portainer.oficialmed.com.br
2. Navegue até: Stacks → prime-sync-api
3. Clique em: **Update the stack** (botão azul)
4. Role até o final e clique: **Update the stack**
5. Aguarde o container reiniciar (~30 segundos)

**Opção B - Via SSH:**
```bash
# Conectar no servidor
ssh usuario@seu-servidor

# Reiniciar o serviço
docker service update --force prime-sync-api_prime-sync-api

# Verificar status
docker service ps prime-sync-api_prime-sync-api
```

---

### **5️⃣ Verificar se funcionou**

**A) Verificar logs (aguardar 1-2 minutos para o cronjob rodar):**
```bash
docker service logs prime-sync-api_prime-sync-api --tail 100 --follow
```

**Ou via Portainer:**
- Containers → prime-sync-api → Logs

**B) Buscar no log:**
```
✅ Encontrados X clientes novos
📋 Clientes: {'inseridos': X, 'mensagem': 'X clientes sincronizados'}
```

**C) Executar query de verificação no Supabase:**
```sql
-- Script: verificar_todas_tabelas.sql
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h
FROM api.prime_clientes;
```

**Resultado esperado:** `ultimas_24h > 0` ✅

---

## 📊 Monitoramento Contínuo

### **Criar alerta de sincronização**

Execute no Supabase para criar uma view de monitoramento:

```sql
CREATE OR REPLACE VIEW api.monitor_sincronizacao AS
SELECT 
    'prime_clientes' as tabela,
    MAX(created_at) as ultima_sincronizacao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    CASE 
        WHEN MAX(created_at) < NOW() - INTERVAL '2 hours' THEN '🔴 ALERTA'
        WHEN MAX(created_at) < NOW() - INTERVAL '1 hour' THEN '🟡 ATENÇÃO'
        ELSE '🟢 OK'
    END as status
FROM api.prime_clientes

UNION ALL

SELECT 
    'prime_pedidos',
    MAX(created_at),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
    CASE 
        WHEN MAX(created_at) < NOW() - INTERVAL '2 hours' THEN '🔴 ALERTA'
        WHEN MAX(created_at) < NOW() - INTERVAL '1 hour' THEN '🟡 ATENÇÃO'
        ELSE '🟢 OK'
    END
FROM api.prime_pedidos

UNION ALL

SELECT 
    'prime_rastreabilidade',
    MAX(created_at),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
    CASE 
        WHEN MAX(created_at) < NOW() - INTERVAL '2 hours' THEN '🔴 ALERTA'
        WHEN MAX(created_at) < NOW() - INTERVAL '1 hour' THEN '🟡 ATENÇÃO'
        ELSE '🟢 OK'
    END
FROM api.prime_rastreabilidade;

-- Consultar status
SELECT * FROM api.monitor_sincronizacao;
```

---

## 🐛 Troubleshooting

### **Problema: Ainda não sincroniza após correção**

1. **Verificar logs de erro:**
```bash
docker service logs prime-sync-api_prime-sync-api --tail 200 | grep ERROR
```

2. **Testar manualmente o endpoint:**
```bash
curl -X POST https://sincro.oficialmed.com.br/sync
```

3. **Verificar conectividade com Firebird:**
```bash
# No servidor
docker exec -it $(docker ps -q -f name=prime-sync) python -c "import fdb; print('OK')"
```

### **Problema: HTTP 409 continua em tipos_processo**

Execute no Supabase:
```sql
-- Resetar completamente a tabela
TRUNCATE api.prime_tipos_processo RESTART IDENTITY CASCADE;

-- Aguardar próxima sincronização (vai recriar tudo)
```

### **Problema: Erro de timeout**

Aumentar timeout no `app.py` (necessário rebuild):
```python
# Linha 82, 241, etc
timeout=30  # aumentar para 60
```

---

## 📝 Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `corrigir_cliente_corrompido.sql` | Script para deletar registro com código 9999999 |
| `corrigir_tipos_processo_duplicados.sql` | Script para remover duplicatas |
| `verificar_todas_tabelas.sql` | Query completa de status de sincronização |
| `INSTRUCOES_CORRECAO.md` | Este arquivo (documentação) |

---

## ✅ Checklist Final

- [ ] Executei `corrigir_cliente_corrompido.sql` no Supabase
- [ ] Executei `corrigir_tipos_processo_duplicados.sql` no Supabase
- [ ] Reiniciei o serviço via Portainer ou Docker
- [ ] Aguardei 2 minutos para o cronjob rodar
- [ ] Verifiquei os logs e vi "clientes sincronizados"
- [ ] Executei `verificar_todas_tabelas.sql` e confirmei registros nas últimas 24h
- [ ] Documentei a correção (data/hora/resultado)

---

**🎯 Após seguir todos os passos, a sincronização deve voltar ao normal!**

**Dúvidas?** Consulte os logs ou entre em contato com o suporte.



