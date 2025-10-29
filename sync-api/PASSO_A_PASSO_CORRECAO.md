# ✅ Passo a Passo: Corrigir Sincronização de Clientes

**Data:** 27/10/2025  
**Tempo Estimado:** 10 minutos  
**Dificuldade:** ⭐⭐☆☆☆ (Fácil)

---

## 🎯 O que vamos fazer?

Corrigir o problema que impede `prime_clientes` de sincronizar há 4 dias, causado por um registro com código 9999999.

---

## 📋 PASSO 1: Validar o Problema (OPCIONAL)

### Opção A: Script Python (Recomendado)

```bash
cd "C:\Banco de Dados Prime\sync-api"

# Configurar variáveis de ambiente
$env:SUPABASE_URL="https://[seu-projeto].supabase.co"
$env:SUPABASE_KEY="sua-service-role-key-aqui"

# Executar teste
python testar_correcao_local.py
```

**Resultado esperado:**
```
❌ Registros corrompidos: ENCONTRADOS
   → ID: 12345, Código: 9999999, Nome: [algum nome]
```

### Opção B: Query SQL no Supabase

1. Acesse: https://supabase.com/dashboard
2. Projeto → SQL Editor → New query
3. Execute:

```sql
SELECT codigo_cliente_original, nome, created_at 
FROM api.prime_clientes 
WHERE codigo_cliente_original > 500000
ORDER BY codigo_cliente_original DESC;
```

**Se retornar registros:** Precisa corrigir! ✅ Prossiga  
**Se retornar vazio:** Problema já foi corrigido ✅

---

## 🔧 PASSO 2: Executar Correção no Supabase

### 2.1 - Acessar SQL Editor

1. Acesse: https://supabase.com/dashboard
2. Selecione seu projeto
3. Menu lateral: **SQL Editor**
4. Clique em: **New query**

### 2.2 - Executar Script de Clientes

Copie e cole TODO o conteúdo de: `corrigir_cliente_corrompido.sql`

Ou execute manualmente:

```sql
-- 1. Verificar o problema
SELECT codigo_cliente_original, nome, created_at 
FROM api.prime_clientes 
WHERE codigo_cliente_original > 500000;

-- 2. Deletar registro corrompido
DELETE FROM api.prime_clientes
WHERE codigo_cliente_original = 9999999;

-- 3. Confirmar correção
SELECT MAX(codigo_cliente_original) as ultimo_codigo_real
FROM api.prime_clientes;
```

**Clique em:** RUN (ou Ctrl+Enter)

**Resultado esperado:**
```
ultimo_codigo_real
------------------
45678  (ou similar, mas < 100000)
```

### 2.3 - Executar Script de Tipos de Processo

Copie e cole TODO o conteúdo de: `corrigir_tipos_processo_duplicados.sql`

Ou execute manualmente:

```sql
-- 1. Verificar duplicatas
SELECT codigo_tipo_original, COUNT(*) as quantidade
FROM api.prime_tipos_processo
GROUP BY codigo_tipo_original
HAVING COUNT(*) > 1;

-- 2. Remover duplicatas (mantém o mais antigo)
WITH duplicados AS (
    SELECT 
        id,
        ROW_NUMBER() OVER (PARTITION BY codigo_tipo_original ORDER BY created_at ASC) as rn
    FROM api.prime_tipos_processo
)
DELETE FROM api.prime_tipos_processo
WHERE id IN (SELECT id FROM duplicados WHERE rn > 1);

-- 3. Confirmar correção
SELECT COUNT(*) as total_tipos, COUNT(DISTINCT codigo_tipo_original) as tipos_unicos
FROM api.prime_tipos_processo;
```

**Resultado esperado:**
```
total_tipos | tipos_unicos
------------|-------------
9           | 9
```

(Ambos devem ser iguais = sem duplicatas)

---

## 🔄 PASSO 3: Reiniciar o Serviço

### Opção A: Via Portainer (Recomendado)

