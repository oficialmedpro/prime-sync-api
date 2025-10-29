# ⚠️ PROBLEMA: Campo data_criacao não existe no Firebird

**Data:** 27/10/2025  
**Tabela:** `ATENDIMENTO_A1` (pedidos)

---

## 🔍 Investigação Realizada

### ✅ Campos que EXISTEM:
- `CODIGO` - Código do pedido (PK, sequencial)
- `CODIGO_CLIENTE` - Cliente do pedido
- `AVIADA_DT` - Data de aprovação
- `ENTREGUE_DT` - Data de entrega
- `VALORVENDA` - Valor total
- `OBSERVACAO` - Observações

### ❌ Campos que NÃO EXISTEM:
- `DATA` ❌
- `DATA_PEDIDO` ❌
- `DATA_CRIACAO` ❌
- `DATA_CADASTRO` ❌
- `DT_CRIACAO` ❌
- `DATACAD` ❌
- `DATAATEND` ❌
- `DATA_ATENDIMENTO` ❌

**Conclusão:** A tabela `ATENDIMENTO_A1` **NÃO armazena** a data de criação do pedido!

---

## 💡 Soluções Possíveis

### **Opção 1: Usar `created_at` do Supabase** ✅ RECOMENDADO

O campo `created_at` do Supabase já registra quando o pedido foi inserido. Para pedidos novos, isso será suficiente.

**Para pedidos antigos (já sincronizados):**
- `created_at` = data da primeira sincronização
- Não é a data real de criação, mas é a melhor aproximação

**Vantagem:**
- Não precisa alterar código
- Funciona automaticamente

**Desvantagem:**
- Dados históricos terão data da migração, não data real

---

### **Opção 2: Usar `AVIADA_DT` como aproximação**

Se todo pedido passa por aprovação, `AVIADA_DT` pode ser usada como data aproximada.

**Código:**
```python
data_criacao = aviada_dt or entregue_dt or datetime.now()
```

**Vantagem:**
- Usa dados do Firebird
- Melhor que `created_at` para dados históricos

**Desvantagem:**
- Nem todo pedido é aprovado imediatamente
- Data pode ser dias/semanas após criação real

---

### **Opção 3: Deixar NULL e usar filtros inteligentes** ⚠️

Aceitar que `data_criacao` não existe e usar:
- `data_aprovacao` (AVIADA_DT)
- `data_entrega` (ENTREGUE_DT)
- `created_at` (Supabase)

**Nos relatórios/queries:**
```sql
-- Usar a primeira data disponível
SELECT 
    *,
    COALESCE(data_criacao, data_aprovacao, data_entrega, created_at) as data_referencia
FROM prime_pedidos
```

---

## 🎯 Recomendação FINAL

### **Para Pedidos NOVOS (daqui pra frente):**

**Usar `created_at` do Supabase** automaticamente.

- Remove o campo `data_criacao` do código Python
- O Supabase preenche `created_at` automaticamente
- É a data real de inserção no Supabase

### **Para Pedidos ANTIGOS (já sincronizados):**

**Opção A: Manter NULL**
- Aceitar que não tem data de criação
- Usar `created_at` como referência

**Opção B: Preencher com AVIADA_DT**
- Script retroativo para preencher `data_criacao = AVIADA_DT`
- Menos preciso, mas melhor que NULL

---

## 🔧 AÇÃO IMEDIATA

### 1️⃣ Reverter alteração no app.py

**REMOVER esta linha:**
```python
A.DATA,  # <- Campo não existe!
```

**REMOVER do mapeamento:**
```python
data_criacao = ...  # <- Não vai funcionar
```

### 2️⃣ Atualizar schema do Supabase (OPCIONAL)

Se `data_criacao` deve ser preenchida:

**Opção A: DEFAULT = created_at**
```sql
ALTER TABLE api.prime_pedidos
ALTER COLUMN data_criacao 
SET DEFAULT NOW();
```

**Opção B: Trigger**
```sql
CREATE OR REPLACE FUNCTION set_data_criacao()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.data_criacao IS NULL THEN
        NEW.data_criacao := NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_data_criacao
BEFORE INSERT ON api.prime_pedidos
FOR EACH ROW
EXECUTE FUNCTION set_data_criacao();
```

### 3️⃣ Script retroativo (se escolher Opção B)

```python
# Preencher data_criacao com AVIADA_DT para pedidos antigos
UPDATE api.prime_pedidos
SET data_criacao = data_aprovacao
WHERE data_criacao IS NULL 
AND data_aprovacao IS NOT NULL;

# Para pedidos sem aprovação, usar created_at
UPDATE api.prime_pedidos
SET data_criacao = created_at
WHERE data_criacao IS NULL;
```

---

## 📊 Impacto nos Relatórios

Se relatórios usam `data_criacao`, ajustar para:

```sql
-- Usar COALESCE para fallback
SELECT 
    COALESCE(data_criacao, data_aprovacao, created_at) as data_pedido,
    COUNT(*) as total_pedidos
FROM api.prime_pedidos
GROUP BY data_pedido
ORDER BY data_pedido;
```

---

## ✅ Decisão Tomada

**Por favor, escolha uma das opções acima e me informe para que eu ajuste o código.**

Opções:
1. **Remover `data_criacao`** do código e usar apenas `created_at`
2. **Usar `AVIADA_DT`** como aproximação para `data_criacao`
3. **Manter NULL** e ajustar queries/relatórios com COALESCE

**Qual você prefere?**




