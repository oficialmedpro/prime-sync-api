-- ============================================================================
-- SCRIPT: Corrigir duplicatas em prime_tipos_processo
-- DATA: 27/10/2025
-- PROBLEMA: HTTP 409 ao tentar inserir tipos duplicados
-- ============================================================================

-- 1️⃣ VERIFICAR se há duplicatas (mesmos código_tipo_original)
SELECT 
    codigo_tipo_original,
    COUNT(*) as quantidade,
    array_agg(id ORDER BY created_at) as ids_duplicados,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao
FROM api.prime_tipos_processo
GROUP BY codigo_tipo_original
HAVING COUNT(*) > 1
ORDER BY codigo_tipo_original;

-- 2️⃣ VERIFICAR todos os tipos cadastrados
SELECT 
    id,
    codigo_tipo_original,
    nome_processo,
    nome_ficha,
    sequencia,
    ativo,
    created_at,
    updated_at
FROM api.prime_tipos_processo
ORDER BY codigo_tipo_original;

-- 3️⃣ DELETAR registros duplicados (mantém apenas o mais antigo)
WITH duplicados AS (
    SELECT 
        id,
        codigo_tipo_original,
        ROW_NUMBER() OVER (PARTITION BY codigo_tipo_original ORDER BY created_at ASC) as rn
    FROM api.prime_tipos_processo
)
DELETE FROM api.prime_tipos_processo
WHERE id IN (
    SELECT id FROM duplicados WHERE rn > 1
);

-- 4️⃣ VERIFICAR o último código processado
SELECT 
    MAX(codigo_tipo_original) as ultimo_codigo,
    COUNT(*) as total_tipos,
    COUNT(DISTINCT codigo_tipo_original) as tipos_unicos
FROM api.prime_tipos_processo;

-- 5️⃣ OPCIONAL: Se quiser RESETAR a tabela e sincronizar do zero
-- CUIDADO: Isso vai deletar TODOS os tipos e a próxima sincronização vai recriar tudo
-- Descomente apenas se necessário:
-- TRUNCATE api.prime_tipos_processo RESTART IDENTITY CASCADE;

-- ============================================================================
-- EXPLICAÇÃO DO ERRO HTTP 409:
-- O script estava buscando tipos com CODIGO > ultimo_codigo
-- Mas estava retornando 0 como último código (linha 693 do app.py)
-- Isso fazia buscar TODOS os tipos novamente, causando duplicatas
-- ============================================================================

-- 6️⃣ VERIFICAR a constraint de unicidade
SELECT
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'api.prime_tipos_processo'::regclass
AND contype IN ('u', 'p');  -- u = unique, p = primary key

-- ============================================================================
-- APÓS EXECUTAR ESTE SCRIPT:
-- 1. Execute: docker service update --force prime-sync-api_prime-sync-api
-- 2. Verifique os logs para confirmar que não há mais erro 409
-- ============================================================================



