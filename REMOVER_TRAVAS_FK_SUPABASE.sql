-- ============================================================================
-- REMOVER TRAVAS DE FOREIGN KEYS - PERMITIR INSERÇÃO INDEPENDENTE
-- ============================================================================
-- Este script torna as Foreign Keys opcionais (permitindo NULL)
-- para que os registros possam ser inseridos independentemente
-- e depois atualizados quando os registros pai forem sincronizados.
-- ============================================================================

-- 1. REMOVER FK de prime_formulas.pedido_id → prime_pedidos.id
--    Permite inserir fórmulas mesmo sem pedido existir
ALTER TABLE api.prime_formulas 
DROP CONSTRAINT IF EXISTS prime_formulas_pedido_id_fkey;

ALTER TABLE api.prime_formulas 
ALTER COLUMN pedido_id DROP NOT NULL;

-- 2. REMOVER FK de prime_formulas_itens.formula_id → prime_formulas.id
--    Permite inserir itens mesmo sem fórmula existir
ALTER TABLE api.prime_formulas_itens 
DROP CONSTRAINT IF EXISTS prime_formulas_itens_formula_id_fkey;

ALTER TABLE api.prime_formulas_itens 
ALTER COLUMN formula_id DROP NOT NULL;

-- 3. REMOVER FK de prime_formulas_itens.pedido_id → prime_pedidos.id
--    Permite inserir itens mesmo sem pedido existir
ALTER TABLE api.prime_formulas_itens 
DROP CONSTRAINT IF EXISTS prime_formulas_itens_pedido_id_fkey;

ALTER TABLE api.prime_formulas_itens 
ALTER COLUMN pedido_id DROP NOT NULL;

-- 4. REMOVER FK de prime_pedidos.cliente_id → prime_clientes.id
--    Permite inserir pedidos mesmo sem cliente existir
ALTER TABLE api.prime_pedidos 
DROP CONSTRAINT IF EXISTS prime_pedidos_cliente_id_fkey;

ALTER TABLE api.prime_pedidos 
ALTER COLUMN cliente_id DROP NOT NULL;

-- 5. REMOVER FK de prime_rastreabilidade.pedido_id → prime_pedidos.id
--    Permite inserir rastreabilidade mesmo sem pedido existir
ALTER TABLE api.prime_rastreabilidade 
DROP CONSTRAINT IF EXISTS prime_rastreabilidade_pedido_id_fkey;

ALTER TABLE api.prime_rastreabilidade 
ALTER COLUMN pedido_id DROP NOT NULL;

-- 6. REMOVER FK de prime_rastreabilidade.tipo_processo_id → prime_tipos_processo.id
--    Permite inserir rastreabilidade mesmo sem tipo existir
ALTER TABLE api.prime_rastreabilidade 
DROP CONSTRAINT IF EXISTS prime_rastreabilidade_tipo_processo_id_fkey;

ALTER TABLE api.prime_rastreabilidade 
ALTER COLUMN tipo_processo_id DROP NOT NULL;

-- ============================================================================
-- RESUMO DAS ALTERAÇÕES:
-- ============================================================================
-- ✅ prime_formulas.pedido_id → NULL permitido
-- ✅ prime_formulas_itens.formula_id → NULL permitido
-- ✅ prime_formulas_itens.pedido_id → NULL permitido
-- ✅ prime_pedidos.cliente_id → NULL permitido
-- ✅ prime_rastreabilidade.pedido_id → NULL permitido
-- ✅ prime_rastreabilidade.tipo_processo_id → NULL permitido
-- ============================================================================
-- APÓS REMOVER AS TRAVAS:
-- - Todos os registros podem ser inseridos independentemente
-- - Os campos FK podem ficar NULL temporariamente
-- - Quando os registros pai forem sincronizados, você pode fazer UPDATE
--   para preencher os campos FK com os IDs corretos
-- ============================================================================

