# 🚀 Guia Completo - Migração de Fórmulas com Ativos

## 📋 O Que Este Guia Faz

Esta migração adiciona **informações completas dos ativos** (produtos) de cada fórmula ao Supabase:

### ✅ Opção 1: Texto Completo do Rótulo
- Atualiza o campo `descricao` das fórmulas
- **ANTES**: "CONTÉM 30 CAPS" (só quantidade)
- **DEPOIS**: "SILICIUMAX PO 200mg - L CISTEINA 100mg - BIOTINA 10mg..." (lista completa)

### ✅ Opção 2: Tabela de Itens Individuais
- Cria nova tabela `prime_formulas_itens`
- Cada ativo/produto em uma linha separada
- Permite consultas detalhadas por ativo

---

## 📊 Estrutura de Dados

### Tabela: `prime_formulas` (existente - ATUALIZADA)
```
┌─────────────┬────────────────────────────────────────────────┐
│ Campo       │ Novo Conteúdo                                  │
├─────────────┼────────────────────────────────────────────────┤
│ descricao   │ "5HTP 150mg - TRIPTOFANO 150mg - MELATONINA..." │
│             │ (TEXTO COMPLETO com todos os ativos)           │
└─────────────┴────────────────────────────────────────────────┘
```

### Tabela: `prime_formulas_itens` (NOVA)
```sql
┌─────────────────┬──────────────────────────┬────────────┬─────────┐
│ nome_produto    │ quantidade               │ unidade    │ valor   │
├─────────────────┼──────────────────────────┼────────────┼─────────┤
│ 5HTP            │ 150                      │ mg         │ 25.00   │
│ TRIPTOFANO      │ 150                      │ mg         │ 30.00   │
│ TIROSINA        │ 150                      │ mg         │ 20.00   │
│ MELATONINA      │ 5                        │ mg         │ 15.00   │
└─────────────────┴──────────────────────────┴────────────┴─────────┘
```

---

## 🚀 Execução - Modo Automático (RECOMENDADO)

### Passo 1: Criar a Tabela no Supabase

**Opção A: Via SQL Editor (Recomendado)**

1. Acesse: https://supabase.com/dashboard
2. Selecione seu projeto
3. Vá em **SQL Editor** (menu lateral)
4. Clique em **New Query**
5. Cole o conteúdo do arquivo: `sql_criar_tabela_formulas_itens.sql`
6. Clique em **RUN** (ou pressione Ctrl+Enter)
7. Aguarde a mensagem: ✅ Success

**Opção B: Via Script Python**
```bash
# O script master tentará criar automaticamente
py executar_migracao_completa_formulas.py
```

### Passo 2: Executar Migração Completa

```bash
cd "C:\Banco de Dados Prime"
py executar_migracao_completa_formulas.py
```

O script executará **automaticamente**:
1. ✅ Verificar se tabela existe
2. ✅ Atualizar descrições das fórmulas
3. ✅ Exportar itens das fórmulas

---

## 🔧 Execução - Modo Manual (Passo a Passo)

### Etapa 1: Criar Tabela

```bash
# Execute o SQL manualmente no Supabase SQL Editor
# Arquivo: sql_criar_tabela_formulas_itens.sql
```

### Etapa 2: Atualizar Descrições

```bash
py atualizar_formulas_textorotulo.py
```

**O que faz:**
- Busca todas as fórmulas do Firebird
- Atualiza campo `descricao` de DESCRICAOROTULO → TEXTOROTULO
- Processa em lotes de 500

### Etapa 3: Exportar Itens

```bash
py exportar_formulas_itens.py
```

**O que faz:**
- Busca todos os itens da ATENDIMENTO_A3 (Firebird)
- Insere na tabela prime_formulas_itens (Supabase)
- Processa em lotes de 1000

---

## 📊 Verificação dos Dados

### No Supabase

