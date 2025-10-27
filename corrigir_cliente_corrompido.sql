-- ============================================================================
-- SCRIPT: Corrigir registro corrompido em prime_clientes
-- DATA: 27/10/2025
-- PROBLEMA: Registro com codigo_cliente_original = 9999999 impedindo sincronização
-- ============================================================================

-- 1️⃣ VERIFICAR registros suspeitos (códigos muito altos)
SELECT 
    id,
    codigo_cliente_original,
    nome,
    cpf_cnpj,
    created_at,
    updated_at
FROM api.prime_clientes
WHERE codigo_cliente_original > 500000  -- Códigos acima de 500k são suspeitos
ORDER BY codigo_cliente_original DESC;

-- 2️⃣ VERIFICAR o último código REAL (antes do corrompido)
SELECT 
    codigo_cliente_original,
    nome,
    cpf_cnpj,
    created_at
FROM api.prime_clientes
WHERE codigo_cliente_original < 500000  -- Códigos normais
ORDER BY codigo_cliente_original DESC
LIMIT 10;

-- 3️⃣ DELETAR o registro corrompido com código 9999999
DELETE FROM api.prime_clientes
WHERE codigo_cliente_original = 9999999;

-- 4️⃣ DELETAR outros registros suspeitos (se houver)
-- Descomente se encontrar outros códigos absurdos
-- DELETE FROM api.prime_clientes
-- WHERE codigo_cliente_original > 500000;

-- 5️⃣ VERIFICAR a correção
SELECT 
    MAX(codigo_cliente_original) as ultimo_codigo_real,
    COUNT(*) as total_clientes
FROM api.prime_clientes;

-- ============================================================================
-- APÓS EXECUTAR ESTE SCRIPT:
-- 1. Execute: docker service update --force prime-sync-api_prime-sync-api
-- 2. Aguarde 1 minuto para o cronjob rodar
-- 3. Verifique os logs: docker service logs prime-sync-api_prime-sync-api --tail 100
-- ============================================================================

