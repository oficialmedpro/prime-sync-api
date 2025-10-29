-- ============================================================================
-- SCRIPT: Verificar status de todas as tabelas sincronizadas
-- DATA: 27/10/2025
-- ============================================================================

-- 📊 PRIME_CLIENTES
SELECT 
    'prime_clientes' as tabela,
    COUNT(*) as total_registros,
    MIN(codigo_cliente_original) as primeiro_codigo,
    MAX(codigo_cliente_original) as ultimo_codigo,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as ultimos_7dias
FROM api.prime_clientes

UNION ALL

-- 📊 PRIME_PEDIDOS
SELECT 
    'prime_pedidos' as tabela,
    COUNT(*) as total_registros,
    MIN(codigo_orcamento_original) as primeiro_codigo,
    MAX(codigo_orcamento_original) as ultimo_codigo,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as ultimos_7dias
FROM api.prime_pedidos

UNION ALL

-- 📊 PRIME_FORMULAS
SELECT 
    'prime_formulas' as tabela,
    COUNT(*) as total_registros,
    MIN(codigo_orcamento_original) as primeiro_codigo,
    MAX(codigo_orcamento_original) as ultimo_codigo,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as ultimos_7dias
FROM api.prime_formulas

UNION ALL

-- 📊 PRIME_FORMULAS_ITENS
SELECT 
    'prime_formulas_itens' as tabela,
    COUNT(*) as total_registros,
    MIN(codigo_atendimento_original) as primeiro_codigo,
    MAX(codigo_atendimento_original) as ultimo_codigo,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as ultimos_7dias
FROM api.prime_formulas_itens

UNION ALL

-- 📊 PRIME_RASTREABILIDADE
SELECT 
    'prime_rastreabilidade' as tabela,
    COUNT(*) as total_registros,
    MIN(codigo_processo_original) as primeiro_codigo,
    MAX(codigo_processo_original) as ultimo_codigo,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as ultimos_7dias
FROM api.prime_rastreabilidade

UNION ALL

-- 📊 PRIME_TIPOS_PROCESSO
SELECT 
    'prime_tipos_processo' as tabela,
    COUNT(*) as total_registros,
    MIN(codigo_tipo_original) as primeiro_codigo,
    MAX(codigo_tipo_original) as ultimo_codigo,
    MIN(created_at) as primeira_insercao,
    MAX(created_at) as ultima_insercao,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ultimas_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as ultimos_7dias
FROM api.prime_tipos_processo

ORDER BY tabela;

-- ============================================================================
-- ANÁLISE DETALHADA: Registros por hora nas últimas 24h
-- ============================================================================

SELECT 
    'prime_clientes' as tabela,
    DATE_TRUNC('hour', created_at) as hora,
    COUNT(*) as registros
FROM api.prime_clientes
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)

UNION ALL

SELECT 
    'prime_pedidos' as tabela,
    DATE_TRUNC('hour', created_at) as hora,
    COUNT(*) as registros
FROM api.prime_pedidos
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)

UNION ALL

SELECT 
    'prime_rastreabilidade' as tabela,
    DATE_TRUNC('hour', created_at) as hora,
    COUNT(*) as registros
FROM api.prime_rastreabilidade
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)

ORDER BY tabela, hora DESC;

-- ============================================================================
-- VERIFICAR registros com códigos suspeitos
-- ============================================================================

-- Clientes com códigos absurdos
SELECT 'CLIENTES SUSPEITOS' as tipo, * 
FROM api.prime_clientes 
WHERE codigo_cliente_original > 500000 
ORDER BY codigo_cliente_original DESC;

-- Pedidos com códigos absurdos  
SELECT 'PEDIDOS SUSPEITOS' as tipo, * 
FROM api.prime_pedidos 
WHERE codigo_orcamento_original > 300000000 
ORDER BY codigo_orcamento_original DESC;