1. Acesse: https://portainer.oficialmed.com.br
2. Login com suas credenciais
3. Navegue: **Home** → **Stacks** → **prime-sync-api**
4. Clique no botão azul: **📝 Editor**
5. Não altere nada! Apenas role até o final
6. Clique em: **🔄 Update the stack**
7. Aguarde ~30 segundos (status: Running ✅)

### Opção B: Via SSH/Docker

```bash
# Conectar no servidor
ssh usuario@seu-servidor

# Reiniciar o serviço (força recriação)
docker service update --force prime-sync-api_prime-sync-api

# Verificar status
docker service ps prime-sync-api_prime-sync-api
```

**Resultado esperado:**
```
NAME                           CURRENT STATE
prime-sync-api_prime-sync-api  Running (menos de 1 minuto atrás)
```

---

## ✅ PASSO 4: Verificar Correção

### 4.1 - Aguardar Execução do Cronjob

**O cronjob roda a cada 30 minutos.**

Aguarde 1-2 minutos para garantir que executou pelo menos 1 vez.

### 4.2 - Verificar Logs

#### Via Portainer:
1. Portainer → **Containers**
2. Localize: `prime-sync-api_prime-sync-api.X.xxxxx`
3. Clique nele → **Logs**
4. Role até encontrar a última execução

#### Via SSH:
```bash
docker service logs prime-sync-api_prime-sync-api --tail 100 --follow
```

### 4.3 - Buscar no Log

Procure por estas linhas (CTRL+F):

**ANTES da correção (problema):**
```
📊 Clientes - Último código: 9999999
📋 Clientes: {'inseridos': 0, 'mensagem': 'Nenhum cliente novo'}
```

**DEPOIS da correção (sucesso):**
```
📊 Clientes - Último código: 45678  ← Código normal!
✅ Encontrados 15 clientes novos
📋 Clientes: {'inseridos': 15, 'mensagem': '15 clientes sincronizados'}
```

Se vir `inseridos: X` onde X > 0 → **Sucesso!** ✅

### 4.4 - Verificar no Supabase

Execute no SQL Editor:

```sql
SELECT 
    COUNT(*) as total_clientes,
    MAX(codigo_cliente_original) as ultimo_codigo,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as ultima_hora,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h
FROM api.prime_clientes;
```

**Resultado esperado:**
```
total_clientes | ultimo_codigo | ultima_insercao       | ultima_hora | ultimas_24h
---------------|---------------|-----------------------|-------------|------------
12,450         | 45678         | 2025-10-27 18:30:15   | 5           | 120
```

✅ `ultima_hora > 0` → Está sincronizando!  
✅ `ultimo_codigo < 100000` → Código normal!

---

## 📊 PASSO 5: Monitoramento Contínuo

### Dashboard Completo

Execute no Supabase SQL Editor: `verificar_todas_tabelas.sql`

Ou manualmente:

```sql
SELECT 
    'prime_clientes' as tabela,
    COUNT(*) as total,
    MAX(created_at) as ultima_sync,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    CASE 
        WHEN MAX(created_at) > NOW() - INTERVAL '2 hours' THEN '🟢 OK'
        ELSE '🔴 PROBLEMA'
    END as status
FROM api.prime_clientes

UNION ALL

SELECT 
    'prime_pedidos',
    COUNT(*),
    MAX(created_at),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
    CASE 
        WHEN MAX(created_at) > NOW() - INTERVAL '2 hours' THEN '🟢 OK'
        ELSE '🔴 PROBLEMA'
    END
FROM api.prime_pedidos

UNION ALL

SELECT 
    'prime_rastreabilidade',
    COUNT(*),
    MAX(created_at),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
    CASE 
        WHEN MAX(created_at) > NOW() - INTERVAL '2 hours' THEN '🟢 OK'
        ELSE '🔴 PROBLEMA'
    END
FROM api.prime_rastreabilidade;
```

**Execute esta query 1x por semana** para garantir que tudo está OK.

---

## 🐛 Troubleshooting

### ❌ Problema: Ainda mostra último código 9999999

