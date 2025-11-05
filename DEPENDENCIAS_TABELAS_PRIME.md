# 📊 DEPENDÊNCIAS E ORDEM DE SINCRONIZAÇÃO - Tabelas Prime

## 🔗 RELACIONAMENTOS (Foreign Keys)

### 1. **prime_clientes** (Tabela Base - Nível 0)
- **Chave primária:** `id` (bigint, auto-incremento)
- **Chave única:** `codigo_cliente_original` (integer, NOT NULL)
- **Não depende de nenhuma tabela prime**
- ✅ **Pode ser sincronizada primeiro**

### 2. **prime_pedidos** (Nível 1 - Depende de clientes)
- **Chave primária:** `id` (bigint, auto-incremento)
- **Chave única:** `codigo_orcamento_original` (integer, NOT NULL)
- **Foreign Key:** `cliente_id` → `prime_clientes.id` (NOT NULL, ON DELETE CASCADE)
- **Depende de:** `prime_clientes` ✅
- ⚠️ **DEVE ser sincronizada DEPOIS de clientes**

### 3. **prime_tipos_processo** (Tabela Base - Nível 0)
- **Chave primária:** `id` (bigint, auto-incremento)
- **Chave única:** `codigo_tipo_original` (integer, NOT NULL)
- **Não depende de nenhuma tabela prime**
- ✅ **Pode ser sincronizada em paralelo com clientes**

### 4. **prime_formulas** (Nível 2 - Depende de pedidos)
- **Chave primária:** `id` (bigint, auto-incremento)
- **Foreign Key:** `pedido_id` → `prime_pedidos.id` (NOT NULL)
- **Depende de:** `prime_pedidos` ✅
- ⚠️ **DEVE ser sincronizada DEPOIS de pedidos**

### 5. **prime_formulas_itens** (Nível 3 - Depende de fórmulas e pedidos)
- **Chave primária:** `id` (bigint, auto-incremento)
- **Foreign Keys:**
  - `formula_id` → `prime_formulas.id` (NOT NULL)
  - `pedido_id` → `prime_pedidos.id` (NOT NULL)
- **Depende de:** `prime_formulas` ✅ e `prime_pedidos` ✅
- ⚠️ **DEVE ser sincronizada DEPOIS de fórmulas**

### 6. **prime_rastreabilidade** (Nível 2 - Depende de pedidos e tipos_processo)
- **Chave primária:** `id` (bigint, auto-incremento)
- **Chave única:** `codigo_processo_original` (integer, NOT NULL)
- **Foreign Keys:**
  - `pedido_id` → `prime_pedidos.id` (NOT NULL)
  - `tipo_processo_id` → `prime_tipos_processo.id` (NOT NULL)
- **Depende de:** `prime_pedidos` ✅ e `prime_tipos_processo` ✅
- ⚠️ **DEVE ser sincronizada DEPOIS de pedidos e tipos_processo**

---

## 📋 ORDEM CORRETA DE SINCRONIZAÇÃO

### **Fase 1: Tabelas Base (sem dependências)**
```
1. prime_clientes         ← Sem dependências
2. prime_tipos_processo   ← Sem dependências (pode ser em paralelo)
```

### **Fase 2: Tabelas que dependem de Fase 1**
```
3. prime_pedidos          ← Depende de: prime_clientes
```

### **Fase 3: Tabelas que dependem de Fase 2**
```
4. prime_formulas         ← Depende de: prime_pedidos
5. prime_rastreabilidade   ← Depende de: prime_pedidos + prime_tipos_processo
```

### **Fase 4: Tabelas que dependem de Fase 3**
```
6. prime_formulas_itens   ← Depende de: prime_formulas + prime_pedidos
```

---

## ⚠️ PROBLEMA IDENTIFICADO

### **Erro atual:**
```
⚠️ Pedido 251100467 não encontrado no Supabase, pulando...
```

### **Causa:**
1. A API tenta sincronizar **rastreabilidade** (Fase 3)
2. Mas alguns **pedidos** (Fase 2) ainda não foram inseridos
3. Por isso a rastreabilidade não encontra o pedido e pula

### **Solução:**
1. **Garantir que TODOS os pedidos sejam inseridos ANTES de fórmulas e rastreabilidade**
2. **Adicionar retry/verificação:** Se pedido não existe, tentar inserir antes de continuar
3. **Melhorar logging:** Mostrar quantos pedidos faltam e por quê

---

## 🔍 COLUNAS OBRIGATÓRIAS (NOT NULL)

### **prime_clientes:**
- `id` (auto)
- `codigo_cliente_original` (integer)
- `nome` (varchar)

### **prime_pedidos:**
- `id` (auto)
- `codigo_orcamento_original` (integer)
- `cliente_id` (bigint) ← **DEVE existir em prime_clientes**
- `codigo_cliente_original` (integer)
- `valor_total` (numeric, default 0)
- `status_aprovacao` (varchar)
- `status_entrega` (varchar)
- `status_geral` (varchar)

### **prime_formulas:**
- `id` (auto)
- `pedido_id` (bigint) ← **DEVE existir em prime_pedidos**
- `codigo_orcamento_original` (integer)
- `numero_formula` (integer)

### **prime_formulas_itens:**
- `id` (auto)
- `formula_id` (bigint) ← **DEVE existir em prime_formulas**
- `pedido_id` (bigint) ← **DEVE existir em prime_pedidos**
- `codigo_atendimento_original` (integer)
- `numero_formula` (integer)
- `nome_produto` (text)

### **prime_rastreabilidade:**
- `id` (auto)
- `codigo_processo_original` (integer)
- `pedido_id` (bigint) ← **DEVE existir em prime_pedidos**
- `codigo_orcamento_original` (integer)
- `tipo_processo_id` (bigint) ← **DEVE existir em prime_tipos_processo**
- `codigo_tipo_original` (integer)
- `tipo_movimento` (integer)
- `sequencia` (integer)

### **prime_tipos_processo:**
- `id` (auto)
- `codigo_tipo_original` (integer)
- `nome_processo` (varchar)
- `sequencia` (integer)

---

## ✅ REGRAS DE NEGÓCIO

1. **Pedidos SEM clientes:** Não podem ser inseridos (FK constraint)
2. **Fórmulas SEM pedidos:** Não podem ser inseridas (FK constraint)
3. **Itens SEM fórmulas:** Não podem ser inseridos (FK constraint)
4. **Rastreabilidade SEM pedidos:** Não pode ser inserida (FK constraint)
5. **Rastreabilidade SEM tipos_processo:** Não pode ser inserida (FK constraint)

---

**Última atualização:** 05/11/2025 22:30
**Status:** Documentação das dependências completa

