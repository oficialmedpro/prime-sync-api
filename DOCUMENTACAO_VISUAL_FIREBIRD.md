# 📊 DOCUMENTAÇÃO FIREBIRD - VISUAL

---

## ⚠️ ESTRUTURA FIREBIRD - NUNCA ESQUECER ⚠️

---

### 1. DADOS DO CLIENTE

#### Tabela: `CLIENTE` (Dados básicos)
```
┌─ CODIGO
├─ NOMECLIENTE
├─ CPF_CNPJ
├─ DIANASCIMENTO  ─┐
├─ MESNASCIMENTO  ─┼─ (combinar para DATA_NASCIMENTO)
├─ ANONASCIMENTO  ─┘
├─ SEXO (0=NI, 1=M, 2=F)
├─ EMAIL1
└─ ATIVO
```

#### Tabela: `CADASTRO_TELEFONE` ⚠️ **(Telefones separados!)**
```
WHERE TIPO_CADASTRO = 1 (cliente)
  AND CODIGO_CADASTRO = [CODIGO_CLIENTE]

Campos:
├─ TELEFONEPREFIXO  ─┐
└─ TELEFONE         ─┴─ (concatenar)
```

#### Tabela: `CADASTRO_ENDERECO` ⚠️ **(Endereços separados!)**
```
WHERE TIPO_CADASTRO = 1 (cliente)
  AND CODIGO_CADASTRO = [CODIGO_CLIENTE]

Campos:
├─ DESCRICAO (ex: "Casa")
├─ ENDERECO
├─ NUMERO
└─ CEP
```

#### Tabela: `ATENDIMENTO_A1` **(Totalizadores calculados)**
```
Calcular por cliente:
├─ COUNT(*) → total_orcamentos
├─ COUNT(AVIADA_DT) → total_aprovados
├─ COUNT(ENTREGUE_DT) → total_entregues
├─ SUM(VALORVENDA) → valor_total
├─ MIN(CADASTRO_DT) → primeira_compra
└─ MAX(CADASTRO_DT) → ultima_compra
```

---

### 🔥 IMPORTANTE: SEMPRE buscar nas 4 tabelas!

```
⚠️ TIPO_CADASTRO:
   1 = CLIENTE
   2 = FORNECEDOR (NÃO PEGAR!)
```

---

### 2. PEDIDOS/ORÇAMENTOS

#### Tabela: `ATENDIMENTO_A1`
```
┌─ CODIGO (PK)
├─ CODIGO_CLIENTE (FK)
│
├─ CADASTRO_DT     → data_criacao
├─ AVIADA_DT       → data_aprovacao
├─ ENTREGUE_DT     → data_entrega
├─ CANCELADO_DT?   → data_cancelamento (verificar se existe!)
│
├─ VALORVENDA      → valor_total
└─ OBSERVACAO      → observacoes
```

**Status (calculados):**
```
IF ENTREGUE_DT → status_geral = 'ENTREGUE'
ELIF AVIADA_DT → status_geral = 'APROVADO'
ELSE           → status_geral = 'PENDENTE'
```

---

### 3. FÓRMULAS

#### Tabela: `ATENDIMENTO_A2`
```
┌─ CODIGO_ATEND_A1 (FK → pedido)
├─ NUMEROFORMULA
│
├─ TEXTOROTULO      → descricao ⚠️ NOME DO PRODUTO JÁ ESTÁ AQUI!
├─ POSOLOGIA        → posologia
└─ VALORFORMULA_VENDA → valor_formula
```

**⚠️ NÃO buscar nome do produto de `ESTOQUE` para fórmulas!**  
**✅ `TEXTOROTULO` já contém o nome completo!**

---

### 4. ITENS DAS FÓRMULAS

#### Tabela: `ATENDIMENTO_A3` + JOIN `ESTOQUE`
```
ATENDIMENTO_A3:
┌─ CODIGO_ATEND_A1 (FK → pedido)
├─ NUMEROFORMULA (FK → fórmula)
├─ CODIGO_ESTOQUE (FK → produto)
│
├─ QUANTIDADE
├─ VALOR_CUSTO
└─ VALOR_VENDA

ESTOQUE (JOIN):
└─ NOME → nome_produto ⚠️ BUSCAR AQUI!
```

