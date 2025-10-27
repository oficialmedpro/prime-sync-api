# Campos da Tabela prime_clientes

## ⚠️ EXECUTE NO SUPABASE SQL EDITOR:

```sql
-- Ver todos os campos da tabela
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'api'
AND table_name = 'prime_clientes'
ORDER BY ordinal_position;
```

## 📋 Campos que o código está inserindo (ATUAL):

```python
cliente = {
    'codigo_cliente_original',  # INTEGER - PK
    'nome',                      # VARCHAR(255)
    'cpf_cnpj',                 # VARCHAR(20)
    'email',                     # VARCHAR(255)
    'telefone',                  # VARCHAR
    'endereco_logradouro',       # VARCHAR(255)
    'endereco_numero',           # VARCHAR
    'endereco_cidade',           # VARCHAR(100)
    'endereco_estado',           # VARCHAR(2)
    'endereco_cep',              # VARCHAR(10)
    'data_nascimento',           # DATE
    'sexo',                      # VARCHAR(1)
    'ativo',                     # BOOLEAN
    'updated_at'                 # TIMESTAMP
}
```

## ❌ Campo REMOVIDO (não existe no Supabase):

- `data_cadastro` ← **REMOVIDO**

## 📝 INSTRUÇÕES:

1. Execute a query SQL acima no Supabase
2. Compare os campos retornados com a lista acima
3. Me informe se há diferenças
4. Ajustaremos o código conforme necessário

## 🔧 Campos Opcionais Comuns:

Se a tabela tiver estes campos, podemos adicionar:

- `created_at` (TIMESTAMP)
- `id` (UUID) - geralmente auto-gerado
- `cliente_id` (UUID) - FK para outra tabela
- `observacoes` (TEXT)
- `data_cadastro` (DATE) - se existir

## ✅ Após verificar:

Me envie a lista de campos e vou ajustar o `app.py` para usar APENAS os campos que existem.

