-- ============================================================================
-- VERIFICAR CAMPOS DA TABELA prime_clientes
-- Execute no Supabase SQL Editor
-- ============================================================================

-- 1. Ver estrutura completa da tabela
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'api'
AND table_name = 'prime_clientes'
ORDER BY ordinal_position;

-- ============================================================================
-- 2. Ver 1 registro de exemplo para entender os campos
-- ============================================================================

SELECT * FROM api.prime_clientes LIMIT 1;

-- ============================================================================
-- 3. Verificar constraints e chaves
-- ============================================================================

SELECT
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'api'
AND tc.table_name = 'prime_clientes'
ORDER BY tc.constraint_type, kcu.ordinal_position;