**Causa:** Script SQL não foi executado ou não funcionou

**Solução:**
1. Volte ao Supabase SQL Editor
2. Execute novamente:
```sql
DELETE FROM api.prime_clientes WHERE codigo_cliente_original > 500000;
```
3. Confirme: `SELECT MAX(codigo_cliente_original) FROM api.prime_clientes;`
4. Reinicie o serviço novamente

---

### ❌ Problema: Logs mostram "inseridos: 0"

**Possíveis causas:**

**A) Não há clientes novos no Firebird**
- Execute no Firebird/Prime:
```sql
SELECT MAX(CODIGO) FROM CLIENTE WHERE ATIVO = -1;
```
- Compare com o último código no Supabase
- Se forem iguais → Realmente não há clientes novos ✅

**B) Erro de conexão com Firebird**
- Verifique logs por: `grep "ERROR" logs`
- Verifique se secrets estão corretos no Portainer

**C) Problema com permissões no Supabase**
- Execute:
```sql
GRANT ALL ON api.prime_clientes TO authenticated;
GRANT ALL ON api.prime_clientes TO service_role;
```

---

### ❌ Problema: HTTP 409 continua em tipos_processo

**Solução drástica (resetar tabela):**

```sql
-- CUIDADO: Deleta TUDO!
TRUNCATE api.prime_tipos_processo RESTART IDENTITY CASCADE;

-- A próxima sincronização vai recriar todos os registros
```

Aguarde 2 minutos e verifique logs.

---

### ❌ Problema: Endpoint /sync não responde

**Verificar se o container está rodando:**
```bash
docker service ps prime-sync-api_prime-sync-api
```

**Se mostrar "Failed":**
```bash
# Ver logs de erro
docker service logs prime-sync-api_prime-sync-api --tail 200

# Reiniciar
docker service update --force prime-sync-api_prime-sync-api
```

---

## 📞 Suporte

### Arquivos de Referência:

| Documento | Quando usar |
|-----------|-------------|
| `INSTRUCOES_CORRECAO.md` | Instruções detalhadas + troubleshooting |
| `RESUMO_DIAGNOSTICO_27-10-2025.md` | Análise técnica completa |
| `LISTA_ARQUIVOS_PROJETO.md` | Índice de todos os arquivos |
| `corrigir_cliente_corrompido.sql` | Script SQL para clientes |
| `corrigir_tipos_processo_duplicados.sql` | Script SQL para tipos |
| `verificar_todas_tabelas.sql` | Dashboard de monitoramento |
| `testar_correcao_local.py` | Teste automatizado Python |

### Comandos Úteis:

```bash
# Ver logs em tempo real
docker service logs prime-sync-api_prime-sync-api --follow

# Ver últimos 200 logs
docker service logs prime-sync-api_prime-sync-api --tail 200

# Filtrar apenas erros
docker service logs prime-sync-api_prime-sync-api | grep ERROR

# Testar endpoint manualmente
curl https://sincro.oficialmed.com.br/sync
```

---

## ✅ Checklist Final

- [ ] Executei script SQL de clientes no Supabase
- [ ] Confirmei que último código é < 100000
- [ ] Executei script SQL de tipos_processo no Supabase
- [ ] Confirmei que não há duplicatas
- [ ] Reiniciei o serviço via Portainer ou Docker
- [ ] Aguardei 2 minutos para cronjob executar
- [ ] Verifiquei logs e encontrei "clientes sincronizados"
- [ ] Executei query de verificação e confirmei registros na última hora
- [ ] Salvei este documento para referência futura
- [ ] 🎉 **PROBLEMA RESOLVIDO!**

---

**🎯 Após completar todos os passos, a sincronização deve estar funcionando normalmente!**

**Tempo total:** ~10 minutos  
**Próxima verificação:** Em 24 horas (executar `verificar_todas_tabelas.sql`)

---

_Dúvidas? Consulte `INSTRUCOES_CORRECAO.md` ou `RESUMO_DIAGNOSTICO_27-10-2025.md`_




