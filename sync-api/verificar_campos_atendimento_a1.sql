-- ============================================================================
-- VERIFICAR CAMPOS DA TABELA ATENDIMENTO_A1 NO FIREBIRD
-- Execute no cliente Firebird ou via script Python
-- ============================================================================

-- Listar todos os campos da tabela ATENDIMENTO_A1
SELECT 
    RF.RDB$FIELD_NAME,
    RF.RDB$FIELD_TYPE,
    RF.RDB$FIELD_LENGTH,
    RF.RDB$FIELD_SCALE,
    RF.RDB$NULL_FLAG
FROM RDB$RELATION_FIELDS RF
WHERE RF.RDB$RELATION_NAME = 'ATENDIMENTO_A1'
ORDER BY RF.RDB$FIELD_POSITION;

-- ============================================================================
-- Ver registros de exemplo com TODOS os campos
-- ============================================================================

SELECT * FROM ATENDIMENTO_A1 
WHERE ROWS 10;

-- ============================================================================
-- Campos relacionados a DATA
-- ============================================================================

SELECT 
    RF.RDB$FIELD_NAME,
    RF.RDB$FIELD_TYPE,
    CASE RF.RDB$FIELD_TYPE
        WHEN 12 THEN 'DATE'
        WHEN 13 THEN 'TIME'
        WHEN 35 THEN 'TIMESTAMP'
        ELSE 'OUTRO'
    END as tipo_data
FROM RDB$RELATION_FIELDS RF
WHERE RF.RDB$RELATION_NAME = 'ATENDIMENTO_A1'
AND RF.RDB$FIELD_TYPE IN (12, 13, 35)
ORDER BY RF.RDB$FIELD_NAME;

-- ============================================================================
-- Campos que podem ser de DATA DE CRIACAO
-- ============================================================================

SELECT 
    RF.RDB$FIELD_NAME
FROM RDB$RELATION_FIELDS RF
WHERE RF.RDB$RELATION_NAME = 'ATENDIMENTO_A1'
AND (
    RF.RDB$FIELD_NAME LIKE '%DATA%' OR
    RF.RDB$FIELD_NAME LIKE '%DATE%' OR
    RF.RDB$FIELD_NAME LIKE '%CRIACAO%' OR
    RF.RDB$FIELD_NAME LIKE '%CREATED%' OR
    RF.RDB$FIELD_NAME LIKE '%CADASTRO%'
)
ORDER BY RF.RDB$FIELD_NAME;