**⚠️ Para ITENS, SIM precisa buscar nome da tabela `ESTOQUE`!**

---

## 📋 ORDEM DE SINCRONIZAÇÃO

```
1. CLIENTES
   │
   ↓ (gera cliente_id)
   │
2. PEDIDOS
   │
   ↓ (gera pedido_id)
   │
3. FÓRMULAS
   │
   ↓ (gera formula_id)
   │
4. ITENS
```

**❌ NUNCA sincronizar fora de ordem!**

---

## 🔄 FLUXO DE SINCRONIZAÇÃO

### CLIENTES:
```
FIREBIRD                                    SUPABASE
========================================================

CLIENTE (dados básicos)            ─┐
CADASTRO_TELEFONE (TIPO=1)         ─┤
CADASTRO_ENDERECO (TIPO=1)         ─┼──→  prime_clientes
ATENDIMENTO_A1 (totalizadores)     ─┘
```

### PEDIDOS:
```
FIREBIRD                                    SUPABASE
========================================================

ATENDIMENTO_A1                     ──→  prime_pedidos
                                          (+ cliente_id do Supabase)
```

### FÓRMULAS:
```
FIREBIRD                                    SUPABASE
========================================================

ATENDIMENTO_A2                     ──→  prime_formulas
(TEXTOROTULO = nome produto!)             (+ pedido_id do Supabase)
```

### ITENS:
```
FIREBIRD                                    SUPABASE
========================================================

ATENDIMENTO_A3      ─┐
ESTOQUE (JOIN)      ─┴──→  prime_formulas_itens
                            (+ formula_id do Supabase)
```

---

## ✅ CHECKLIST RÁPIDO

Antes de sincronizar, verifique:

### Clientes:
- [ ] Busquei de `CLIENTE`?
- [ ] Busquei de `CADASTRO_TELEFONE` (TIPO=1)?
- [ ] Busquei de `CADASTRO_ENDERECO` (TIPO=1)?
- [ ] Calculei totalizadores de `ATENDIMENTO_A1`?
- [ ] Concatenei `TELEFONEPREFIXO` + `TELEFONE`?
- [ ] Combinei `DIA` + `MES` + `ANO` de nascimento?

### Pedidos:
- [ ] Busquei `cliente_id` do Supabase primeiro?
- [ ] Usei `CADASTRO_DT` para data_criacao?
- [ ] Converti datas para `.isoformat()`?

### Fórmulas:
- [ ] Busquei `pedido_id` do Supabase primeiro?
- [ ] Usei `TEXTOROTULO` como nome do produto?
- [ ] NÃO tentei buscar de `ESTOQUE`?

### Itens:
- [ ] Busquei `formula_id` do Supabase primeiro?
- [ ] Fiz JOIN com `ESTOQUE` para nome do produto?
- [ ] Usei `LEFT JOIN` para não perder itens?

---

## 🆘 ERROS COMUNS

| Erro | Causa | Solução |
|------|-------|---------|
| Cliente sem telefone | Não buscou `CADASTRO_TELEFONE` | `WHERE TIPO_CADASTRO = 1` |
| Cliente sem endereço | Não buscou `CADASTRO_ENDERECO` | `WHERE TIPO_CADASTRO = 1` |
| Totalizadores zerados | Não calculou de `ATENDIMENTO_A1` | Query de agregação `GROUP BY` |
| Fórmula sem nome | Tentou buscar de `ESTOQUE` | Usar `TEXTOROTULO` direto |
| Item sem nome | Não fez JOIN com `ESTOQUE` | `LEFT JOIN ESTOQUE E ON...` |
| FK error (pedido) | Não buscou `cliente_id` | Buscar antes de inserir |
| JSON date error | Não converteu data | `.isoformat()` |

---

## 📖 LEIA ANTES DE QUALQUER ALTERAÇÃO:

1. **[DOCUMENTACAO_FIREBIRD_COMPLETA.md](./DOCUMENTACAO_FIREBIRD_COMPLETA.md)** ⚠️ OBRIGATÓRIO
2. **[ESTRUTURA_FIREBIRD_IMPORTANTE.md](./ESTRUTURA_FIREBIRD_IMPORTANTE.md)** ⚠️ OBRIGATÓRIO

---

**Se você esquecer:** Dados virão NULL ou incompletos!  
**Última atualização:** 28/10/2025


