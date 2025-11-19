-- ============================================================================
-- ATUALIZAR FOREIGN KEYS DEPOIS DA SINCRONIZAÇÃO
-- ============================================================================
-- Este script atualiza os campos FK (que estavam NULL) depois que
-- todos os registros foram sincronizados, preenchendo os relacionamentos.
-- Execute este script DEPOIS de garantir que todos os registros estão 100%
-- ============================================================================

-- 1. Atualizar prime_formulas.pedido_id (preencher FK quando pedido existir)
UPDATE api.prime_formulas f
SET pedido_id = p.id
FROM api.prime_pedidos p
WHERE f.pedido_id IS NULL
  AND f.codigo_orcamento_original = p.codigo_orcamento_original;

-- 2. Atualizar prime_formulas_itens.formula_id (preencher FK quando fórmula existir)
UPDATE api.prime_formulas_itens fi
SET formula_id = f.id
FROM api.prime_formulas f
WHERE fi.formula_id IS NULL
  AND fi.codigo_atendimento_original = f.codigo_orcamento_original
  AND fi.numero_formula = f.numero_formula;

-- 3. Atualizar prime_formulas_itens.pedido_id (preencher FK quando pedido existir)
UPDATE api.prime_formulas_itens fi
SET pedido_id = p.id
FROM api.prime_pedidos p
WHERE fi.pedido_id IS NULL
  AND fi.codigo_atendimento_original = p.codigo_orcamento_original;

-- 4. Atualizar prime_pedidos.cliente_id (preencher FK quando cliente existir)
UPDATE api.prime_pedidos p
SET cliente_id = c.id
FROM api.prime_clientes c
WHERE p.cliente_id IS NULL
  AND p.codigo_cliente_original = c.codigo_cliente_original;

-- 5. Atualizar prime_rastreabilidade.pedido_id (preencher FK quando pedido existir)
UPDATE api.prime_rastreabilidade r
SET pedido_id = p.id
FROM api.prime_pedidos p
WHERE r.pedido_id IS NULL
  AND r.codigo_orcamento_original = p.codigo_orcamento_original;

-- 6. Atualizar prime_rastreabilidade.tipo_processo_id (preencher FK quando tipo existir)
UPDATE api.prime_rastreabilidade r
SET tipo_processo_id = t.id
FROM api.prime_tipos_processo t
WHERE r.tipo_processo_id IS NULL
  AND r.codigo_tipo_original = t.codigo_tipo_original;

-- ============================================================================
-- VERIFICAR REGISTROS AINDA SEM FK (devem ser zero após sincronização 100%)
-- ============================================================================
SELECT 
    'prime_formulas' as tabela,
    COUNT(*) as registros_sem_pedido_id
FROM api.prime_formulas
WHERE pedido_id IS NULL

UNION ALL

SELECT 
    'prime_formulas_itens' as tabela,
    COUNT(*) as registros_sem_formula_id
FROM api.prime_formulas_itens
WHERE formula_id IS NULL OR pedido_id IS NULL

UNION ALL

SELECT 
    'prime_pedidos' as tabela,
    COUNT(*) as registros_sem_cliente_id
FROM api.prime_pedidos
WHERE cliente_id IS NULL

UNION ALL

SELECT 
    'prime_rastreabilidade' as tabela,
    COUNT(*) as registros_sem_fk
FROM api.prime_rastreabilidade
WHERE pedido_id IS NULL OR tipo_processo_id IS NULL;

-- ============================================================================
-- OPCIONAL: Recriar as FK após preencher todos os campos
-- (descomente apenas se quiser restabelecer a integridade referencial)
-- ============================================================================

-- ALTER TABLE api.prime_formulas 
-- ADD CONSTRAINT prime_formulas_pedido_id_fkey 
-- FOREIGN KEY (pedido_id) REFERENCES api.prime_pedidos(id) ON DELETE CASCADE;

-- ALTER TABLE api.prime_formulas_itens 
-- ADD CONSTRAINT prime_formulas_itens_formula_id_fkey 
-- FOREIGN KEY (formula_id) REFERENCES api.prime_formulas(id) ON DELETE CASCADE;

-- ALTER TABLE api.prime_formulas_itens 
-- ADD CONSTRAINT prime_formulas_itens_pedido_id_fkey 
-- FOREIGN KEY (pedido_id) REFERENCES api.prime_pedidos(id) ON DELETE CASCADE;

-- ALTER TABLE api.prime_pedidos 
-- ADD CONSTRAINT prime_pedidos_cliente_id_fkey 
-- FOREIGN KEY (cliente_id) REFERENCES api.prime_clientes(id) ON DELETE CASCADE;

-- ALTER TABLE api.prime_rastreabilidade 
-- ADD CONSTRAINT prime_rastreabilidade_pedido_id_fkey 
-- FOREIGN KEY (pedido_id) REFERENCES api.prime_pedidos(id) ON DELETE CASCADE;

-- ALTER TABLE api.prime_rastreabilidade 
-- ADD CONSTRAINT prime_rastreabilidade_tipo_processo_id_fkey 
-- FOREIGN KEY (tipo_processo_id) REFERENCES api.prime_tipos_processo(id);