```sql
-- Verificar total de fórmulas
SELECT COUNT(*) FROM api.prime_formulas;

-- Verificar total de itens
SELECT COUNT(*) FROM api.prime_formulas_itens;

-- Ver exemplo de fórmula completa
SELECT
    f.numero_formula,
    f.descricao as formula_completa,
    fi.nome_produto,
    fi.quantidade,
    fi.unidade
FROM api.prime_formulas f
LEFT JOIN api.prime_formulas_itens fi ON f.id = fi.formula_id
WHERE f.id = 1
ORDER BY fi.numero_linha;
```

### Resultado Esperado

```
┌─────────────────┬──────────────────────────────────────────────┐
│ numero_formula  │ 1                                            │
│ descricao       │ 5HTP 150mg - TRIPTOFANO 150mg - MELATONINA...│
├─────────────────┼──────────────────────────────────────────────┤
│ Itens:                                                         │
│   - 5HTP: 150mg                                                │
│   - TRIPTOFANO: 150mg                                          │
│   - MELATONINA: 5mg                                            │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Consultas Úteis

### 1. Listar todos os ativos de uma fórmula

```sql
SELECT
    fi.nome_produto,
    fi.quantidade || fi.unidade as dosagem,
    fi.valor_venda
FROM api.prime_formulas_itens fi
WHERE fi.formula_id = 123
ORDER BY fi.numero_linha;
```

### 2. Buscar fórmulas que contêm um ativo específico

```sql
SELECT DISTINCT
    f.id,
    f.numero_formula,
    f.descricao
FROM api.prime_formulas f
INNER JOIN api.prime_formulas_itens fi ON f.id = fi.formula_id
WHERE fi.nome_produto ILIKE '%BIOTINA%';
```

### 3. Valor total por ativo

```sql
SELECT
    fi.nome_produto,
    COUNT(*) as total_formulas,
    SUM(fi.valor_venda) as valor_total
FROM api.prime_formulas_itens fi
GROUP BY fi.nome_produto
ORDER BY valor_total DESC
LIMIT 20;
```

### 4. View consolidada (já criada)

```sql
-- Já está criada como api.v_formulas_completas
SELECT * FROM api.v_formulas_completas
WHERE pedido_id = 456;
```

---

## 📋 Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `sql_criar_tabela_formulas_itens.sql` | SQL para criar tabela |
| `atualizar_formulas_textorotulo.py` | Atualiza descrição das fórmulas |
| `exportar_formulas_itens.py` | Exporta itens individuais |
| `executar_migracao_completa_formulas.py` | **Script Master** (executa tudo) |
| `GUIA_MIGRACAO_FORMULAS_COMPLETAS.md` | Este guia |

---

## ⚠️ Importante

### Tempo Estimado
- Criar tabela: 1 minuto
- Atualizar descrições: ~5-10 minutos (depende do total de fórmulas)
- Exportar itens: ~10-20 minutos (depende do total de itens)

### Requisitos
- Python 3.7+
- Biblioteca `requests` instalada
- Conexão com Firebird funcionando
- Acesso ao Supabase (service_role key)

### Backup
**Antes de executar:**
```sql
-- Backup da tabela de fórmulas (no Supabase SQL Editor)
CREATE TABLE api.prime_formulas_backup AS
SELECT * FROM api.prime_formulas;
```

---

## 🆘 Solução de Problemas

### Erro: "Tabela não existe"
```bash
# Execute o SQL manualmente no Supabase
# Arquivo: sql_criar_tabela_formulas_itens.sql
```

### Erro: "Timeout"
```python
# Aumente o timeout nos scripts
timeout=120  # Aumentar de 60 para 120
```

### Erro: "Fórmula não encontrada"
```bash
# Certifique-se que prime_formulas foi populada primeiro
# Verifique:
SELECT COUNT(*) FROM api.prime_formulas;
```

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs dos scripts
2. Confira se a tabela prime_formulas já existe
3. Teste a conexão com Firebird
4. Verifique as credenciais do Supabase

---

## ✅ Checklist de Execução

- [ ] Criar tabela `prime_formulas_itens` no Supabase
- [ ] Executar script `atualizar_formulas_textorotulo.py`
- [ ] Executar script `exportar_formulas_itens.py`
- [ ] Verificar dados no Supabase
- [ ] Testar consultas de exemplo

---

**Data de Criação:** 2025-10-24
**Última Atualização:** 2025-10-24
